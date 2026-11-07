"""Generate a signed backup only when due, for a private Actions artifact."""
import os,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from core.backups import backup_due,write_backup
from core.models import Configuration,BackupRun
from core.locking import maintenance_lock
event=json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text(encoding='utf-8'))
if not event.get('repository',{}).get('private'):raise RuntimeError('O agendamento de cópias exige repositório privado.')
with maintenance_lock():
    ready=backup_due()
    retention=min(90,max(2,Configuration.current().backup_keep))
    if ready:
        Path('backups').mkdir(exist_ok=True)
        write_backup('backups/backup.json')
        BackupRun.objects.create(success=True,detail='Arquivo completo gerado pelo agendamento. Upload externo ainda não confirmado.')
with open(os.environ['GITHUB_OUTPUT'],'a',encoding='utf-8') as f:
    f.write(f'ready={str(ready).lower()}\nretention={retention}\n')
print('Arquivo preparado para guarda externa.' if ready else 'Última cópia confirmada ainda dentro do intervalo.')
