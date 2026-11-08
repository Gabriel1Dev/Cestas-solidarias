"""Portable logical backups: no dependency on writable serverless filesystem."""
import hashlib,hmac,json,os
from pathlib import Path
from datetime import date,timedelta
from django.core import serializers
from django.conf import settings
from django.db import transaction,connections
from django.db.migrations.recorder import MigrationRecorder
from django.utils import timezone
from django.contrib.auth.models import User,Group
from . import models
from .locking import maintenance_lock
from .periods import periods,distribution_periods
from .services import admin,audit
FORMAT='cestas-online-v3'
MODEL_ORDER=[Group,User,models.Person,models.Document,models.Family,models.Membership,models.Benefit,models.ExtensionAuthorization,models.Period,models.ScheduleAuthorization,models.Delivery,models.Audit,models.Configuration,models.BackupRun,models.BackupConfirmation,models.RuntimeState]
def schema(using='default'):
    return [list(r) for r in MigrationRecorder.Migration.objects.using(using).order_by('app','name').values_list('app','name')]
def sha256(data):return hashlib.sha256(data).hexdigest()
def signature(payload):
    unsigned={k:v for k,v in payload.items() if k!='signature'}
    data=json.dumps(unsigned,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
    return hmac.new(settings.CESTAS_BACKUP_SIGNING_KEY.encode(),data,hashlib.sha256).hexdigest()
def create_snapshot():
    with maintenance_lock():
        models.RuntimeState.objects.get_or_create(pk=1)
        objects=[]
        for model in MODEL_ORDER:objects.extend(model.objects.order_by('pk'))
        payload={'format':FORMAT,'created_at':timezone.now().isoformat(),'schema':schema(),'objects':json.loads(serializers.serialize('json',objects,use_natural_foreign_keys=True))}
        payload['signature']=signature(payload)
        validate_payload(payload)
        return json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode('utf-8')
def validate_payload(payload,using='default'):
    if not hmac.compare_digest(str(payload.get('signature','')),signature(payload)):raise ValueError('Assinatura inválida. O arquivo foi alterado ou a chave de backup não corresponde à origem.')
    current_schema = schema(using)
    legacy_schema = [item for item in current_schema if item[1] not in {'0004_duration','0005_client_workflow','0006_extension_period_limit','0007_client_workflow_guards','0008_screening_reasons','0009_exception_document_flag','0010_delivery_actual_date','0011_triage_schedule_and_delivery_guards'}]
    old_duration_schema = [item for item in current_schema if item[1] not in {'0005_client_workflow','0006_extension_period_limit','0007_client_workflow_guards','0008_screening_reasons','0009_exception_document_flag','0010_delivery_actual_date','0011_triage_schedule_and_delivery_guards'}]
    previous_schema = [item for item in current_schema if item[1] not in {'0010_delivery_actual_date','0011_triage_schedule_and_delivery_guards'}]
    if payload.get('format') not in (FORMAT,'cestas-online-v2') or payload.get('schema') not in (current_schema, previous_schema, legacy_schema, old_duration_schema):
        raise ValueError('Formato ou migrações incompatíveis com esta versão.')
    allowed={m._meta.label_lower for m in MODEL_ORDER}
    rows={label:{} for label in allowed}
    for obj in payload.get('objects',[]):
        label=obj.get('model')
        if label not in allowed or obj.get('pk') in rows[label]:raise ValueError('Modelo desconhecido ou identificador repetido no backup.')
        rows[label][obj['pk']]=obj['fields']
    extension_rows=rows['core.extensionauthorization']
    for bid,b in rows['core.benefit'].items():
        policy=b['policy']
        months=policy.get('months')
        if months not in (1,2,3,6): raise ValueError('Duração inválida.')
        if policy.get('renewable') is not False or policy.get('missed_accumulate') is not False:raise ValueError('Política de benefício inválida.')
        all_periods=[(pk,p) for pk,p in rows['core.period'].items() if p['benefit']==bid]
        base=sorted((p['number'],p['start'],p['end']) for _,p in all_periods if not p.get('extension'))
        if policy.get('version')==3:
            expected=distribution_periods(date.fromisoformat(b['original_start']),months)
            if b['mode']!='distribution' or policy.get('mode')!='distribution':raise ValueError('Política de distribuição inválida.')
        else:
            expected=periods(date.fromisoformat(b['original_start']),b['mode'],months)
        if base!=[(i,str(a),str(z)) for i,(a,z) in enumerate(expected,1)]:raise ValueError('Benefício sem períodos originais válidos.')
        if policy.get('periods')!=[{'start':str(a),'end':str(z)} for a,z in expected]:raise ValueError('Política e períodos divergentes.')
        last_number=max(row[0] for row in base);last_end=max(date.fromisoformat(row[2]) for row in base)
        auths=sorted(((aid,a) for aid,a in extension_rows.items() if a['benefit']==bid),key=lambda pair:pair[1]['authorized_at'])
        for auth_id,auth in auths:
            if auth['months'] not in range(1,7) or len(auth['reason'].strip())<10:raise ValueError('Autorização de prorrogação inválida.')
            extension_periods=sorted((p['number'],p['start'],p['end']) for _,p in all_periods if p.get('extension')==auth_id)
            expected_extension=distribution_periods(date.fromisoformat(auth['authorized_at'][:10]),auth['months'])
            if extension_periods!=[(last_number+i,str(a),str(z)) for i,(a,z) in enumerate(expected_extension,1)]:raise ValueError('Prorrogação sem períodos autorizados válidos.')
            last_number+=auth['months'];last_end=expected_extension[-1][1]
        if b['family'] not in rows['core.family']:raise ValueError('Benefício sem família.')
    for auth_id,auth in rows['core.scheduleauthorization'].items():
        if auth['period'] not in rows['core.period'] or len(auth['reason'].strip())<10:raise ValueError('Autorização de reagendamento inválida.')
    occupied=set()
    for d in rows['core.delivery'].values():
        if d['period'] not in rows['core.period'] or d['period'] in occupied:raise ValueError('Entrega duplicada ou sem período.')
        occupied.add(d['period']);p=rows['core.period'][d['period']]
        b=rows['core.benefit'][p['benefit']]
        if d['delivered_on'] < b['original_start']:raise ValueError('Entrega anterior ao início do atendimento.')
        family=rows['core.family'][b['family']]
        if family.get('status','approved')!='approved':raise ValueError('Entrega vinculada a triagem não aprovada.')
        family_id=b['family']
        if not any(m['person']==d['recipient'] and m['family']==family_id and not m['ended_at'] for m in rows['core.membership'].values()):raise ValueError('Pessoa sem vínculo na entrega.')
    return {label:len(items) for label,items in rows.items()}
def read_backup(path,using='default'):
    raw=Path(path).read_bytes()
    payload=json.loads(raw.decode('utf-8'))
    counts=validate_payload(payload,using)
    return raw,payload,counts
def write_backup(path):
    path=Path(path).resolve()
    if not path.parent.is_dir():raise ValueError('O diretório de destino deve existir.')
    data=create_snapshot()
    with path.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    return sha256(data)
def backup_due():
    last=models.BackupConfirmation.objects.order_by('-at').first()
    return not last or timezone.now()-last.at>=timedelta(hours=models.Configuration.current().backup_interval_hours)
def record_confirmation(path,location):
    raw,_,_=read_backup(path)
    if len(location.strip())<5:raise ValueError('Informe onde a cópia foi efetivamente guardada.')
    return models.BackupConfirmation.objects.create(location=location.strip(),sha256=sha256(raw))
def load_empty_database(payload,using):
    # Restore only into a newly migrated, unused database. Production is never overwritten.
    if models.Family.objects.using(using).exists() or models.Audit.objects.using(using).exists() or User.objects.using(using).exists():raise ValueError('O destino deve ser um banco novo, sem usuários, famílias ou histórico.')
    validate_payload(payload,using)
    with transaction.atomic(using=using):
        # Older signed backups did not require a reschedule time. Preserve the
        # period's configured time, falling back to the standard distribution time.
        restore_objects=json.loads(json.dumps(payload['objects']))
        periods_by_id={str(obj['pk']):obj['fields'] for obj in restore_objects if obj.get('model')=='core.period'}
        config=next((obj['fields'] for obj in restore_objects if obj.get('model')=='core.configuration'),{})
        fallback=config.get('distribution_time') or '09:00:00'
        for obj in restore_objects:
            if obj.get('model')=='core.scheduleauthorization' and not obj['fields'].get('time'):
                period=periods_by_id.get(str(obj['fields'].get('period')),{})
                obj['fields']['time']=period.get('scheduled_time') or fallback
        for obj in serializers.deserialize('json',json.dumps(restore_objects),using=using,handle_forward_references=True):
            obj.save(using=using)
        models.RuntimeState.objects.using(using).update_or_create(pk=1,defaults={'writes_paused':True})
        connections[using].check_constraints()
        from django.core.management.color import no_style
        with connections[using].cursor() as c:
            for sql in connections[using].ops.sequence_reset_sql(no_style(),MODEL_ORDER):c.execute(sql)
    return {m._meta.label_lower:m.objects.using(using).count() for m in MODEL_ORDER}
def configure_target(url,alias='recovery'):
    from config.database import database_config
    from django.conf import settings
    from copy import deepcopy
    config=deepcopy(connections['default'].settings_dict)
    config.update(database_config(url,allow_local=settings.LOCAL_TEST))
    connections.databases[alias]=config
    connections[alias].connect()
    return alias
def stage_recovery(path,target_url,user,pre_backup,receipt):
    admin(user)
    raw,payload,counts=read_backup(path)
    families={obj['pk']:obj['fields'] for obj in payload['objects'] if obj['model']=='core.family'}
    for obj in payload['objects']:
        if obj['model']!='core.benefit':continue
        fields=obj['fields'];identity=families[fields['family']]['identity']
        existing=models.Benefit.objects.filter(family__identity=identity).first()
        if existing and (str(existing.original_start)!=fields['original_start'] or existing.mode!=fields['mode'] or existing.policy!=fields['policy']):raise ValueError('A cópia tenta alterar as regras originais de uma família existente.')
    tested=json.loads(Path(receipt).read_text(encoding='utf-8'))
    if tested.get('sha256')!=sha256(raw):raise ValueError('Ensaie o arquivo exato antes da recuperação.')
    alias=configure_target(target_url)
    # Reading a fresh target and comparing source config prevents accidental in-place recovery.
    source=connections['default'].settings_dict;target=connections[alias].settings_dict
    normalize=lambda h:h.replace('-pooler.','.')
    if (normalize(source['HOST']),source['PORT'],source['NAME'])==(normalize(target['HOST']),target['PORT'],target['NAME']):raise ValueError('Destino não pode ser o banco ativo.')
    if models.Family.objects.using(alias).exists() or User.objects.using(alias).exists():raise ValueError('Destino já possui dados. Use um banco vazio com migrações aplicadas.')
    with maintenance_lock():
        write_backup(pre_backup)
        models.RuntimeState.objects.update_or_create(pk=1,defaults={'writes_paused':True})
        audit(user,'Suspender atendimento para recuperação','recovery','Recuperação ensaiada; banco original preservado',after={'sha256':sha256(raw)})
    # State stays paused even if import fails. A separate admin command explicitly resumes it.
    result=load_empty_database(payload,alias)
    return result
