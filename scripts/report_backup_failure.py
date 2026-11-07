import os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from core.models import BackupRun
from core.locking import maintenance_lock
with maintenance_lock():BackupRun.objects.create(success=False,detail='O agendamento falhou. Nenhuma nova guarda externa foi confirmada; confira o responsável técnico e a execução privada.')
