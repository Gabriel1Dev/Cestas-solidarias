import os,getpass,json
from django.contrib.auth import authenticate
from django.core.management.base import BaseCommand,CommandError
from core.backups import stage_recovery
class Command(BaseCommand):
    help='Suspende o banco atual, preserva cópia e restaura em novo banco ensaiado. Não substitui a produção.'
    def add_arguments(self,p):
        p.add_argument('arquivo');p.add_argument('--usuario',required=True);p.add_argument('--comprovante',required=True);p.add_argument('--copia-atual',required=True);p.add_argument('--confirmar',action='store_true')
    def handle(self,*args,**opts):
        if not opts['confirmar']:raise CommandError('Ensaie a cópia e use --confirmar apenas no procedimento de recuperação.')
        u=authenticate(username=opts['usuario'],password=getpass.getpass('Senha do administrador atual: '))
        if not u or not u.is_superuser:raise CommandError('Administrador ativo e senha válidos são obrigatórios.')
        target=os.environ.get('CESTAS_RESTORE_DATABASE_URL')
        if not target:raise CommandError('Defina CESTAS_RESTORE_DATABASE_URL para outro banco novo, com migrações aplicadas.')
        try:
            result=stage_recovery(opts['arquivo'],target,u,opts['copia_atual'],opts['comprovante'])
            self.stdout.write('Restauração preparada. Os dois bancos estão suspensos. Confira os dados, troque a conexão da hospedagem e libere explicitamente o banco escolhido. '+json.dumps(result))
        except Exception as e:raise CommandError(str(e))
