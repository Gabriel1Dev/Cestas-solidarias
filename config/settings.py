import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
from .database import database_config
BASE_DIR=Path(__file__).resolve().parent.parent
LOCAL_TEST=os.environ.get('CESTAS_LOCAL_TEST')=='1'
if os.environ.get('VERCEL') and LOCAL_TEST:raise ImproperlyConfigured('Modo de teste local não pode ser usado na hospedagem.')
SECRET_KEY=os.environ.get('DJANGO_SECRET_KEY','')
if len(SECRET_KEY)<40:raise ImproperlyConfigured('Defina DJANGO_SECRET_KEY com ao menos 40 caracteres aleatórios, fora do código.')
CESTAS_BACKUP_SIGNING_KEY=os.environ.get('CESTAS_BACKUP_SIGNING_KEY') or SECRET_KEY
if len(CESTAS_BACKUP_SIGNING_KEY)<40:raise ImproperlyConfigured('A chave de assinatura de backups deve ter ao menos 40 caracteres.')
DEBUG=False
ALLOWED_HOSTS=[h.strip() for h in os.environ.get('CESTAS_HOSTS','127.0.0.1,localhost').split(',') if h.strip()]
deployment_host=os.environ.get('VERCEL_URL','').strip()
if deployment_host.endswith('.vercel.app') and '://' not in deployment_host and '/' not in deployment_host:
    ALLOWED_HOSTS.append(deployment_host)
CSRF_TRUSTED_ORIGINS=[s.strip() for s in os.environ.get('CESTAS_ORIGINS','').split(',') if s.strip()]
if os.environ.get('VERCEL') and not os.environ.get('CESTAS_HOSTS'):raise ImproperlyConfigured('Configure os domínios exatos em CESTAS_HOSTS.')
DATABASES={'default':database_config(os.environ.get('DATABASE_URL',''),allow_local=LOCAL_TEST)}
INSTALLED_APPS=['django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles','core.apps.CoreConfig']
MIDDLEWARE=['django.middleware.security.SecurityMiddleware','whitenoise.middleware.WhiteNoiseMiddleware','core.locking.MaintenanceMiddleware','django.contrib.sessions.middleware.SessionMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware','django.contrib.auth.middleware.AuthenticationMiddleware','django.contrib.messages.middleware.MessageMiddleware','django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF='config.urls'
WSGI_APPLICATION='config.wsgi.application'
TEMPLATES=[{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[BASE_DIR/'templates'],'APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages','core.views.brand']}}]
AUTH_PASSWORD_VALIDATORS=[{'NAME':'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},{'NAME':'django.contrib.auth.password_validation.MinimumLengthValidator'},{'NAME':'django.contrib.auth.password_validation.CommonPasswordValidator'},{'NAME':'django.contrib.auth.password_validation.NumericPasswordValidator'}]
LANGUAGE_CODE='pt-br'
TIME_ZONE='America/Sao_Paulo'
USE_I18N=True
USE_TZ=True
STATIC_URL='/static/'
STATIC_ROOT=BASE_DIR/'staticfiles'
STATICFILES_DIRS=[BASE_DIR/'static']
DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'
LOGIN_URL='/entrar/'
LOGIN_REDIRECT_URL='/'
LOGOUT_REDIRECT_URL='/entrar/'
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE='Lax'
SESSION_COOKIE_SECURE=not LOCAL_TEST
CSRF_COOKIE_SECURE=not LOCAL_TEST
CSRF_COOKIE_SAMESITE='Lax'
SECURE_SSL_REDIRECT=not LOCAL_TEST
SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO','https') if os.environ.get('VERCEL') else None
SECURE_CONTENT_TYPE_NOSNIFF=True
SECURE_HSTS_SECONDS=2592000 if not LOCAL_TEST else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS=False
SECURE_HSTS_PRELOAD=False
X_FRAME_OPTIONS='DENY'
DATA_UPLOAD_MAX_MEMORY_SIZE=2*1024*1024
SESSION_EXPIRE_AT_BROWSER_CLOSE=True
SESSION_COOKIE_AGE=8*60*60
CESTAS_SETUP_TOKEN=os.environ.get('CESTAS_SETUP_TOKEN','')
if CESTAS_SETUP_TOKEN and len(CESTAS_SETUP_TOKEN)<40:raise ImproperlyConfigured('O link de configuração inicial exige um token aleatório de ao menos 40 caracteres.')
