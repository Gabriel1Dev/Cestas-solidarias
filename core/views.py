from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Family, Person, Document, Benefit, Period, Delivery, Audit, Configuration, BackupRun, BackupConfirmation
from .forms import FamilyForm, MemberForm, EditFamilyForm, DeliveryForm, ConfigurationForm, PersonEditForm
from . import services
def brand(request):
    try:
        from .backups import backup_due
        return {'institute':Configuration.current().institute,'backup_overdue':backup_due()}
    except Exception: return {'institute':'Cestas Solidárias'}
def error(form,exc): form.add_error(None,' '.join(exc.messages))
def family_rows(q='',status=''):
    qs=Family.objects.select_related('responsible','benefit').order_by('responsible__name')
    if q:
        docs=Document.objects.filter(number__contains=services.normalize(q)).values('person_id') if services.normalize(q) else []
        qs=qs.filter(Q(memberships__person__name__icontains=q)|Q(memberships__person_id__in=docs)|Q(address__icontains=q)).distinct()
    today=timezone.localdate(); rows=[]
    for f in qs:
        p,label=services.eligibility(f,today)
        end=f.benefit.periods.last().end
        state='encerrado' if today>=end else ('retirado' if not p else 'disponivel')
        if not status or status==state: rows.append({'family':f,'label':label,'period':p,'end':end-timedelta(days=1),'state':state})
    return rows
@login_required
def dashboard(request):
    services.operator(request.user)
    today=timezone.localdate(); rows=family_rows()
    active=[r for r in rows if r['state']!='encerrado']
    return render(request,'dashboard.html',{'active':len(active),'month_deliveries':Delivery.objects.filter(delivered_on__year=today.year,delivered_on__month=today.month).count(),'pending':sum(r['state']=='disponivel' for r in rows),'ending':sum(today<=r['end']<=today+timedelta(days=30) for r in rows),'closed':len(rows)-len(active),'rows':[r for r in rows if r['state']=='disponivel'][:8],'today':today,'backup':BackupRun.objects.first(),'last_success':BackupConfirmation.objects.order_by('-at').first(),'cfg':Configuration.current()})
@login_required
def families(request):
    services.operator(request.user)
    return redirect('/consulta/?'+request.GET.urlencode()) if request.GET else redirect('consultation')

@login_required
def consultation(request):
    services.operator(request.user)
    q=request.GET.get('q','').strip(); status=request.GET.get('status','')
    return render(request,'families.html',{'rows':family_rows(q,status),'q':q,'status':status,'consultation':True})

@login_required
def withdrawals(request):
    services.operator(request.user)
    q=request.GET.get('q','').strip(); status=request.GET.get('status','disponivel')
    return render(request,'families.html',{'rows':family_rows(q,status),'q':q,'status':status,'withdrawals':True})
@login_required
def new_family(request):
    services.operator(request.user)
    form=FamilyForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        try:
            f=services.create_family(request.user,**form.cleaned_data)
            messages.success(request,'Família cadastrada. Confira os seis períodos e inclua os integrantes.')
            return redirect('family',pk=f.pk)
        except ValidationError as e: error(form,e)
        except Person.DoesNotExist: form.add_error('person_id','Pessoa não encontrada.')
    return render(request,'form.html',{'form':form,'title':'Cadastrar família','intro':'Um cadastro permanente por família. Confira o papel antes de informar o início original.','button':'Salvar família'})
@login_required
def family(request,pk):
    services.operator(request.user)
    f=get_object_or_404(Family.objects.select_related('responsible','benefit'),pk=pk)
    p,label=services.eligibility(f)
    similar=Family.objects.filter(Q(address__iexact=f.address)|Q(responsible__name__iexact=f.responsible.name)|Q(responsible__birth_date=f.responsible.birth_date)).exclude(pk=f.pk).select_related('responsible')[:10]
    data=[]; today=timezone.localdate()
    for period in f.benefit.periods.select_related('delivery','delivery__recipient','delivery__recorded_by'):
        d=getattr(period,'delivery',None)
        data.append({'p':period,'last':period.end-timedelta(days=1),'d':d,'status':'Retirada registrada' if d else ('Não retirou' if today>=period.end else ('Aguardando período' if today<period.start else 'Disponível'))})
    return render(request,'family.html',{'consultation':request.resolver_match.url_name=='consultation_family','family':f,'period':p,'label':label,'periods':data,'members':f.memberships.select_related('person').prefetch_related('person__documents'),'similar':similar,'audits':Audit.objects.filter(target=str(f.pk))[:30]})
@login_required
def member(request,pk):
    services.operator(request.user); f=get_object_or_404(Family,pk=pk)
    form=MemberForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        try:
            services.add_member(request.user,f,**form.cleaned_data)
            messages.success(request,'Integrante incluído. Vínculos anteriores foram preservados.'); return redirect('family',pk=pk)
        except ValidationError as e: error(form,e)
        except Person.DoesNotExist: form.add_error('person_id','Pessoa não encontrada.')
    return render(request,'form.html',{'form':form,'title':'Incluir integrante','intro':str(f),'button':'Incluir integrante'})
@login_required
def edit(request,pk):
    services.operator(request.user); f=get_object_or_404(Family,pk=pk)
    form=EditFamilyForm(f,request.POST or None,initial={'phone':f.phone,'address':f.address,'responsible':f.responsible_id})
    if request.method=='POST' and form.is_valid():
        try:
            services.edit_family(request.user,f,**form.cleaned_data)
            messages.success(request,'Cadastro atualizado com histórico da alteração.'); return redirect('family',pk=pk)
        except ValidationError as e: error(form,e)
    return render(request,'form.html',{'form':form,'title':'Editar família','intro':'A troca de responsável preserva o início original e os seis períodos.','button':'Salvar alteração'})
@login_required
def delivery(request,pk):
    services.operator(request.user); f=get_object_or_404(Family.objects.select_related('responsible','benefit'),pk=pk)
    historical=request.GET.get('historico')=='1'
    p,label=services.eligibility(f)
    form=DeliveryForm(f,request.POST or None,initial={'recipient':f.responsible_id,'day':timezone.localdate()})
    if not historical:
        form.fields['day'].disabled=True
    if request.method=='POST' and form.is_valid():
        try:
            services.deliver(request.user,f,historical=historical,**form.cleaned_data)
            messages.success(request,'Entrega registrada com sucesso.'); return redirect('family',pk=pk)
        except ValidationError as e: error(form,e)
    return render(request,'delivery.html',{'form':form,'family':f,'historical':historical,'period':p,'label':label})
@login_required
def settings_view(request):
    services.admin(request.user); cfg=Configuration.current()
    form=ConfigurationForm(request.POST or None,instance=cfg)
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            before=Configuration.objects.values().get(pk=1)
            form.save()
            services.audit(request.user,'Configuração','config','Alteração pelo administrador',before,Configuration.objects.values().get(pk=1))
        messages.success(request,'Configurações salvas. Benefícios existentes mantêm seus períodos.'); return redirect('settings')
    return render(request,'settings.html',{'form':form,'runs':BackupRun.objects.all()[:15],'last_success':BackupConfirmation.objects.order_by('-at').first(),'cfg':cfg})
@login_required
@require_POST
def backup(request):
    services.admin(request.user)
    from .backups import create_snapshot
    try:
        data=create_snapshot()
        if len(data)>4_000_000:
            messages.error(request,'O arquivo excede o limite de download web. Use o comando de backup administrativo para gerar a cópia completa.')
            return redirect('settings')
        BackupRun.objects.create(success=True,detail='Arquivo completo gerado para download. Guarda externa não confirmada.')
        services.audit(request.user,'Gerar backup completo','backup','Download administrativo; guarda externa não confirmada')
        response=HttpResponse(data,content_type='application/json; charset=utf-8')
        response['Content-Disposition']='attachment; filename="cestas-backup-'+timezone.now().strftime('%Y%m%dT%H%M%S')+'.json"'
        response['Cache-Control']='no-store'
        return response
    except Exception:
        BackupRun.objects.create(success=False,detail='Falha ao gerar backup completo para download.')
        messages.error(request,'Não foi possível gerar a cópia. Nenhuma confirmação de guarda externa foi registrada. Procure o administrador técnico.')
        return redirect('settings')
@login_required
def reports(request):
    services.operator(request.user)
    return render(request,'reports.html',{'q':request.GET.get('q','').strip()})
@login_required
def export(request):
    services.operator(request.user)
    from .reports import families_pdf
    q=request.GET.get('q','').strip();status=request.GET.get('status','')
    labels={'':'Todas as situações','disponivel':'Podem retirar agora','retirado':'Já retiraram neste período','encerrado':'Benefício encerrado'}
    if status not in labels:
        messages.error(request,'Selecione uma situação válida para o relatório.')
        return redirect('reports')
    rows=family_rows(q,status)
    selection=labels[status]+(' | Busca: '+q if q else '')
    data=families_pdf(rows,Configuration.current().institute,timezone.localtime(),request.user.username,selection)
    response=HttpResponse(data,content_type='application/pdf')
    response['Content-Disposition']='attachment; filename="relatorio-familias-'+timezone.localdate().strftime('%Y-%m-%d')+'.pdf"'
    response['Cache-Control']='no-store'
    services.audit(request.user,'Exportação PDF','report','Relatório de famílias',after={'count':len(rows),'status':status,'query':q})
    return response
@login_required
def audits(request):
    services.admin(request.user)
    return render(request,'audit.html',{'audits':Audit.objects.select_related('actor').all()[:300]})
@login_required
def person_edit(request,pk):
    services.operator(request.user); p=get_object_or_404(Person,pk=pk)
    form=PersonEditForm(request.POST or None,initial={'name':p.name,'birth_date':p.birth_date})
    if request.method=='POST' and form.is_valid():
        data=form.cleaned_data
        try:
            with transaction.atomic():
                if data['birth_date']>timezone.localdate(): raise ValidationError('Nascimento não pode estar no futuro.')
                number=services.normalize(data['number'])
                if number and Document.objects.filter(number=number).exists(): raise ValidationError('Documento já cadastrado. Confira a pessoa existente; não foi feita nenhuma alteração.')
                before={'name':p.name,'birth_date':str(p.birth_date)}
                p.name=data['name']; p.birth_date=data['birth_date']; p.save(update_fields=['name','birth_date'])
                if number: Document.objects.create(person=p,kind=data['kind'],number=number)
                services.audit(request.user,'Corrigir pessoa',f'person:{pk}',data['reason'],before,{'name':p.name,'birth_date':str(p.birth_date),'added_document':number})
                for m in p.memberships.all(): services.audit(request.user,'Corrigir dados de integrante',m.family_id,data['reason'],before,{'name':p.name,'birth_date':str(p.birth_date),'added_document':number})
            messages.success(request,'Dados corrigidos com histórico preservado.')
            return redirect('families')
        except ValidationError as e: error(form,e)
    return render(request,'form.html',{'form':form,'title':f'Corrigir pessoa #{pk}','intro':'A correção se aplica à mesma pessoa em todos os vínculos. Documentos antigos e benefícios permanecem preservados.','button':'Salvar correção'})
@login_required
def annotate_delivery(request,pk):
    services.admin(request.user)
    from django import forms
    d=get_object_or_404(Delivery.objects.select_related('period__benefit__family'),pk=pk)
    class CorrectionForm(forms.Form):
        correction=forms.CharField(label='Informação correta e motivo da correção',min_length=10,max_length=1000,widget=forms.Textarea)
    form=CorrectionForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        services.audit(request.user,'Anotação de correção de entrega',d.period.benefit.family_id,form.cleaned_data['correction'],{'delivery':d.pk,'date':str(d.delivered_on),'recipient':d.recipient_id,'period':d.period.number},{'annotation':form.cleaned_data['correction'],'original_preserved':True})
        messages.success(request,'Correção anexada ao histórico. O registro original e o limite do período permanecem preservados.')
        return redirect('family',pk=d.period.benefit.family_id)
    return render(request,'form.html',{'form':form,'title':f'Anotar correção da entrega #{pk}','intro':'A anotação preserva a entrega original. Ela não libera outra cesta nem modifica a vigência.','button':'Registrar anotação'})
