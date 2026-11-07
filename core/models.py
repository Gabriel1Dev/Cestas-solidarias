import uuid
from django.conf import settings
from django.db import models
from django.db.models import Q
class Person(models.Model):
    name=models.CharField('Nome completo',max_length=160)
    birth_date=models.DateField('Data de nascimento')
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name
class Document(models.Model):
    person=models.ForeignKey(Person,on_delete=models.PROTECT,related_name='documents')
    kind=models.CharField(max_length=30)
    number=models.CharField(max_length=80,unique=True)
class Family(models.Model):
    identity=models.UUIDField(default=uuid.uuid4,unique=True,editable=False)
    responsible=models.ForeignKey(Person,on_delete=models.PROTECT,related_name='represented_families')
    phone=models.CharField(max_length=40,blank=True)
    address=models.CharField(max_length=240)
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self): return f'F{self.pk:05d} · {self.responsible.name}'
class Membership(models.Model):
    family=models.ForeignKey(Family,on_delete=models.PROTECT,related_name='memberships')
    person=models.ForeignKey(Person,on_delete=models.PROTECT,related_name='memberships')
    relationship=models.CharField(max_length=60)
    joined_at=models.DateTimeField(auto_now_add=True)
    ended_at=models.DateTimeField(null=True,blank=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['family','person'],name='unique_member')]
class Benefit(models.Model):
    family=models.OneToOneField(Family,on_delete=models.PROTECT,related_name='benefit')
    original_start=models.DateField()
    mode=models.CharField(max_length=12,choices=[('calendar','Mês do calendário'),('anniversary','A partir da data de início')])
    policy=models.JSONField()
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    created_at=models.DateTimeField(auto_now_add=True)
class Period(models.Model):
    benefit=models.ForeignKey(Benefit,on_delete=models.PROTECT,related_name='periods')
    number=models.PositiveSmallIntegerField()
    start=models.DateField()
    end=models.DateField(help_text='Limite exclusivo')
    class Meta:
        ordering=['number']
        constraints=[models.UniqueConstraint(fields=['benefit','number'],name='one_period_number'),models.CheckConstraint(condition=Q(number__gte=1,number__lte=6),name='six_periods_only'),models.CheckConstraint(condition=Q(end__gt=models.F('start')),name='positive_period')]
class Delivery(models.Model):
    period=models.OneToOneField(Period,on_delete=models.PROTECT,related_name='delivery')
    recipient=models.ForeignKey(Person,on_delete=models.PROTECT)
    delivered_on=models.DateField()
    recorded_at=models.DateTimeField(auto_now_add=True)
    recorded_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    historical=models.BooleanField(default=False)
    note=models.CharField(max_length=300,blank=True)
class Audit(models.Model):
    at=models.DateTimeField(auto_now_add=True)
    actor=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    action=models.CharField(max_length=80)
    target=models.CharField(max_length=120)
    reason=models.CharField(max_length=300)
    before=models.JSONField(default=dict)
    after=models.JSONField(default=dict)
    class Meta: ordering=['-at','-id']
class Configuration(models.Model):
    id=models.PositiveSmallIntegerField(primary_key=True,default=1,editable=False)
    institute=models.CharField('Nome do instituto',max_length=120,default='Instituto • Cestas Solidárias')
    document_types=models.CharField('Tipos de documento (separados por vírgula)',max_length=200,default='CPF,RG,Outro')
    dependent_documents=models.BooleanField('Exigir documentos dos dependentes',default=False)
    phone_required=models.BooleanField('Exigir telefone',default=False)
    period_mode=models.CharField('Contagem dos novos benefícios',max_length=12,choices=Benefit._meta.get_field('mode').choices,default='calendar')
    backup_destination=models.CharField('Diretório de backup principal',max_length=400,blank=True)
    independent_destination=models.CharField('Diretório em dispositivo independente',max_length=400,blank=True)
    backup_interval_hours=models.PositiveIntegerField('Intervalo desejado (horas)',default=24)
    backup_keep=models.PositiveIntegerField('Versões a conservar por destino',default=30)
    @classmethod
    def current(cls): return cls.objects.get_or_create(pk=1)[0]
class BackupRun(models.Model):
    at=models.DateTimeField(auto_now_add=True)
    success=models.BooleanField()
    detail=models.TextField()
    class Meta: ordering=['-at']
class RuntimeState(models.Model):
    id=models.PositiveSmallIntegerField(primary_key=True,default=1,editable=False)
    writes_paused=models.BooleanField(default=False)
class BackupConfirmation(models.Model):
    at=models.DateTimeField(auto_now_add=True)
    location=models.CharField(max_length=300)
    sha256=models.CharField(max_length=64)
class LoginAttempt(models.Model):
    fingerprint=models.CharField(max_length=64,unique=True)
    window_start=models.DateTimeField()
    failures=models.PositiveSmallIntegerField(default=0)
