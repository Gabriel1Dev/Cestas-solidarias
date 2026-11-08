import json,tempfile
from unittest.mock import patch
from pathlib import Path
from datetime import date
from django.test import TestCase,override_settings
from django.contrib.auth.models import User,Group
from django.utils import timezone
from django.db import connections
from .models import Family,Delivery,RuntimeState,Audit,BackupConfirmation
from .services import create_family,deliver,decide_family
from .backups import create_snapshot,validate_payload,load_empty_database,write_backup,read_backup,record_confirmation,backup_due,stage_recovery,sha256
from .test_support import temporary_database
class OnlineTests(TestCase):
    def setUp(self):
        self.admin=User.objects.create_superuser('admin',password='Ficticio-para-testes-987!')
        self.clock=patch('django.utils.timezone.localdate',return_value=date(2025,11,8));self.clock.start();self.addCleanup(self.clock.stop)
        self.f=create_family(self.admin,has_children="yes",months=3,name='Família online fictícia',birth=date(1980,1,1),kind='CPF',number='10000000795',identity_kind='RG',identity_number='RG10000000795',address='Rua Exemplo',start=timezone.localdate(),residents_count=2,children_school_frequency='Frequência informada',screening_reason='other',screening_notes='Informações essenciais',personal_documents_seen=True,address_proof_seen=True)
        decide_family(self.admin,self.f,approved=True,reason='Documentos conferidos e critérios atendidos')
    def test_shared_data_across_different_phone_sessions(self):
        from django.test import Client
        a=Client();b=Client();a.force_login(self.admin);b.force_login(self.admin)
        response=a.post(f'/familias/{self.f.pk}/entrega/',{'recipient':self.f.responsible_id,'period':self.f.benefit.periods.first().pk,'day':'2025-11-08','note':''})
        self.assertEqual(response.status_code,302)
        self.assertContains(b.get(f'/familias/{self.f.pk}/'),'já registrada')
        self.assertEqual(Delivery.objects.count(),1)
    def test_html_date_values_are_iso_for_browser_date_fields(self):
        from .forms import DeliveryForm,PersonEditForm
        day=date(2026,11,6)
        form=DeliveryForm(self.f,initial={'day':day})
        self.assertIn('value="2026-11-06"',str(form['day']))
        person=PersonEditForm(initial={'birth_date':date(1980,2,10)})
        self.assertIn('value="1980-02-10"',str(person['birth_date']))
    def test_consultation_and_withdrawals_are_separate(self):
        self.assertEqual(self.client.get('/consulta/').status_code,302)
        self.assertEqual(self.client.get('/retiradas/').status_code,302)
        self.client.force_login(self.admin)
        home=self.client.get('/')
        for link in ['/consulta/','/familias/nova/','/agenda/','/relatorios/','/triagem/']:
            self.assertContains(home,'href="'+link+'"')
        result=self.client.get('/consulta/?q=online')
        self.assertContains(result,'Família online fictícia')
        self.assertContains(result,f'href="/consulta/{self.f.pk}/"')
        self.assertNotContains(result,'Atender família')
        self.assertNotContains(self.client.get('/consulta/?q=INEXISTENTE'),'Família online fictícia')
        detail=self.client.get(f'/consulta/{self.f.pk}/')
        self.assertContains(detail,'Agenda e histórico das cestas')
        self.assertContains(detail,'Voltar à consulta')
        for action in ['Confirmar entrega','Editar cadastro','Incluir</a>','Corrigir dados /','Registrar retirada do papel','Anotar correção']:
            self.assertNotContains(detail,action)
        self.assertContains(self.client.get('/agenda/'),'Agenda de entregas')
        self.assertContains(self.client.get(f'/familias/{self.f.pk}/'),'Confirmar entrega')
        deliver(self.admin,self.f,self.f.responsible)
        self.assertNotContains(self.client.get('/retiradas/'),'Família online fictícia')
        self.assertContains(self.client.get('/retiradas/?status=retirado'),'Família online fictícia')
        self.assertContains(self.client.get('/consulta/'),'Família online fictícia')
        self.assertRedirects(self.client.get('/familias/?q=online'),'/consulta/?q=online')
    def test_pdf_export_filters_empty_and_removes_team_routes(self):
        from pypdf import PdfReader
        from io import BytesIO
        self.client.force_login(self.admin)
        response=self.client.get('/relatorios/familias.pdf')
        self.assertEqual(response['Content-Type'],'application/pdf')
        self.assertTrue(response.content.startswith(b'%PDF-'))
        content=''.join(p.extract_text() for p in PdfReader(BytesIO(response.content)).pages)
        self.assertIn('Família online fictícia',content)
        empty=self.client.get('/relatorios/familias.pdf?q=INEXISTENTE')
        self.assertIn('Nenhuma família encontrada',''.join(p.extract_text() for p in PdfReader(BytesIO(empty.content)).pages))
        self.assertEqual(self.client.get('/usuarios/').status_code,404)
        self.assertEqual(self.client.get('/usuarios/1/').status_code,404)
        self.assertNotContains(self.client.get('/'),'href="/usuarios/"')
        self.assertContains(self.client.get('/relatorios/'),'Baixar relatório em PDF')
    def test_backup_download_is_admin_only_and_does_not_claim_external_copy(self):
        self.client.force_login(self.admin)
        response=self.client.post('/backup/')
        self.assertEqual(response.status_code,200)
        payload=json.loads(response.content)
        self.assertEqual(validate_payload(payload)['core.family'],1)
        self.assertIn('attachment',response['Content-Disposition'])
        self.assertTrue(backup_due());self.assertFalse(BackupConfirmation.objects.exists())
    def test_login_attempts_are_throttled(self):
        for _ in range(5):self.client.post('/entrar/',{'username':'admin','password':'incorreta'})
        self.assertEqual(self.client.post('/entrar/',{'username':'admin','password':'incorreta'}).status_code,429)
    def test_maintenance_blocks_all_phones(self):
        RuntimeState.objects.update_or_create(pk=1,defaults={'writes_paused':True})
        self.client.force_login(self.admin)
        self.assertEqual(self.client.post(f'/familias/{self.f.pk}/entrega/',{'recipient':self.f.responsible_id}).status_code,503)
        self.assertEqual(Delivery.objects.count(),0)
    def test_backup_validation_rejects_extended_benefit_and_duplicate_delivery(self):
        deliver(self.admin,self.f,self.f.responsible)
        p=json.loads(create_snapshot())
        period=next(r for r in p['objects'] if r['model']=='core.period');period['fields']['end']='2099-01-01'
        with self.assertRaises(ValueError):validate_payload(p)
        p=json.loads(create_snapshot());d=next(r for r in p['objects'] if r['model']=='core.delivery');copy=json.loads(json.dumps(d));copy['pk']=99999;p['objects'].append(copy)
        with self.assertRaises(ValueError):validate_payload(p)
    def test_external_copy_requires_explicit_confirmation(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'backup.json';write_backup(path)
            self.assertTrue(backup_due())
            record_confirmation(path,'Dispositivo independente de testes')
            self.assertFalse(backup_due())
            self.assertEqual(read_backup(path)[2]['core.family'],1)
    def test_unencrypted_remote_database_rejected(self):
        from config.database import database_config
        from django.core.exceptions import ImproperlyConfigured
        with self.assertRaises(ImproperlyConfigured):database_config('postgresql://user:pass@example.com/db?sslmode=disable',allow_local=True)

@override_settings(CESTAS_SETUP_TOKEN='x'*64)
class FirstSetupTests(TestCase):
    def test_setup_requires_secret_link_and_closes_after_first_account(self):
        self.assertEqual(self.client.get('/configurar-inicial/').status_code,404)
        self.assertEqual(self.client.get('/configurar-inicial/?token=incorreto').status_code,404)
        self.assertEqual(self.client.get('/configurar-inicial/?token='+'x'*64).status_code,200)
        response=self.client.post('/configurar-inicial/',{'setup_token':'x'*64,'username':'gestor','password1':'Ficticio-configuracao-874!','password2':'Ficticio-configuracao-874!'})
        self.assertEqual(response.status_code,302)
        user=User.objects.get(username='gestor');self.assertTrue(user.is_superuser)
        self.assertTrue(Audit.objects.filter(action='Criar primeiro administrador').exists())
        self.assertEqual(self.client.get('/configurar-inicial/?token='+'x'*64).status_code,404)
    def test_wrong_token_cannot_create_admin(self):
        response=self.client.post('/configurar-inicial/',{'setup_token':'errado','username':'intruso','password1':'Ficticio-configuracao-874!','password2':'Ficticio-configuracao-874!'})
        self.assertEqual(response.status_code,404);self.assertFalse(User.objects.exists())
