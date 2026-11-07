import getpass
from django.contrib.auth import authenticate
from django.core.management.base import BaseCommand,CommandError
from core.locking import maintenance_lock
from core.models import RuntimeState
from core.services import audit
class Command(BaseCommand):
    def add_arguments(self,p):p.add_argument('--usuario',required=True)
    def handle(self,*args,**opts):
        u=authenticate(username=opts['usuario'],password=getpass.getpass('Senha do administrador: '))
        if not u or not u.is_superuser:raise CommandError('Administrador ativo e senha válidos são obrigatórios.')
        with maintenance_lock():
            RuntimeState.objects.update_or_create(pk=1,defaults={'writes_paused':False})
            audit(u,'Retomar atendimento','recovery','Liberação após conferência administrativa')
        self.stdout.write('Atendimento liberado neste banco. Confira a conexão usada na hospedagem.')
