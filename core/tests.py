import sqlite3
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
from contextlib import closing
from unittest.mock import patch
from django.test import TestCase, Client
from django.contrib.auth.models import User,Group
from django.core.exceptions import ValidationError,PermissionDenied
from django.db import connection, IntegrityError, transaction
from .models import Person,Document,Family,Benefit,Period,Delivery,Membership,Configuration,Audit
from .periods import periods,add_months
from .services import create_family,add_member,edit_family,deliver,eligibility,normalize

class RulesTests(TestCase):
    def setUp(self):
        self.admin=User.objects.create_superuser('admin',password='Ficticio-para-testes-987!')
        self.operator=User.objects.create_user('atendente',password='Ficticio-para-testes-987!')
        self.operator.groups.add(Group.objects.get_or_create(name='Atendentes')[0])
        self.clock=patch('django.utils.timezone.localdate',return_value=date(2025,1,20));self.clock.start();self.addCleanup(self.clock.stop)
        self.f=create_family(self.operator,name='Maria Exemplo',birth=date(1980,3,2),kind='CPF',number='111.222.333-44',address='Rua Fictícia 1',start=date(2025,1,15))
    def test_six_calendar_periods(self):
        self.assertEqual(self.f.benefit.periods.count(),6)
        self.assertEqual(self.f.benefit.periods.first().start,date(2025,1,15))
        self.assertEqual(self.f.benefit.periods.last().end,date(2025,7,1))
    def test_one_delivery_duplicate_and_repeated_request(self):
        deliver(self.operator,self.f,self.f.responsible)
        with self.assertRaisesMessage(ValidationError,'já registrada'): deliver(self.operator,self.f,self.f.responsible)
        self.client.force_login(self.operator)
        for _ in range(2):
            response=self.client.post(f'/familias/{self.f.pk}/entrega/',{'recipient':self.f.responsible_id,'note':''})
            self.assertContains(response,'já registrada')
        self.assertEqual(Delivery.objects.count(),1)
    def test_expired_and_no_accumulation(self):
        self.assertIsNone(eligibility(self.f,date(2025,7,1))[0])
        with patch('django.utils.timezone.localdate',return_value=date(2025,7,20)):
            with self.assertRaisesMessage(ValidationError,'encerrado'): deliver(self.operator,self.f,self.f.responsible)
        self.assertEqual(Period.objects.count(),6)
    def test_no_renewal_or_extension_even_queryset(self):
        benefit_id=self.f.benefit.pk
        for operation in [lambda:Benefit.objects.filter(pk=self.f.benefit.pk).update(original_start=date(2026,1,1)),lambda:Period.objects.filter(benefit=self.f.benefit).update(end=date(2030,1,1)),lambda:Benefit.objects.filter(pk=self.f.benefit.pk).delete()]:
            with self.assertRaises(IntegrityError),transaction.atomic(): operation()
        with self.assertRaises(IntegrityError),transaction.atomic():
            Benefit.objects.create(family=self.f,original_start=date(2025,1,1),mode='calendar',policy=self.f.benefit.policy,created_by=self.admin)
        with self.assertRaises(IntegrityError),transaction.atomic():
            Period.objects.create(benefit_id=benefit_id,number=7,start=date(2025,7,1),end=date(2025,8,1))
    def test_change_responsible_does_not_restart(self):
        p=add_member(self.operator,self.f,name='João Exemplo',birth=date(1978,4,9),kind='CPF',number='55566677788',relationship='Cônjuge')
        before=list(self.f.benefit.periods.values_list('start','end'))
        edit_family(self.operator,self.f,'','Rua 2',p,'Troca solicitada pela família')
        self.assertEqual(before,list(self.f.benefit.periods.values_list('start','end')))
        self.assertEqual(self.f.benefit.original_start,date(2025,1,15))
    def test_recreating_original_responsible_blocked_after_replacement(self):
        original=self.f.responsible
        p=add_member(self.operator,self.f,name='Outro Exemplo',birth=date(1982,1,1),kind='CPF',number='123123',relationship='Cônjuge')
        edit_family(self.operator,self.f,'','Rua 2',p,'Troca de responsável')
        with self.assertRaises(ValidationError):create_family(self.admin,person_id=original.pk,address='Outro endereço',start=date(2025,1,1),review_reason='Tentativa de novo cadastro')
    def test_normalized_document_collision(self):
        self.assertEqual(normalize('abc-12.3'),'ABC123')
        with self.assertRaisesMessage(ValidationError,'já cadastrado'):create_family(self.operator,name='Novo Nome',birth=date(1980,1,1),kind='CPF',number='11122233344',address='Rua 3',start=date(2025,1,1))
        self.assertEqual(Family.objects.count(),1)
    def test_address_coincidence_does_not_block(self):
        f=create_family(self.operator,name='Família diferente',birth=date(1983,3,2),kind='CPF',number='22233344455',address='Rua Fictícia 1',start=date(2025,1,1))
        self.assertNotEqual(self.f.pk,f.pk)
    def test_previous_dependent_can_form_family_with_admin_review(self):
        p=add_member(self.operator,self.f,name='Filha Exemplo',birth=date(2000,1,1),kind='CPF',number='99988877766',relationship='Filha')
        with self.assertRaises(PermissionDenied):create_family(self.operator,person_id=p.pk,address='Rua nova',start=date(2025,1,1),review_reason='Constituiu outra família')
        f=create_family(self.admin,person_id=p.pk,address='Rua nova',start=date(2025,1,1),review_reason='Análise: constituiu outra família independente')
        self.assertEqual(p.memberships.count(),2);self.assertEqual(f.benefit.periods.count(),6)
    def test_historical_import_preserves_start(self):
        self.f=create_family(self.operator,name='Cadastro do papel',birth=date(1970,1,1),kind='CPF',number='778899',address='Rua 4',start=date(2024,8,30))
        d=deliver(self.operator,self.f,self.f.responsible,day=date(2024,9,10),historical=True,note='Caderno de setembro, folha 8')
        self.assertTrue(d.historical);self.assertEqual(d.recorded_by,self.operator)
        self.assertEqual(self.f.benefit.periods.last().end,date(2025,2,1))
        with patch('django.utils.timezone.localdate',return_value=date(2025,2,1)):
            with self.assertRaises(ValidationError):deliver(self.operator,self.f,self.f.responsible)
    def test_future_and_outside_period(self):
        with self.assertRaises(ValidationError):deliver(self.operator,self.f,self.f.responsible,day=date(2025,1,21),historical=True,note='Nota teste')
        with self.assertRaises(ValidationError):deliver(self.operator,self.f,self.f.responsible,day=date(2024,12,20),historical=True,note='Nota teste')
    def test_policy_change_only_affects_new_benefits(self):
        c=Configuration.current();c.period_mode='anniversary';c.save()
        self.f.benefit.refresh_from_db();self.assertEqual(self.f.benefit.mode,'calendar')
        f=create_family(self.operator,name='Nova família',birth=date(1985,1,1),kind='CPF',number='897453',address='Rua 9',start=date(2025,1,20))
        self.assertEqual(f.benefit.periods.first().end,date(2025,2,20))
    def test_permissions_and_csrf(self):
        for path in ['/','/consulta/','/retiradas/','/familias/','/relatorios/familias.pdf','/configuracoes/','/auditoria/']:
            self.assertEqual(self.client.get(path).status_code,302)
        self.client.force_login(self.operator)
        for path in ['/configuracoes/','/auditoria/']:
            self.assertEqual(self.client.get(path).status_code,403)
        self.assertEqual(self.client.post('/backup/').status_code,403)
        c=Client(enforce_csrf_checks=True);c.force_login(self.operator)
        self.assertEqual(c.post(f'/familias/{self.f.pk}/entrega/',{}).status_code,403)
        outsider=User.objects.create_user('sem_perfil');self.client.force_login(outsider)
        self.assertEqual(self.client.get('/familias/').status_code,403)
    def test_login_uses_password_hash_and_rejects_wrong_password(self):
        self.assertNotEqual(self.operator.password,'Ficticio-para-testes-987!')
        self.assertFalse(self.client.login(username='atendente',password='senha-incorreta'))
        response=self.client.post('/entrar/',{'username':'atendente','password':'Ficticio-para-testes-987!'})
        self.assertEqual(response.status_code,302)
        self.assertEqual(self.client.get('/consulta/').status_code,200)
    def test_all_pages_render_and_export(self):
        self.client.force_login(self.admin)
        for path in ['/','/consulta/','/retiradas/',f'/consulta/{self.f.pk}/',f'/familias/{self.f.pk}/',f'/familias/{self.f.pk}/editar/',f'/familias/{self.f.pk}/integrante/',f'/familias/{self.f.pk}/entrega/',f'/familias/{self.f.pk}/entrega/?historico=1','/familias/nova/','/configuracoes/','/auditoria/',f'/pessoas/{self.f.responsible_id}/editar/']:
            with self.subTest(path=path):self.assertEqual(self.client.get(path).status_code,200)
        response=self.client.get('/relatorios/familias.pdf');self.assertEqual(response.status_code,200);self.assertIn('no-store',response['Cache-Control'])
    def test_recipient_membership_and_delivery_immutable(self):
        p=Person.objects.create(name='Pessoa avulsa',birth_date=date(1980,1,1))
        with self.assertRaises(ValidationError): deliver(self.operator,self.f,p)
        d=deliver(self.operator,self.f,self.f.responsible)
        with self.assertRaises(IntegrityError),transaction.atomic():Delivery.objects.filter(pk=d.pk).delete()
        with self.assertRaises(IntegrityError),transaction.atomic():Delivery.objects.filter(pk=d.pk).update(delivered_on=date(2025,2,1))
    def test_delivery_correction_is_annotation_and_cannot_reopen(self):
        d=deliver(self.operator,self.f,self.f.responsible)
        self.client.force_login(self.operator)
        self.assertEqual(self.client.post(f'/entregas/{d.pk}/anotar/',{'correction':'Pessoa que retirou informada incorretamente no papel'}).status_code,403)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.post(f'/entregas/{d.pk}/anotar/',{'correction':'Pessoa que retirou informada incorretamente no papel'}).status_code,302)
        self.assertEqual(Delivery.objects.count(),1)
        self.assertTrue(Audit.objects.filter(action='Anotação de correção de entrega').exists())
        self.assertIsNone(eligibility(self.f)[0])
    def test_person_correction_preserves_previous_values(self):
        self.client.force_login(self.operator)
        response=self.client.post(f'/pessoas/{self.f.responsible_id}/editar/',{'name':'Maria Corrigida','birth_date':'1980-03-02','kind':'CPF','number':'','reason':'Conferência com cadastro original'})
        self.assertEqual(response.status_code,302)
        self.assertTrue(Audit.objects.filter(action='Corrigir pessoa',before__name='Maria Exemplo').exists())
        self.assertTrue(Document.objects.filter(number='11122233344').exists())
class DateTests(TestCase):
    def test_calendar_year_boundary(self):
        p=periods(date(2024,11,30),'calendar')
        self.assertEqual(p[-1][1],date(2025,5,1));self.assertEqual(len(p),6)
    def test_anniversary_january31_and_leap_year(self):
        p=periods(date(2024,1,31),'anniversary')
        self.assertEqual(p[0][1],date(2024,2,29));self.assertEqual(p[1][1],date(2024,3,31));self.assertEqual(p[-1][1],date(2024,7,31))
        self.assertEqual(add_months(date(2025,1,31),1),date(2025,2,28))
    def test_calendar_first_partial_month_counts(self):
        p=periods(date(2025,1,31),'calendar');self.assertEqual(p[0],(date(2025,1,31),date(2025,2,1)));self.assertEqual(p[-1][1],date(2025,7,1))
