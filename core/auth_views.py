import hashlib,hmac
from datetime import timedelta
from django.conf import settings
from django.contrib.auth.views import LoginView
from django.utils import timezone
from .models import LoginAttempt
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.shortcuts import render,redirect
from django.http import Http404
from .services import audit

def first_setup(request):
    expected=getattr(settings,'CESTAS_SETUP_TOKEN','')
    supplied=request.POST.get('setup_token','') if request.method=='POST' else request.GET.get('token','')
    if not expected or not hmac.compare_digest(supplied,expected) or User.objects.exists():raise Http404
    form=UserCreationForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        user=form.save(commit=False);user.is_superuser=True;user.is_staff=True;user.save()
        audit(user,'Criar primeiro administrador',f'user:{user.pk}','Configuração inicial por link de uso único')
        login(request,user,backend='django.contrib.auth.backends.ModelBackend')
        return redirect('dashboard')
    return render(request,'first_setup.html',{'form':form,'setup_token':supplied})
class RateLimitedLoginView(LoginView):
    template_name='login.html'
    def fingerprint(self):
        text=self.request.POST.get('username','').strip().casefold()+'|'+self.request.META.get('REMOTE_ADDR','')
        return hmac.new(settings.SECRET_KEY.encode(),text.encode(),hashlib.sha256).hexdigest()
    def post(self,request,*args,**kwargs):
        attempt=LoginAttempt.objects.filter(fingerprint=self.fingerprint()).first()
        if attempt and attempt.failures>=5 and timezone.now()-attempt.window_start<timedelta(minutes=15):
            form=self.get_form();form.add_error(None,'Muitas tentativas. Aguarde 15 minutos para tentar novamente.')
            response=self.render_to_response(self.get_context_data(form=form),status=429);response['Retry-After']='900';return response
        return super().post(request,*args,**kwargs)
    def form_invalid(self,form):
        attempt,_=LoginAttempt.objects.get_or_create(fingerprint=self.fingerprint(),defaults={'window_start':timezone.now()})
        if timezone.now()-attempt.window_start>=timedelta(minutes=15):attempt.window_start=timezone.now();attempt.failures=0
        attempt.failures+=1;attempt.save(update_fields=['window_start','failures'])
        # Keep the table bounded by removing expired counters, not attendance history.
        LoginAttempt.objects.filter(window_start__lt=timezone.now()-timedelta(days=1)).delete()
        return super().form_invalid(form)
    def form_valid(self,form):
        LoginAttempt.objects.filter(fingerprint=self.fingerprint()).delete()
        return super().form_valid(form)
