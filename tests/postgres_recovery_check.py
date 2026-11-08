"""Integration suite in generated, disposable PostgreSQL databases on loopback."""
import os,sys,json,tempfile,secrets,threading
from datetime import date, timedelta
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
        from core.services import create_family,deliver,decide_family
        from core.backups import create_snapshot,load_empty_database,read_backup,write_backup,stage_recovery,sha256,configure_target
        from core.test_support import temporary_database
        call_command('migrate',interactive=False,verbosity=0)
        user=User.objects.create_superuser('admin',password=secrets.token_urlsafe(30))
        op=User.objects.create_user('operador');op.groups.add(Group.objects.get_or_create(name='Atendentes')[0])
        f=create_family(user,has_children="yes",months=3,name='Família fictícia',birth=date(1980,1,1),kind='CPF',number='10000000957',identity_kind='RG',identity_number='RG10000000957',address='Rua de testes',start=timezone.localdate()-timedelta(days=50),residents_count=2,children_school_frequency='Frequência informada',screening_reason='other',screening_notes='Informações registradas',personal_documents_seen=True,address_proof_seen=True)
        decide_family(user,f,approved=True,reason='Documentos e critérios conferidos')
        first_period=f.benefit.periods.first()
        period_id=first_period.pk;delivery_day=first_period.scheduled_on;person_id=f.responsible_id;user_id=user.pk
        barrier=threading.Barrier(2)
        def writer(_):
            with psycopg.connect(os.environ['DATABASE_URL']) as db:
                barrier.wait()
                try:
                    db.execute('INSERT INTO core_delivery(period_id,recipient_id,delivered_on,recorded_at,recorded_by_id,historical,note) VALUES(%s,%s,%s,NOW(),%s,false,%s)',(period_id,person_id,delivery_day,user_id,''));db.commit();return 'ok'
                except psycopg.IntegrityError:return 'blocked'
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(writer,range(2)))
        assert sorted(results)==['blocked','ok'] and Delivery.objects.count()==1
        print('PASS: duas conexões PostgreSQL disputam a entrega; apenas uma grava')
        with tempfile.TemporaryDirectory(prefix='cestas-backup-') as td:
            source=Path(td)/'backup.json';write_backup(source)
            raw,payload,counts=read_backup(source)
            # A signed pre-migration snapshot contained a six-period immutable benefit.
            from core.backups import signature, validate_payload
            from core.periods import periods
            legacy=json.loads(raw)
            legacy['format']='cestas-online-v2'
            legacy['schema']=[entry for entry in legacy['schema'] if entry[1] not in {'0004_duration','0005_client_workflow','0006_extension_period_limit','0007_client_workflow_guards','0008_screening_reasons','0009_exception_document_flag','0010_delivery_actual_date','0011_triage_schedule_and_delivery_guards'}]
            benefit=next(obj for obj in legacy['objects'] if obj['model']=='core.benefit')
            initial=date.fromisoformat(benefit['fields']['original_start'])
            benefit['fields']['mode']='calendar'
            boundaries=periods(initial,'calendar',6)
            policy=benefit['fields']['policy']
            policy.update(version=1, months=6,mode='calendar', periods=[{'start':str(a),'end':str(b)} for a,b in boundaries])
            policy.pop('has_children',None)
            old_periods=[obj for obj in legacy['objects'] if obj['model']=='core.period']
            legacy['objects']=[obj for obj in legacy['objects'] if obj['model']!='core.period']
            legacy_periods=[]
            for number,(start,end) in enumerate(boundaries,1):
                period_pk=old_periods[number-1]['pk'] if number<=len(old_periods) else max((p['pk'] for p in old_periods),default=0)+number
                legacy_periods.append({'model':'core.period','pk':period_pk,'fields':{'benefit':benefit['pk'],'number':number,'start':str(start),'end':str(end),'scheduled_on':None,'scheduled_time':None,'extension':None}})
            insert_at=next((i for i,obj in enumerate(legacy['objects']) if obj['model'] in ('core.scheduleauthorization','core.delivery')),len(legacy['objects']))
            legacy['objects'][insert_at:insert_at]=legacy_periods
            legacy['signature']=signature(legacy)
            legacy_counts=validate_payload(legacy)
            with temporary_database() as (legacy_alias,legacy_target):
                assert load_empty_database(legacy,legacy_alias)==legacy_counts
                from core.models import Benefit
                assert Benefit.objects.using(legacy_alias).get().periods.count()==6
            print('PASS: cópia antiga assinada com seis períodos recuperada em banco separado')
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
            create_family(user,has_children="yes",months=3,name='Depois do backup',birth=date(1990,1,1),kind='CPF',number='10000001090',identity_kind='RG',identity_number='RG10000001090',address='Outra rua',start=timezone.localdate(),residents_count=1,children_school_frequency='Frequência informada',screening_reason='other',screening_notes='Informações registradas',personal_documents_seen=True,address_proof_seen=True)
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
