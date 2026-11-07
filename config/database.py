from urllib.parse import urlparse,unquote,parse_qs
from django.core.exceptions import ImproperlyConfigured
def database_config(value,allow_local=False):
    url=urlparse(value)
    if url.scheme not in ('postgres','postgresql') or not url.hostname or not url.path.strip('/'):
        raise ImproperlyConfigured('Defina DATABASE_URL com uma conexão PostgreSQL válida.')
    query=parse_qs(url.query)
    sslmode=query.get('sslmode',['require'])[0]
    if sslmode not in ('require','verify-ca','verify-full') and not (allow_local and url.hostname in ('127.0.0.1','localhost','::1')):
        raise ImproperlyConfigured('PostgreSQL remoto exige TLS; use sslmode=require ou verificação mais forte.')
    return {'ENGINE':'django.db.backends.postgresql','NAME':unquote(url.path.lstrip('/')),'USER':unquote(url.username or ''),'PASSWORD':unquote(url.password or ''),'HOST':url.hostname,'PORT':url.port or 5432,'CONN_MAX_AGE':0,'DISABLE_SERVER_SIDE_CURSORS':True,'OPTIONS':{'sslmode':sslmode,'connect_timeout':15}}
