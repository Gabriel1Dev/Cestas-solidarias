from django.core.management.base import BaseCommand,CommandError
from core.backups import write_backup,backup_due
from core.locking import maintenance_lock
from core.models import BackupRun
class Command(BaseCommand):
    help='Gera backup JSON completo e consistente. Não confirma sozinho uma cópia externa.'
    def add_arguments(self,p):
        p.add_argument('--output',required=True);p.add_argument('--if-due',action='store_true')
    def handle(self,*args,**opts):
        try:
            with maintenance_lock():
                if opts['if_due'] and not backup_due():self.stdout.write('Cópia externa ainda dentro do intervalo.');return
                checksum=write_backup(opts['output'])
                BackupRun.objects.create(success=True,detail='Arquivo completo gerado; guarda externa ainda não confirmada.')
            self.stdout.write('Backup completo gerado. Confirme a guarda externa após copiar. SHA-256: '+checksum)
        except Exception as e:
            BackupRun.objects.create(success=False,detail=type(e).__name__+': falha ao gerar cópia')
            raise CommandError(str(e))
