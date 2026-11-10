from datetime import date, time, timedelta
from unittest.mock import patch
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from .models import Family, Benefit, Delivery, Audit
from .services import create_family, decide_family, deliver, authorize_extension, authorize_reschedule
from .backups import create_snapshot

class ClientWorkflowTests(TestCase):
    def test_cpf_verification_offers_new_period_only_after_end(self):
        family=self.intake(start=self.today-timedelta(days=370));self.approve(family)
        self.client.force_login(self.coordinator)
        response=self.client.post('/familias/nova/',{'number':'52998224725','check_cpf':'1'})
        self.assertContains(response,'Esta pessoa já foi atendida')
        self.assertContains(response,f'/familias/{family.pk}/prorrogacao/')
        response=self.client.post(f'/familias/{family.pk}/prorrogacao/',{'months':'2'})
        self.assertEqual(response.status_code,302)
        family.refresh_from_db()
        self.assertEqual(family.benefit.periods.count(),5)
        response=self.client.post('/familias/nova/',{'number':'52998224725','check_cpf':'1'})
        self.assertNotContains(response,'Sim, iniciar novo atendimento')

    def test_real_delivery_can_be_before_planned_date(self):
        family=self.intake(start=date(2024,1,1));self.approve(family)
        period=family.benefit.periods.first()
        actual=family.benefit.original_start
        self.assertLess(actual,period.scheduled_on)
        self.assertEqual(deliver(self.coordinator,family,family.responsible,period=period,day=actual).delivered_on,actual)
        self.assertTrue(create_snapshot())

    def test_real_delivery_date_can_follow_planned_period_without_duplicate(self):
        family=self.intake(start=self.today-timedelta(days=370)); self.approve(family)
        period=family.benefit.periods.first()
        actual=period.start+timedelta(days=40)
        delivery=deliver(self.coordinator,family,family.responsible,period=period,day=actual)
        self.assertEqual(delivery.delivered_on,actual)
        self.assertNotEqual(delivery.delivered_on,period.scheduled_on)
        with self.assertRaises(ValidationError):
            deliver(self.coordinator,family,family.responsible,period=period,day=actual)
        self.assertTrue(create_snapshot())

    def test_extension_requires_one_to_three_months_and_no_reason(self):
        family=self.intake(start=self.today-timedelta(days=370));self.approve(family)
        extension=authorize_extension(self.coordinator,family,months=2)
        self.assertEqual(extension.months,2)
        with self.assertRaises(ValidationError):
            authorize_extension(self.coordinator,family,months=4)

    def test_historical_access_is_restricted_and_cannot_record_today(self):
        family=self.intake(); self.approve(family)
        self.client.force_login(self.volunteer)
        self.assertEqual(self.client.get(f'/familias/{family.pk}/entrega/?historico=1').status_code,403)
        with self.assertRaises(PermissionDenied):
            deliver(self.volunteer,family,family.responsible,day=self.today,historical=True,note='Registro anterior')
        with self.assertRaises(ValidationError):
            deliver(self.coordinator,family,family.responsible,day=self.today,historical=True,note='Registro anterior')

    def test_database_restricts_historical_records_to_coordinator_and_past_dates(self):
        family=self.intake(start=self.today-timedelta(days=370));self.approve(family)
        period=family.benefit.periods.first()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Delivery.objects.create(period=period,recipient=family.responsible,delivered_on=self.today-timedelta(days=1),recorded_by=self.volunteer,historical=True,note='Importação antiga')
        with self.assertRaises(IntegrityError), transaction.atomic():
            Delivery.objects.create(period=period,recipient=family.responsible,delivered_on=self.today,recorded_by=self.coordinator,historical=True,note='Importação antiga')

    def test_reschedule_requires_time(self):
        family=self.intake(); self.approve(family)
        period=family.benefit.periods.first()
        with self.assertRaisesMessage(ValidationError,'horário'):
            authorize_reschedule(self.coordinator,period,day=period.start,time=None,reason='Solicitação justificada')

    def setUp(self):
        self.coordinator=User.objects.create_superuser('coord','coord@example.test','Not-a-real-password-123!')
        self.volunteer=User.objects.create_user('volunteer',password='Not-a-real-password-123!')
        self.volunteer.groups.add(Group.objects.get_or_create(name='Atendentes')[0])
        self.today=timezone.localdate()

    def intake(self,*,address='Rua do Exemplo 900',start=None,cpf='52998224725'):
        return create_family(self.volunteer,has_children='yes',months=3,name='Pessoa de Teste',birth=date(1985,1,1),kind='CPF',number=cpf,identity_kind='RG',identity_number='RG'+cpf,address=address,start=start or self.today,residents_count=3,children_school_frequency='Frequência informada',screening_reason='health',screening_notes='Problema de saúde que afetou a renda',personal_documents_seen=True,address_proof_seen=True)

    def approve(self,family):
        decide_family(self.coordinator,family,approved=True,reason='Documentos e critérios conferidos')

    def test_new_family_form_submits_with_hidden_cpf_type(self):
        self.client.force_login(self.volunteer)
        response=self.client.post('/familias/nova/',{'name':'Cadastro de Teste','birth':'1985-01-01','kind':'CPF','number':'52998224725','identity_kind':'RG','identity_number':'RG98765','address':'Rua Formulário 100','start':self.today.isoformat(),'residents_count':'3','has_children':'yes','months':'2','children_school_frequency':'Frequenta escola','screening_reason':'health','screening_notes':'Situação informada pela família','personal_documents_seen':'on','address_proof_seen':'on'})
        self.assertEqual(response.status_code,302)
        family=Family.objects.get(responsible__name='Cadastro de Teste')
        self.assertEqual(family.status,'pending')
        self.assertEqual(family.benefit.periods.count(),2)

    def test_triage_blocks_delivery_until_coordinator_approves(self):
        family=self.intake()
        self.assertEqual(family.status,'pending')
        with self.assertRaisesMessage(ValidationError,'aguardando decisão'):
            deliver(self.volunteer,family,family.responsible)
        with self.assertRaises(PermissionDenied):
            decide_family(self.volunteer,family,approved=True,reason='Atendimento conferido')
        with self.assertRaisesMessage(ValidationError,'comprovante'):
            decide_family(self.coordinator,family,approved=True,reason='Atendimento conferido',screening={'personal_documents_seen':True,'address_proof_seen':False})
        self.approve(family)
        self.assertEqual(family.status,'approved')
        self.assertTrue(Audit.objects.filter(target=str(family.pk),action='Aprovar triagem').exists())

    def test_coordinator_can_complete_triage_from_the_phone_friendly_form(self):
        family=self.intake(address='Rua do Exemplo 904')
        self.client.force_login(self.coordinator)
        self.assertContains(self.client.get('/triagem/'),family.responsible.name)
        response=self.client.post(f'/triagem/{family.pk}/aprovar/',{'triage-'+str(family.pk)+'-residents_count':'3','triage-'+str(family.pk)+'-months':'2','triage-'+str(family.pk)+'-has_children':'on','triage-'+str(family.pk)+'-children_school_frequency':'Frequência informada','triage-'+str(family.pk)+'-screening_reason':'health','triage-'+str(family.pk)+'-screening_notes':'Situação conferida pela coordenação','triage-'+str(family.pk)+'-personal_documents_seen':'on','triage-'+str(family.pk)+'-address_proof_seen':'on','triage-'+str(family.pk)+'-reason':'Documentos e critérios revisados','triage-'+str(family.pk)+'-cpf_number':'52998224725','triage-'+str(family.pk)+'-identity_kind':'RG','triage-'+str(family.pk)+'-identity_number':'RG52998224725'})
        self.assertEqual(response.status_code,302)
        family.refresh_from_db();self.assertEqual(family.status,'approved')
        self.assertEqual(Audit.objects.filter(target=str(family.pk),action='Aprovar triagem').latest('id').after['months'],2)
        benefit=Benefit.objects.get(family=family)
        self.assertEqual(benefit.policy['months'],2)
        self.assertEqual(benefit.periods.count(),2)

    def test_triage_validation_preserves_entered_data(self):
        family = self.intake()
        self.client.force_login(self.coordinator)
        prefix = f'triage-{family.pk}-'
        response = self.client.post(f'/triagem/{family.pk}/aprovar/', {
            prefix + 'residents_count': '3',
            prefix + 'months': '1',
            prefix + 'screening_reason': 'health',
            prefix + 'screening_notes': 'Observação de teste preservada',
        })
        self.assertContains(response, 'comprovante de endereço')
        self.assertContains(response, 'Observação de teste preservada')
        family.refresh_from_db()
        self.assertEqual(family.status, 'pending')

    def test_configuration_change_records_distribution_time(self):
        self.client.force_login(self.coordinator)
        response = self.client.post('/configuracoes/', {
            'institute': 'Instituto de teste', 'document_types': 'CPF,RG',
            'distribution_time': '10:30', 'backup_interval_hours': 24, 'backup_keep': 30,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Audit.objects.get(action='Configuração').after['distribution_time'], '10:30:00')

    def test_monthly_schedule_is_second_saturday_and_miss_does_not_release_basket(self):
        family=self.intake(address='Rua do Exemplo 901')
        self.approve(family)
        periods=list(family.benefit.periods.all())
        self.assertEqual(len(periods),3)
        for p in periods:
            self.assertEqual(p.scheduled_on.weekday(),5)
            self.assertTrue(8<=p.scheduled_on.day<=14)
        missed=periods[0].scheduled_on+timedelta(days=1)
        with patch('django.utils.timezone.localdate',return_value=missed):
            with self.assertRaises(ValidationError):deliver(self.volunteer,family,family.responsible)
        self.assertEqual(Delivery.objects.count(),0)

    def test_coordinator_can_authorize_one_alternate_date_and_record_it(self):
        family=self.intake(address='Rua do Exemplo 902')
        self.approve(family)
        period=family.benefit.periods.first()
        alternate=period.start+timedelta(days=1)
        authorize_reschedule(self.coordinator,period,day=alternate,time=time(14,30),reason='Solicitante doente, coordenação autorizou',supporting_document_seen=True)
        self.client.force_login(self.coordinator)
        with patch('django.utils.timezone.localdate',return_value=period.scheduled_on):
            self.assertContains(self.client.get('/consulta/'),f'Próxima entrega: {alternate:%d/%m/%Y}')
            self.assertEqual(self.client.get('/').context['pending'],0)
            with self.assertRaises(ValidationError):deliver(self.volunteer,family,family.responsible)
            self.assertContains(self.client.get(f'/familias/{family.pk}/entrega/'),f'Entrega prevista para {alternate:%d/%m/%Y}')
        with patch('django.utils.timezone.localdate',return_value=alternate):
            self.assertEqual(self.client.get('/').context['pending'],1)
            page=self.client.get(f'/familias/{family.pk}/entrega/')
            self.assertContains(page,alternate.strftime('%d/%m/%Y'))
            self.assertContains(page,'14:30')
            if alternate<=self.today:
                delivery=deliver(self.volunteer,family,family.responsible)
                self.assertEqual(delivery.delivered_on,alternate)
        with self.assertRaises(ValidationError):
            authorize_reschedule(self.coordinator,period,day=alternate+timedelta(days=1),time=None,reason='Outra data autorizada')

    def test_exceptional_extension_adds_only_the_authorized_months(self):
        start=self.today-timedelta(days=370)
        family=self.intake(address='Rua do Exemplo 903',start=start,cpf='10000000108')
        self.approve(family)
        authorization=authorize_extension(self.coordinator,family,months=2,reason='Doença comprometeu a subsistência familiar')
        self.assertEqual(authorization.months,2)
        self.assertEqual(family.benefit.periods.count(),5)
        self.assertEqual(family.benefit.periods.order_by('-number').first().number,5)
        self.assertTrue(Audit.objects.filter(target=str(family.pk),action='Autorizar prorrogação').exists())
        self.assertTrue(create_snapshot())
