"""Disposable PostgreSQL databases for tests, never an existing application DB."""
from contextlib import contextmanager
from uuid import uuid4
from django.db import connection,connections
from django.core.management import call_command
import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo
@contextmanager
def temporary_database():
    cfg=connection.settings_dict
    name='cestas_check_'+uuid4().hex[:16]
    alias='check_'+uuid4().hex[:10]
    options={'host':cfg['HOST'],'port':cfg['PORT'],'user':cfg['USER'],'password':cfg['PASSWORD'],'sslmode':cfg['OPTIONS'].get('sslmode','require')}
    admin=make_conninfo(dbname='postgres',**options)
    target=make_conninfo(dbname=name,**options)
    with psycopg.connect(admin,autocommit=True) as c:c.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
    from copy import deepcopy
    settings=deepcopy(cfg);settings['NAME']=name
    connections.databases[alias]=settings
    try:
        call_command('migrate',database=alias,interactive=False,verbosity=0)
        yield alias,target
    finally:
        connections[alias].close()
        assert name.startswith('cestas_check_') and len(name)==29
        with psycopg.connect(admin,autocommit=True) as c:
            c.execute('SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=%s AND pid<>pg_backend_pid()',[name])
            c.execute(sql.SQL('DROP DATABASE {}').format(sql.Identifier(name)))
