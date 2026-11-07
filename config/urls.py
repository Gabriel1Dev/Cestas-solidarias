from django.urls import path
from django.contrib.auth import views as auth
from core import views
from core.auth_views import RateLimitedLoginView,first_setup
urlpatterns=[path('pessoas/<int:pk>/editar/',views.person_edit,name='person_edit'),path('entregas/<int:pk>/anotar/',views.annotate_delivery,name='annotate_delivery')]
urlpatterns += [path('configurar-inicial/',first_setup,name='first_setup')]
urlpatterns += [path('',views.dashboard,name='dashboard'),path('entrar/',RateLimitedLoginView.as_view(),name='login'),path('sair/',auth.LogoutView.as_view(),name='logout'),path('familias/',views.families,name='families'),path('consulta/',views.consultation,name='consultation'),path('consulta/<int:pk>/',views.family,name='consultation_family'),path('retiradas/',views.withdrawals,name='withdrawals'),path('familias/nova/',views.new_family,name='new_family'),path('familias/<int:pk>/',views.family,name='family'),path('familias/<int:pk>/editar/',views.edit,name='edit'),path('familias/<int:pk>/integrante/',views.member,name='member'),path('familias/<int:pk>/entrega/',views.delivery,name='delivery'),path('configuracoes/',views.settings_view,name='settings'),path('backup/',views.backup,name='backup'),path('relatorios/',views.reports,name='reports'),path('relatorios/familias.pdf',views.export,name='export'),path('auditoria/',views.audits,name='audits')]
