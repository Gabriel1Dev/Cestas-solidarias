from django import forms
from .models import Configuration
class PersonFields(forms.Form):
    name=forms.CharField(label='Nome completo',max_length=160,required=False)
    birth=forms.DateField(label='Nascimento',widget=forms.DateInput(format='%Y-%m-%d',attrs={'type':'date'}),required=False)
    kind=forms.ChoiceField(label='Tipo de documento',required=False)
    number=forms.CharField(label='Número do documento',max_length=80,required=False)
    person_id=forms.IntegerField(label='Número interno da pessoa já cadastrada',required=False,min_value=1,help_text='Não é o CPF. Use o número Pessoa # exibido na ficha existente; deixe em branco para uma pessoa nova.')
    review_reason=forms.CharField(label='Justificativa da análise do administrador',required=False,max_length=300)
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['kind'].choices=[(s.strip(),s.strip()) for s in Configuration.current().document_types.split(',') if s.strip()]
class FamilyForm(PersonFields):
    phone=forms.CharField(label='Telefone',required=False,max_length=40)
    address=forms.CharField(label='Endereço',max_length=240)
    start=forms.DateField(label='Início original do atendimento',widget=forms.DateInput(format='%Y-%m-%d',attrs={'type':'date'}),help_text='Use a data do papel. Este cadastro não reinicia o benefício.')
class MemberForm(PersonFields):
    relationship=forms.CharField(label='Parentesco ou vínculo',max_length=60)
class EditFamilyForm(forms.Form):
    phone=forms.CharField(label='Telefone',required=False,max_length=40)
    address=forms.CharField(label='Endereço',max_length=240)
    responsible=forms.ModelChoiceField(label='Responsável',queryset=None)
    reason=forms.CharField(label='Motivo da alteração',min_length=5,max_length=300)
    def __init__(self,family,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['responsible'].queryset=family.responsible.__class__.objects.filter(memberships__family=family,memberships__ended_at__isnull=True)
class DeliveryForm(forms.Form):
    recipient=forms.ModelChoiceField(label='Quem retirou',queryset=None)
    day=forms.DateField(label='Data da entrega',widget=forms.DateInput(format='%Y-%m-%d',attrs={'type':'date'}))
    note=forms.CharField(label='Fonte / observação',required=False,max_length=300)
    def __init__(self,family,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['recipient'].queryset=family.responsible.__class__.objects.filter(memberships__family=family,memberships__ended_at__isnull=True)
class ConfigurationForm(forms.ModelForm):
    class Meta:
        model=Configuration
        exclude=['id','backup_destination','independent_destination']
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['backup_keep'].label='Dias de retenção desejados para cópias automáticas (2 a 90)'
    def clean(self):
        data=super().clean()
        if data.get('backup_keep',0)>90:self.add_error('backup_keep','O agendamento fornecido aceita no máximo 90 dias.')
        if data.get('backup_keep',0)<2: self.add_error('backup_keep','Conserve ao menos duas versões.')
        if data.get('backup_interval_hours',0)<1: self.add_error('backup_interval_hours','Mínimo de uma hora.')
        if not data.get('document_types','').strip(): self.add_error('document_types','Informe ao menos um tipo.')
        return data
class PersonEditForm(forms.Form):
    name=forms.CharField(label='Nome completo',max_length=160)
    birth_date=forms.DateField(label='Nascimento',widget=forms.DateInput(format='%Y-%m-%d',attrs={'type':'date'}))
    kind=forms.ChoiceField(label='Tipo do documento adicional',required=False)
    number=forms.CharField(label='Documento adicional (opcional)',max_length=80,required=False,help_text='Os documentos anteriores ficam preservados como identificadores. Se houver erro no documento anterior, registre o correto e explique o motivo.')
    reason=forms.CharField(label='Motivo e origem da correção',min_length=5,max_length=300)
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['kind'].choices=[(s.strip(),s.strip()) for s in Configuration.current().document_types.split(',') if s.strip()]
