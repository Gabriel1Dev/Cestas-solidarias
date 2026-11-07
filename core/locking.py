"""Transaction lock shared by every server instance and operator command."""
from contextlib import contextmanager
from django.db import transaction,connection
from django.http import HttpResponse
LOCK_ID=734812900126
@contextmanager
def maintenance_lock():
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL lock_timeout = '15s'")
            cursor.execute('SELECT pg_advisory_xact_lock(%s)',[LOCK_ID])
        yield
class MaintenanceMiddleware:
    def __init__(self,get_response):self.get_response=get_response
    def __call__(self,request):
        with maintenance_lock():
            from .models import RuntimeState
            if RuntimeState.objects.filter(pk=1,writes_paused=True).exists():
                response=HttpResponse('Atendimento temporariamente suspenso para manutenção. Aguarde a liberação pelo administrador.',status=503,content_type='text/plain; charset=utf-8')
                response['Retry-After']='300'
            else:response=self.get_response(request)
            response['Cache-Control']='no-store'
            return response
