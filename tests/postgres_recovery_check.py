"""Integration suite in generated, disposable PostgreSQL databases on loopback."""
import os,sys,json,tempfile,secrets,threading
from datetime import date
from pathlib import Path
from uuid import uuid4
from urllib.parse import urlparse,urlunparse
from concurrent.futures import ThreadPoolExecutor
import psycopg
from psycopg import sql
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
def main():
    template=os.environ['CESTAS_TEST_DATABASE_URL']
    parts=urlparse(template)
    if parts.hostname not in ('localhost','127.0.0.1','::1'):raise RuntimeError('Esta suíte exige PostgreSQL de testes em loopback.')
    name='cestas_check_'+uuid4().hex[:16]
    admin_url=urlunparse(parts._replace(path='/postgres'))
    with psycopg.connect(admin_url,autocommit=True) as db:db.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
    try:
        os.environ['DATABASE_URL']=urlunparse(parts._replace(path='/'+name))
        os.environ['DJANGO_SECRET_KEY']=secrets.token_urlsafe(64)
        os.environ['CESTAS_LOCAL_TEST']='1'
        os.environ['DJANGO_SETTINGS_MODULE']='config.settings'
        import django
        django.setup()
        from django.core.management import call_command
        from django.contrib.auth.models import User,Group
        from django.db import connections
        from django.utils import timezone
        from core.models import Family,Delivery,RuntimeState,Audit
        from core.services import create_family,deliver
        from core.backups import create_snapshot,load_empty_database,read_backup,write_backup,stage_recovery,sha256,configure_target
        from core.test_support import temporary_database
        call_command('migrate',interactive=False,verbosity=0)
        user=User.objects.create_superuser('admin',password=secrets.token_urlsafe(30))
        op=User.objects.create_user('operador');op.groups.add(Group.objects.get_or_create(name='Atendentes')[0])
        f=create_family(user,name='Família fictícia',birth=date(1980,1,1),kind='CPF',number='123456',address='Rua de testes',start=timezone.localdate())
        period_id=f.benefit.periods.first().pk;person_id=f.responsible_id;user_id=user.pk
        barrier=threading.Barrier(2)
        def writer(_):
            with psycopg.connect(os.environ['DATABASE_URL']) as db:
                barrier.wait()
                try:
                    db.execute('INSERT INTO core_delivery(period_id,recipient_id,delivered_on,recorded_at,recorded_by_id,historical,note) VALUES(%s,%s,%s,NOW(),%s,false,%s)',(period_id,person_id,timezone.localdate(),user_id,''));db.commit();return 'ok'
                except psycopg.IntegrityError:return 'blocked'
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(writer,range(2)))
        assert sorted(results)==['blocked','ok'] and Delivery.objects.count()==1
        print('PASS: duas conexões PostgreSQL disputam a entrega; apenas uma grava')
        with tempfile.TemporaryDirectory(prefix='cestas-backup-') as td:
            source=Path(td)/'backup.json';write_backup(source)
            raw,payload,counts=read_backup(source)
            with temporary_database() as (alias,target):
                restored=load_empty_database(payload,alias)
                assert restored==counts and Delivery.objects.using(alias).count()==1
                assert RuntimeState.objects.using(alias).get(pk=1).writes_paused
                assert Audit.objects.using(alias).count()==Audit.objects.count()
                try:load_empty_database(payload,alias);raise AssertionError('Destino preenchido aceito')
                except ValueError:pass
            print('PASS: ensaio importa em outro banco, preserva histórico e mantém destino suspenso')
            print('PASS: destino preenchido é rejeitado sem exclusão dos dados existentes')
            receipt=Path(td)/'receipt.json';receipt.write_text(json.dumps({'sha256':sha256(raw),'counts':counts}),encoding='utf-8')
            create_family(user,name='Depois do backup',birth=date(1990,1,1),kind='CPF',number='998877',address='Outra rua',start=timezone.localdate())
            with temporary_database() as (alias,target):
                # Build a URL from the temporary database settings without printing credentials.
                new_name=connections[alias].settings_dict['NAME']
                target_url=urlunparse(parts._replace(path='/'+new_name))
                try:stage_recovery(source,target_url,op,Path(td)/'denied.json',receipt);raise AssertionError('Atendente restaurou')
                except Exception as e:
                    from django.core.exceptions import PermissionDenied
                    assert isinstance(e,PermissionDenied)
                print('PASS: restauração é restrita a administrador')
                missing=Path(td)/'wrong-receipt.json';missing.write_text(json.dumps({'sha256':'invalid'}),encoding='utf-8')
                try:stage_recovery(source,target_url,user,Path(td)/'unused.json',missing);raise AssertionError('Arquivo sem ensaio aceito')
                except ValueError:pass
                print('PASS: restauração exige comprovante do arquivo exato')
                prior=Path(td)/'before.json'
                stage_recovery(source,target_url,user,prior,receipt)
                assert Family.objects.count()==2
                assert Family.objects.using(alias).count()==1
                assert Delivery.objects.using(alias).count()==1
                assert read_backup(prior)[2]['core.family']==2
                assert RuntimeState.objects.get(pk=1).writes_paused and RuntimeState.objects.using(alias).get(pk=1).writes_paused
                print('PASS: recuperação preserva banco original e cópia anterior; novo banco contém o histórico da cópia')
                print('PASS: ambos os bancos permanecem suspensos até conferência e liberação explícitas')
        connections.close_all()
    finally:
        if 'django.db' in sys.modules:
            from django.db import connections
            connections.close_all()
        assert name.startswith('cestas_check_') and len(name)==29
        with psycopg.connect(admin_url,autocommit=True) as db:
            db.execute('SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=%s AND pid<>pg_backend_pid()',[name])
            db.execute(sql.SQL('DROP DATABASE {}').format(sql.Identifier(name)))
    print('7 verificações integradas concluídas em bancos PostgreSQL temporários.')
if __name__=='__main__':main()
