from datetime import date
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from .services import create_family
from .backups import create_snapshot, validate_payload, signature

class NewPolicyTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('teste-politica', password='Senha-ficticia-987!')
        self.today = timezone.localdate()
    def make(self, **kwargs):
        values = dict(name='Pessoa fictícia', birth=date(1980,1,1), kind='CPF', number='10000000108', identity_kind='RG',identity_number='RG10000000108',address='Rua Exemplo 12', start=self.today, has_children='yes', months=3,residents_count=2,children_school_frequency='Frequência escolar informada',screening_reason='other',screening_notes='Informações essenciais',personal_documents_seen=True,address_proof_seen=True)
        values.update(kwargs)
        if 'number' in kwargs and 'identity_number' not in kwargs: values['identity_number']='RG'+str(kwargs['number'])
        return create_family(self.admin, **values)
    def test_durations_and_backup(self):
        family=self.make()
        self.assertEqual(family.benefit.periods.count(),3)
        self.assertTrue(create_snapshot())
        other=self.make(name='Outra',number='10000000280',address='Rua Dois',has_children='no',months=1)
        self.assertEqual(other.benefit.periods.count(),1)
        with self.assertRaises(ValidationError):
            self.make(name='Terceira',number='10000000876',address='Rua Tres',has_children='no',months=2)
    def test_cpf_and_address(self):
        self.make()
        with self.assertRaises(ValidationError):
            self.make(name='Outra',number='10000000280',address='rua exemplo, 12')
        with self.assertRaises(ValidationError):
            self.make(name='Outra',kind='RG',number='10000000280',address='Rua Dois')
        with self.assertRaises(ValidationError):
            self.make(name='Outra',number='123',address='Rua Dois')

    def test_previous_schema_signed_backup_remains_valid(self):
        import json
        self.make()
        payload = json.loads(create_snapshot())
        payload['schema'] = [entry for entry in payload['schema'] if entry[1] not in {'0004_duration','0005_client_workflow','0006_extension_period_limit','0007_client_workflow_guards','0008_screening_reasons','0009_exception_document_flag','0010_delivery_actual_date','0011_triage_schedule_and_delivery_guards'}]
        payload['signature'] = signature(payload)
        self.assertEqual(validate_payload(payload)['core.family'], 1)

    def test_cpf_check_digits(self):
        from .services import valid_cpf
        self.assertTrue(valid_cpf('529.982.247-25'))
        self.assertFalse(valid_cpf('529.982.247-24'))
        self.assertFalse(valid_cpf('111.111.111-11'))
