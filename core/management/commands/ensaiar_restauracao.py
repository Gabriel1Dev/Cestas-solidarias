import os,json
from pathlib import Path
from django.core.management.base import BaseCommand,CommandError
from django.utils import timezone
from core.backups import read_backup,configure_target,load_empty_database,sha256
class Command(BaseCommand):
    help='Importa uma cópia em banco novo e isolado indicado por CESTAS_DRILL_DATABASE_URL.'
    def add_arguments(self,p):p.add_argument('arquivo');p.add_argument('--comprovante',required=True)
    def handle(self,*args,**opts):
        try:
            raw,payload,counts=read_backup(opts['arquivo'])
            url=os.environ.get('CESTAS_DRILL_DATABASE_URL')
            if not url:raise ValueError('Defina CESTAS_DRILL_DATABASE_URL para um banco vazio, com migrações aplicadas.')
            alias=configure_target(url,'drill')
            result=load_empty_database(payload,alias)
            if result!=counts:raise ValueError('As contagens restauradas diferem da origem.')
            receipt={'sha256':sha256(raw),'counts':result,'tested_at':timezone.now().isoformat(),'format':'cestas-drill-v2'}
            with Path(opts['comprovante']).open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False)
            self.stdout.write('Ensaio concluído em banco separado, mantido em modo manutenção. '+json.dumps(result))
        except Exception as e:raise CommandError(str(e))
