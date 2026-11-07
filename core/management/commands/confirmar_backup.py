from django.core.management.base import BaseCommand,CommandError
from core.backups import record_confirmation
from core.locking import maintenance_lock
class Command(BaseCommand):
    help='Registra confirmação de guarda externa. Use somente após upload/cópia bem-sucedidos.'
    def add_arguments(self,p):p.add_argument('arquivo');p.add_argument('--destino',required=True)
    def handle(self,*args,**opts):
        try:
            with maintenance_lock():record_confirmation(opts['arquivo'],opts['destino'])
            self.stdout.write('Guarda externa confirmada no histórico.')
        except Exception as e:raise CommandError(str(e))
