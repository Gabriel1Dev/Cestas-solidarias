import re
import unicodedata
from datetime import date, timedelta
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction, IntegrityError, connection
from django.utils import timezone
from .models import Person, Document, Family, Membership, Benefit, Period, Delivery, Audit, Configuration, ExtensionAuthorization, ScheduleAuthorization
from .periods import periods, distribution_periods
def normalize(value):
    return re.sub(r'[^A-Z0-9]','',unicodedata.normalize('NFKD',value).encode('ascii','ignore').decode().upper())
def valid_cpf(value):
    digits = normalize(value)
    if not re.fullmatch(r'[0-9]{11}', digits) or len(set(digits)) == 1:
        return False
    for length in (9, 10):
        total = sum(int(digits[i]) * (length + 1 - i) for i in range(length))
        check = (total * 10 % 11) % 10
        if check != int(digits[length]):
            return False
    return True

def check_address_availability(address, start, end, exclude_family=None):
    # Serialize checks and writes so concurrent registrations cannot both pass.
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(%s)", [730492018])
    key = normalize(address)
    families = Family.objects.select_related('benefit').prefetch_related('benefit__periods')
    if exclude_family is not None:
        families = families.exclude(pk=exclude_family)
    for other in families:
        if other.status=='denied': continue
        if normalize(other.address) != key:
            continue
        other_periods = list(other.benefit.periods.all())
        if other_periods and start < other_periods[-1].end and end > other_periods[0].start:
            raise ValidationError('Já existe atendimento no mesmo endereço durante este período. Consulte o cadastro existente.')

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
def create_family(user,*,has_children=None,months=None,name='',birth=None,kind='',number='',identity_kind='',identity_number='',phone='',address='',start=None,person_id=None,review_reason='',residents_count=1,children_school_frequency='',screening_reason='',screening_notes='',personal_documents_seen=False,address_proof_seen=False):
    operator(user)
    cfg=Configuration.current()
    if not address.strip(): raise ValidationError('Informe o endereço.')
    if cfg.phone_required and not phone.strip(): raise ValidationError('Informe o telefone.')
    if not start or start>timezone.localdate(): raise ValidationError('O início original não pode estar no futuro.')
    if has_children not in ('yes','no') or months not in (1,2,3) or (has_children=='no' and months!=1):
        raise ValidationError('Informe a presença de crianças e uma duração inicial válida.')
    if not 1<=residents_count<=40: raise ValidationError('Informe a quantidade de moradores (1 a 40).')
    if has_children=='yes' and not children_school_frequency.strip(): raise ValidationError('Informe a frequência escolar das crianças ou explique por que não se aplica.')
    if screening_reason not in ('unemployment','health','accident','other'): raise ValidationError('Selecione o motivo da solicitação.')
    boundaries=distribution_periods(start,months)
    check_address_availability(address, boundaries[0][0], boundaries[-1][1])
    if person_id:
        p=Person.objects.get(pk=person_id)
        if not any(valid_cpf(number) for number in p.documents.filter(kind__iexact='CPF').values_list('number', flat=True)):
            raise ValidationError('O responsável precisa ter um CPF válido cadastrado.')

        if not p.documents.filter(kind__iexact='CPF').exists(): raise ValidationError('O responsável precisa ter CPF cadastrado.')
        prior=p.memberships.exists()
        if prior:
            admin(user)
            if len(review_reason.strip())<10: raise ValidationError('Registre a análise da formação de outra família (mínimo 10 caracteres).')
        if p.represented_families.exists() or p.memberships.filter(relationship='Responsável original').exists():
            raise ValidationError('Essa pessoa já representa ou representou família. Consulte e atualize o cadastro permanente; um novo ciclo não é permitido.')
    else:
        if kind.upper() != 'CPF' or not valid_cpf(number):
            raise ValidationError('Informe um CPF válido para o responsável.')
        p=identify(name,birth,kind,number)
    identity_number=normalize(identity_number)
    if identity_number:
        if identity_kind.upper()=='CPF' or identity_kind not in [x.strip() for x in cfg.document_types.split(',')]: raise ValidationError('Informe um documento de identificação aceito, como RG ou outro.')
        existing_identity=Document.objects.filter(number=identity_number).first()
        if existing_identity and existing_identity.person_id!=p.pk: raise ValidationError(f'O documento {identity_kind} informado já pertence a outra pessoa.')
        if not existing_identity: Document.objects.create(person=p,kind=identity_kind,number=identity_number)
    if not p.documents.exclude(kind__iexact='CPF').exists(): raise ValidationError('Cadastre também o RG ou outro documento de identificação.')
    f=Family.objects.create(responsible=p,phone=phone.strip(),address=address.strip(),status='pending',residents_count=residents_count,children_school_frequency=children_school_frequency.strip(),screening_reason=screening_reason,screening_notes=screening_notes.strip(),personal_documents_seen=personal_documents_seen,address_proof_seen=address_proof_seen)
    Membership.objects.create(family=f,person=p,relationship='Responsável original')

    b=Benefit.objects.create(family=f,original_start=start,mode='distribution',policy={'version':3,'has_children':has_children=='yes','months':months,'renewable':False,'missed_accumulate':False,'mode':'distribution','periods':[{'start':str(a),'end':str(z)} for a,z in boundaries]},created_by=user)
    for n,(a,z) in enumerate(boundaries,1): Period.objects.create(benefit=b,number=n,start=a,end=z,scheduled_on=a,scheduled_time=cfg.distribution_time)
    audit(user,'Criar família para triagem',f.pk,'Cadastro aguardando avaliação',after={'responsible':p.pk,'intake_date':str(start),'policy':b.policy,'screening':{'residents':residents_count,'children':has_children=='yes','school_frequency':children_school_frequency,'reason':screening_reason,'documents_seen':personal_documents_seen,'address_proof_seen':address_proof_seen}})
    return f

@transaction.atomic
def decide_family(user,family,*,approved,reason,screening=None):
    admin(user)
    if family.status!='pending': raise ValidationError('Esta triagem já recebeu uma decisão.')
    if not approved and not 10<=len(reason.strip())<=300: raise ValidationError('Explique a não aprovação da triagem (10 a 300 caracteres).')
    if approved and len(reason.strip())>300: raise ValidationError('A justificativa pode ter no máximo 300 caracteres.')
    screening=screening or {}
    children=screening.get('has_children',family.benefit.policy.get('has_children',False))
    months=screening.get('months',family.benefit.policy.get('months',1))
    if months not in (1,2,3) or (not children and months!=1): raise ValidationError('A duração precisa ser de 1 a 3 meses; sem crianças, uma cesta.')
    if children and not screening.get('children_school_frequency',family.children_school_frequency).strip():
        raise ValidationError('Registre a frequência escolar das crianças ou por que não se aplica.')
    if approved:
        cpf=normalize(screening.get('cpf_number',''))
        current_cpfs=list(family.responsible.documents.filter(kind__iexact='CPF').values_list('number',flat=True))
        if cpf:
            if not valid_cpf(cpf): raise ValidationError('Informe um CPF válido do responsável.')
            collision=Document.objects.filter(number=cpf).exclude(person=family.responsible).exists()
            if collision: raise ValidationError('Esse CPF já está vinculado a outra pessoa.')
            if cpf not in current_cpfs: Document.objects.create(person=family.responsible,kind='CPF',number=cpf)
        if not any(valid_cpf(value) for value in family.responsible.documents.filter(kind__iexact='CPF').values_list('number',flat=True)):
            raise ValidationError('Cadastre um CPF válido antes de aprovar.')
        id_number=normalize(screening.get('identity_number',''))
        if id_number:
            id_kind=screening.get('identity_kind','')
            if not id_kind or id_kind.upper()=='CPF': raise ValidationError('Informe o tipo do documento de identificação.')
            existing=Document.objects.filter(number=id_number).first()
            if existing and existing.person_id!=family.responsible_id: raise ValidationError(f'O documento {id_kind} informado já pertence a outra pessoa.')
            if not existing: Document.objects.create(person=family.responsible,kind=id_kind,number=id_number)
        if not family.responsible.documents.exclude(kind__iexact='CPF').exists(): raise ValidationError('Cadastre o RG ou outro documento de identificação antes de aprovar.')
    if approved and (not screening.get('personal_documents_seen',family.personal_documents_seen) or not screening.get('address_proof_seen',family.address_proof_seen)):
        raise ValidationError('Confirme que os documentos pessoais e o comprovante de endereço foram conferidos antes de aprovar.')
    before={'status':family.status,'months':family.benefit.policy.get('months'),'has_children':family.benefit.policy.get('has_children'),'residents_count':family.residents_count,'children_school_frequency':family.children_school_frequency,'screening_reason':family.screening_reason,'screening_notes':family.screening_notes,'personal_documents_seen':family.personal_documents_seen,'address_proof_seen':family.address_proof_seen}
    benefit=family.benefit
    old_months=benefit.policy.get('months')
    old_children=benefit.policy.get('has_children')
    if months!=old_months or children!=old_children:
        if Delivery.objects.filter(period__benefit=benefit).exists() or benefit.extensions.exists():
            raise ValidationError('Não é possível alterar a duração após existir entrega ou prorrogação.')
        boundaries=distribution_periods(benefit.original_start,months)
        if approved:
            check_address_availability(family.address, boundaries[0][0], boundaries[-1][1], exclude_family=family.pk)
        policy=dict(benefit.policy)
        policy.update({'months':months,'has_children':bool(children),'periods':[{'start':str(a),'end':str(z)} for a,z in boundaries]})
        # Permit a narrowly scoped database exception only while this pending
        # triage is being finalized; the trigger checks status and no deliveries.
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL cestas.allow_triage_duration = '1'")
        Period.objects.filter(benefit=benefit).delete()
        benefit.policy=policy
        benefit.save(update_fields=['policy'])
        cfg=Configuration.current()
        for number,(start,end) in enumerate(boundaries,1):
            Period.objects.create(benefit=benefit,number=number,start=start,end=end,scheduled_on=start,scheduled_time=cfg.distribution_time)
    family.residents_count=screening.get('residents_count',family.residents_count)
    family.children_school_frequency=screening.get('children_school_frequency',family.children_school_frequency).strip()
    family.screening_reason=screening.get('screening_reason',family.screening_reason)
    family.screening_notes=screening.get('screening_notes',family.screening_notes).strip()
    family.personal_documents_seen=screening.get('personal_documents_seen',family.personal_documents_seen)
    family.address_proof_seen=screening.get('address_proof_seen',family.address_proof_seen)
    family.status='approved' if approved else 'denied';family.decision_reason=reason.strip();family.decided_by=user;family.decided_at=timezone.now()
    family.save(update_fields=['status','residents_count','children_school_frequency','screening_reason','screening_notes','personal_documents_seen','address_proof_seen','decision_reason','decided_by','decided_at'])
    audit(user,'Aprovar triagem' if approved else 'Não aprovar triagem',family.pk,reason.strip(),before,{'status':family.status,'months':months,'has_children':bool(children),'residents_count':family.residents_count,'children_school_frequency':family.children_school_frequency,'screening_reason':family.screening_reason,'screening_notes':family.screening_notes,'personal_documents_seen':family.personal_documents_seen,'address_proof_seen':family.address_proof_seen})

@transaction.atomic
def authorize_extension(user,family,*,months,reason='Prorrogação confirmada no sistema'):
    admin(user)
    if family.status!='approved': raise ValidationError('Somente atendimentos aprovados podem receber prorrogação.')
    if months not in range(1,4): raise ValidationError('Defina de 1 a 3 meses nesta autorização.')
    if not 10<=len(reason.strip())<=300: raise ValidationError('Registre o motivo excepcional (10 a 300 caracteres).')
    benefit=family.benefit;last=benefit.periods.order_by('-number').first()
    if last is None: raise ValidationError('Não há períodos para prorrogar.')
    if last.end>timezone.localdate(): raise ValidationError('A prorrogação só pode ser autorizada após o período atual terminar.')
    if last.number+months>32767: raise ValidationError('O limite técnico de períodos deste atendimento foi atingido.')
    auth=ExtensionAuthorization.objects.create(benefit=benefit,months=months,reason=reason.strip(),authorized_by=user)
    boundaries=distribution_periods(timezone.localdate(),months)
    check_address_availability(family.address,boundaries[0][0],boundaries[-1][1],exclude_family=family.pk)
    cfg=Configuration.current()
    for n,(a,z) in enumerate(boundaries,last.number+1):
        Period.objects.create(benefit=benefit,number=n,start=a,end=z,scheduled_on=a,scheduled_time=cfg.distribution_time,extension=auth)
    audit(user,'Autorizar prorrogação',family.pk,reason.strip(),{'periods':last.number},{'authorization':auth.pk,'months':months,'periods_added':months})
    return auth

@transaction.atomic
def authorize_reschedule(user,period,*,day,time,reason,supporting_document_seen=False):
    admin(user)
    if time is None: raise ValidationError('Informe o horário autorizado para a entrega.')
    if period.benefit.family.status!='approved': raise ValidationError('A triagem precisa estar aprovada.')
    if Delivery.objects.filter(period=period).exists(): raise ValidationError('A cesta deste período já foi registrada.')
    if ScheduleAuthorization.objects.filter(period=period).exists(): raise ValidationError('Este período já tem uma data excepcional autorizada.')
    if day<timezone.localdate(): raise ValidationError('A nova data deve ser hoje ou futura.')
    if not period.start<=day<period.end: raise ValidationError('A exceção precisa ocorrer dentro do período mensal desta cesta.')
    if not 10<=len(reason.strip())<=300: raise ValidationError('Registre a justificativa excepcional (10 a 300 caracteres).')
    check_address_availability(period.benefit.family.address,day,day+timedelta(days=1),exclude_family=period.benefit.family_id)
    auth=ScheduleAuthorization.objects.create(period=period,date=day,time=time,reason=reason.strip(),authorized_by=user,supporting_document_seen=supporting_document_seen)
    audit(user,'Autorizar nova data de entrega',period.benefit.family_id,reason.strip(),{'date':str(period.scheduled_on),'time':str(period.scheduled_time)},{'authorization':auth.pk,'date':str(day),'time':str(time),'supporting_document_seen':supporting_document_seen})
    return auth
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
    if not any(valid_cpf(number) for number in responsible.documents.filter(kind__iexact='CPF').values_list('number',flat=True)): raise ValidationError('O responsável precisa ter CPF válido cadastrado.')
    if responsible.represented_families.exclude(pk=family.pk).exists(): raise ValidationError('Essa pessoa já é responsável por outra família. Solicite análise administrativa dos vínculos antes de alterar.')
    existing_periods=list(family.benefit.periods.all())
    check_address_availability(address, existing_periods[0].start, existing_periods[-1].end, exclude_family=family.pk)
    before={'phone':family.phone,'address':family.address,'responsible':family.responsible_id}
    family.phone=phone.strip(); family.address=address.strip(); family.responsible=responsible
    family.save(update_fields=['phone','address','responsible'])
    audit(user,'Alterar família',family.pk,reason,before,{'phone':family.phone,'address':family.address,'responsible':responsible.pk})
def eligibility(family,day=None):
    day=day or timezone.localdate()
    if family.status!='approved': return None,'Atendimento aguardando decisão da coordenação.' if family.status=='pending' else 'Atendimento não aprovado.'
    authorized=Period.objects.filter(benefit__family=family,schedule_authorization__date=day).select_related('schedule_authorization').first()
    if authorized:
        if Delivery.objects.filter(period=authorized).exists(): return None,f"Retirada do período {authorized.number} já registrada."
        return authorized,f'Entrega excepcional autorizada para {day:%d/%m/%Y}.'
    p=family.benefit.periods.filter(scheduled_on=day).first()
    if not p:
        p=family.benefit.periods.filter(start__lte=day,end__gt=day,benefit__mode__in=['calendar','anniversary']).first()
    if not p: return None,'Benefício encerrado.' if day>=family.benefit.periods.last().end else 'Atendimento ainda não começou.'
    authorization=ScheduleAuthorization.objects.filter(period=p).first()
    if authorization and authorization.date!=day:
        return None,f'Entrega reagendada para {authorization.date:%d/%m/%Y}.'
    total=family.benefit.periods.count()
    if Delivery.objects.filter(period=p).exists(): return None,f"Retirada do período {p.number}/{total} já registrada."
    return p,f"Pode retirar • período {p.number}/{total}"
@transaction.atomic
def deliver(user,family,recipient,*,day=None,historical=False,note='',period=None):
    operator(user)
    today=timezone.localdate()
    if historical:
        admin(user)
        if day is None or day >= today: raise ValidationError('O registro histórico exige uma data anterior a hoje.')
    p_next=Period.objects.filter(benefit__family=family,schedule_authorization__date=today).select_related('schedule_authorization').first()
    if not p_next: p_next=family.benefit.periods.filter(scheduled_on=today).first()
    day=day or today
    if day>today: raise ValidationError('Não é permitido registrar entrega futura.')
    if historical and len(note.strip())<5: raise ValidationError('Informe a fonte ou motivo do registro histórico.')
    if not family.memberships.filter(person=recipient,ended_at__isnull=True).exists(): raise ValidationError('Quem retirou deve ser integrante da família.')
    if period is not None:
        if family.status!='approved' or period.benefit.family_id!=family.pk: raise ValidationError('Entrega não pertence a um atendimento aprovado.')
        if day < family.benefit.original_start: raise ValidationError('A entrega não pode anteceder o início do atendimento.')
        p=period
        message='Entrega registrada.'
        if Delivery.objects.filter(period=p).exists(): p=None;message='Essa retirada já foi registrada.'
    elif historical and family.status=='approved':
        p=family.benefit.periods.filter(start__lte=day,end__gt=day).first()
        message='Entrega histórica.'
        if p and Delivery.objects.filter(period=p).exists(): p=None;message='Essa retirada já foi registrada.'
    else:
        p,message=eligibility(family,day)
    if not p: raise ValidationError(message)
    try:
        with transaction.atomic():
            d=Delivery.objects.create(period=p,recipient=recipient,delivered_on=day,recorded_by=user,historical=historical,note=note.strip())
    except IntegrityError:
        raise ValidationError('Essa retirada já foi registrada. Nenhuma segunda cesta foi lançada.')
    audit(user,'Entrega histórica' if historical else 'Entrega',family.pk,note or 'Retirada confirmada',after={'delivery':d.pk,'period':p.number,'recipient':recipient.pk,'date':str(day)})
    return d
