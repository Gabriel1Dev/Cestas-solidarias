import re
import unicodedata
from datetime import date
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction, IntegrityError
from django.utils import timezone
from .models import Person, Document, Family, Membership, Benefit, Period, Delivery, Audit, Configuration
from .periods import periods
def normalize(value):
    return re.sub(r'[^A-Z0-9]','',unicodedata.normalize('NFKD',value).encode('ascii','ignore').decode().upper())
def audit(user,action,target,reason,before=None,after=None):
    return Audit.objects.create(actor=user,action=action,target=str(target),reason=reason,before=before or {},after=after or {})
def operator(user):
    if not user.is_active or not (user.is_superuser or user.groups.filter(name='Atendentes').exists()):
        raise PermissionDenied
def admin(user):
    if not user.is_active or not user.is_superuser: raise PermissionDenied
def identify(name,birth,kind,number,required=True):
    number=normalize(number)
    if not name.strip() or not birth or birth>timezone.localdate(): raise ValidationError('Informe nome e nascimento válidos.')
    if not number and required: raise ValidationError('Documento obrigatório.')
    if number:
        config=Configuration.current()
        if kind not in [x.strip() for x in config.document_types.split(',')]: raise ValidationError('Tipo de documento não aceito.')
        existing=Document.objects.select_related('person').filter(number=number).first()
        if existing: raise ValidationError(f'Documento já cadastrado para {existing.person.name}, pessoa #{existing.person_id}. Consulte a família existente ou use o identificador dessa pessoa.')
    person=Person.objects.create(name=name.strip(),birth_date=birth)
    if number: Document.objects.create(person=person,kind=kind,number=number)
    return person
@transaction.atomic
def create_family(user,*,name='',birth=None,kind='',number='',phone='',address='',start=None,person_id=None,review_reason=''):
    operator(user)
    cfg=Configuration.current()
    if not address.strip(): raise ValidationError('Informe o endereço.')
    if cfg.phone_required and not phone.strip(): raise ValidationError('Informe o telefone.')
    if not start or start>timezone.localdate(): raise ValidationError('O início original não pode estar no futuro.')
    if person_id:
        p=Person.objects.get(pk=person_id)
        if not p.documents.exists(): raise ValidationError('O responsável precisa de documento.')
        prior=p.memberships.exists()
        if prior:
            admin(user)
            if len(review_reason.strip())<10: raise ValidationError('Registre a análise da formação de outra família (mínimo 10 caracteres).')
        if p.represented_families.exists() or p.memberships.filter(relationship='Responsável original').exists():
            raise ValidationError('Essa pessoa já representa ou representou família. Consulte e atualize o cadastro permanente; um novo ciclo não é permitido.')
    else: p=identify(name,birth,kind,number)
    f=Family.objects.create(responsible=p,phone=phone.strip(),address=address.strip())
    Membership.objects.create(family=f,person=p,relationship='Responsável original')
    boundaries=periods(start,cfg.period_mode)
    b=Benefit.objects.create(family=f,original_start=start,mode=cfg.period_mode,policy={'version':1,'months':6,'renewable':False,'missed_accumulate':False,'mode':cfg.period_mode,'periods':[{'start':str(a),'end':str(z)} for a,z in boundaries]},created_by=user)
    for n,(a,z) in enumerate(boundaries,1): Period.objects.create(benefit=b,number=n,start=a,end=z)
    audit(user,'Criar família e benefício',f.pk,review_reason or 'Cadastro inicial',after={'responsible':p.pk,'start':str(start),'policy':b.policy})
    return f
@transaction.atomic
def add_member(user,family,*,name='',birth=None,kind='',number='',relationship='',person_id=None,review_reason=''):
    operator(user)
    if not relationship.strip(): raise ValidationError('Informe o parentesco ou vínculo.')
    p=Person.objects.get(pk=person_id) if person_id else identify(name,birth,kind,number,Configuration.current().dependent_documents)
    if p.memberships.filter(family=family).exists(): raise ValidationError('Essa pessoa já possui vínculo com a família.')
    if p.memberships.exclude(family=family).exists():
        admin(user)
        if len(review_reason.strip())<10: raise ValidationError('Pessoa vinculada a outra família: registre uma análise administrativa.')
    if Configuration.current().dependent_documents and not p.documents.exists(): raise ValidationError('Documento do integrante é obrigatório na configuração atual.')
    Membership.objects.create(family=family,person=p,relationship=relationship.strip())
    audit(user,'Incluir integrante',family.pk,review_reason or 'Inclusão de integrante',after={'person':p.pk,'relationship':relationship})
    return p
@transaction.atomic
def edit_family(user,family,phone,address,responsible,reason):
    operator(user)
    if len(reason.strip())<5: raise ValidationError('Informe o motivo da alteração.')
    if not address.strip(): raise ValidationError('Informe o endereço.')
    if Configuration.current().phone_required and not phone.strip(): raise ValidationError('Informe telefone.')
    if not Membership.objects.filter(family=family,person=responsible,ended_at__isnull=True).exists(): raise ValidationError('Responsável deve integrar a família.')
    if not responsible.documents.exists(): raise ValidationError('O responsável precisa de documento. Procure o administrador para completar a identificação.')
    if responsible.represented_families.exclude(pk=family.pk).exists(): raise ValidationError('Essa pessoa já é responsável por outra família. Solicite análise administrativa dos vínculos antes de alterar.')
    before={'phone':family.phone,'address':family.address,'responsible':family.responsible_id}
    family.phone=phone.strip(); family.address=address.strip(); family.responsible=responsible
    family.save(update_fields=['phone','address','responsible'])
    audit(user,'Alterar família',family.pk,reason,before,{'phone':family.phone,'address':family.address,'responsible':responsible.pk})
def eligibility(family,day=None):
    day=day or timezone.localdate()
    p=family.benefit.periods.filter(start__lte=day,end__gt=day).first()
    if not p: return None,'Benefício encerrado.' if day>=family.benefit.periods.last().end else 'Atendimento ainda não começou.'
    if Delivery.objects.filter(period=p).exists(): return None,f'Retirada do período {p.number}/6 já registrada.'
    return p,f'Pode retirar • período {p.number}/6'
@transaction.atomic
def deliver(user,family,recipient,*,day=None,historical=False,note=''):
    operator(user)
    today=timezone.localdate()
    day=day or today
    if day>today: raise ValidationError('Não é permitido registrar entrega futura.')
    if day!=today and not historical: raise ValidationError('Use o registro histórico para datas anteriores.')
    if historical and len(note.strip())<5: raise ValidationError('Informe a fonte ou motivo do registro histórico.')
    if not family.memberships.filter(person=recipient,ended_at__isnull=True).exists(): raise ValidationError('Quem retirou deve ser integrante da família.')
    p,message=eligibility(family,day)
    if not p: raise ValidationError(message)
    try:
        with transaction.atomic():
            d=Delivery.objects.create(period=p,recipient=recipient,delivered_on=day,recorded_by=user,historical=historical,note=note.strip())
    except IntegrityError:
        raise ValidationError('Essa retirada já foi registrada. Nenhuma segunda cesta foi lançada.')
    audit(user,'Entrega histórica' if historical else 'Entrega',family.pk,note or 'Retirada confirmada',after={'delivery':d.pk,'period':p.number,'recipient':recipient.pk,'date':str(day)})
    return d
