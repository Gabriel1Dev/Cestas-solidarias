"""Run only against explicitly supplied local test PostgreSQL, not production."""
import os,sys,secrets,subprocess
from pathlib import Path
from urllib.parse import urlparse
root=Path(__file__).resolve().parent.parent
url=os.environ.get('CESTAS_TEST_DATABASE_URL','')
if urlparse(url).hostname not in ('localhost','127.0.0.1','::1'):raise SystemExit('Defina CESTAS_TEST_DATABASE_URL para um PostgreSQL de testes em loopback, com permissão de criar bancos temporários.')
env=os.environ.copy();env.update({'DATABASE_URL':url,'DJANGO_SECRET_KEY':secrets.token_urlsafe(64),'CESTAS_LOCAL_TEST':'1'})
for args in [[str(root/'manage.py'),'test','core','--verbosity','2','--noinput'],[str(root/'tests'/'postgres_recovery_check.py')]]:
    p=subprocess.run([sys.executable,*args],env=env)
    if p.returncode:raise SystemExit(p.returncode)
