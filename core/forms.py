from django import forms
from .models import Configuration, Period

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
    has_children=forms.ChoiceField(label='Há crianças na residência?',choices=[('', 'Selecione'),('yes','Sim'),('no','Não')])
    months=forms.TypedChoiceField(label='Duração inicial solicitada',choices=[('', 'Selecione'),(1,'1 mês'),(2,'2 meses'),(3,'3 meses')],coerce=int)
    identity_kind=forms.ChoiceField(label='Tipo do documento de identificação',required=False)
    identity_number=forms.CharField(label='Número do documento de identificação (RG ou outro)',max_length=80,required=False)
    phone=forms.CharField(label='Telefone',required=False,max_length=40)
    address=forms.CharField(label='Endereço',max_length=240)
    start=forms.DateField(label='Data do primeiro atendimento',widget=forms.DateInput(format='%Y-%m-%d',attrs={'type':'date'}),help_text='O sistema agendará a primeira entrega no próximo segundo sábado.')
    residents_count=forms.IntegerField(label='Quantas pessoas moram no endereço?',min_value=1,max_value=40)
    children_school_frequency=forms.CharField(label='Frequência escolar das crianças',max_length=300,required=False,help_text='Informe a frequência, ou explique por que não se aplica.')
    screening_reason=forms.ChoiceField(label='Motivo principal da solicitação',choices=[('', 'Selecione'),('unemployment','Desemprego'),('health','Problema de saúde'),('accident','Acidente ou emergência'),('other','Outra situação de vulnerabilidade')])
    screening_notes=forms.CharField(label='Informações essenciais da triagem',widget=forms.Textarea(attrs={'rows':4}),max_length=2000,help_text='Registre apenas o necessário para a avaliação social.')
    personal_documents_seen=forms.BooleanField(label='CPF e documento de identificação conferidos',required=False)
    address_proof_seen=forms.BooleanField(label='Comprovante de endereço conferido',required=False)
    def clean(self):
        data=super().clean()
        if data.get('has_children')=='no' and data.get('months') not in (None,1): self.add_error('months','Sem crianças, o atendimento inicial é de uma cesta.')
        if data.get('has_children')=='yes' and not data.get('children_school_frequency','').strip(): self.add_error('children_school_frequency','Informe a frequência escolar ou o motivo de não se aplicar.')
        if not data.get('person_id') and not data.get('identity_number','').strip(): self.add_error('identity_number','Informe o documento de identificação além do CPF.')
        if data.get('identity_number','').strip() and (not data.get('identity_kind') or data['identity_kind'].upper()=='CPF'): self.add_error('identity_kind','Escolha RG ou outro documento de identificação.')
        return data
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['kind'].choices=[('CPF','CPF')]
        self.fields['kind'].widget=forms.HiddenInput()
        self.fields['kind'].initial='CPF'
        self.fields['kind'].label='Documento do responsável'
        self.fields['number'].label='CPF do responsável'
        valid=[s.strip() for s in Configuration.current().document_types.split(',') if s.strip() and s.strip().upper()!='CPF']
        self.fields['identity_kind'].choices=[('', 'Selecione'),*((value,value) for value in valid)]
        self.order_fields(['name','birth','kind','number','identity_kind','identity_number','phone','address','start','residents_count','has_children','months','children_school_frequency','screening_reason','screening_notes','personal_documents_seen','address_proof_seen','person_id','review_reason'])

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
    period=forms.ModelChoiceField(label='Entrega prevista',queryset=Period.objects.none())
    day=forms.DateField(label='Data real da entrega',widget=forms.DateInput(format='%Y-%m-%d',attrs={'type':'date'}))
    note=forms.CharField(label='Observação (opcional)',required=False,max_length=300)
    def __init__(self,family,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['recipient'].queryset=family.responsible.__class__.objects.filter(memberships__family=family,memberships__ended_at__isnull=True)
        self.fields['period'].queryset=family.benefit.periods.filter(delivery__isnull=True)
        def period_label(p):
            authorization=getattr(p,'schedule_authorization',None)
            planned=authorization.date if authorization else (p.scheduled_on or p.start)
            hour=authorization.time if authorization else p.scheduled_time
            return f"Entrega prevista para {planned:%d/%m/%Y}"+(f' às {hour:%H:%M}' if hour else '')
        self.fields['period'].label_from_instance=period_label

class ConfigurationForm(forms.ModelForm):
    class Meta:
        model=Configuration
        exclude=['id','backup_destination','independent_destination','period_mode']
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['backup_keep'].label='Dias de retenção desejados para cópias automáticas (2 a 90)'
    def clean(self):
        data=super().clean()
        if data.get('backup_keep',0)>90:self.add_error('backup_keep','O agendamento fornecido aceita no máximo 90 dias.')
        if data.get('backup_keep',0)<2:self.add_error('backup_keep','Conserve ao menos duas versões.')
        if data.get('backup_interval_hours',0)<1:self.add_error('backup_interval_hours','Mínimo de uma hora.')
        if not data.get('document_types','').strip():self.add_error('document_types','Informe ao menos um tipo.')
        return data

class PersonEditForm(forms.Form):
    name=forms.CharField(label='Nome completo',max_length=160)
    birth_date=forms.DateField(label='Nascimento',widget=forms.DateInput(format='%Y-%m-%d',attrs={'type':'date'}))
    kind=forms.ChoiceField(label='Tipo do documento adicional',required=False)
    number=forms.CharField(label='Documento adicional (opcional)',max_length=80,required=False,help_text='Os documentos anteriores ficam preservados como identificadores.')
    reason=forms.CharField(label='Motivo e origem da correção',min_length=5,max_length=300)
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['kind'].choices=[(s.strip(),s.strip()) for s in Configuration.current().document_types.split(',') if s.strip()]

class DecisionForm(forms.Form):
    reason=forms.CharField(label='Justificativa da coordenação',min_length=10,max_length=300,widget=forms.Textarea(attrs={'rows':4}))

class ScreeningReviewForm(forms.Form):
    residents_count=forms.IntegerField(label='Moradores',min_value=1,max_value=40)
    months=forms.TypedChoiceField(label='Duração inicial do atendimento',choices=[(i,f'{i} mês' if i==1 else f'{i} meses') for i in range(1,4)],coerce=int)
    children_school_frequency=forms.CharField(label='Escola/frequência das crianças ou justificativa',max_length=300,required=False)
    screening_reason=forms.ChoiceField(label='Motivo principal',choices=[('unemployment','Desemprego'),('health','Problema de saúde'),('accident','Acidente/emergência'),('other','Outra vulnerabilidade')])
    screening_notes=forms.CharField(label='Informações essenciais da triagem',widget=forms.Textarea(attrs={'rows':3}),max_length=2000)
    personal_documents_seen=forms.BooleanField(label='CPF e identificação conferidos',required=False)
    address_proof_seen=forms.BooleanField(label='Comprovante de endereço conferido',required=False)
    reason=forms.CharField(label='Justificativa da decisão da coordenação',min_length=10,max_length=300,widget=forms.Textarea(attrs={'rows':2}))
    has_children=forms.BooleanField(label='Há crianças no domicílio?',required=False)
    cpf_number=forms.CharField(label='CPF do responsável',max_length=80,required=False)
    identity_kind=forms.ChoiceField(label='Tipo do documento de identificação',required=False)
    identity_number=forms.CharField(label='Número do documento de identificação',max_length=80,required=False)
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        valid=[s.strip() for s in Configuration.current().document_types.split(',') if s.strip() and s.strip().upper()!='CPF']
        self.fields['identity_kind'].choices=[('', 'Selecione'),*((value,value) for value in valid)]
    def clean(self):
        data=super().clean()
        if data.get('has_children') and not data.get('children_school_frequency','').strip(): self.add_error('children_school_frequency','Informe a frequência escolar ou por que não se aplica.')
        if not data.get('has_children') and data.get('months')!=1: self.add_error('months','Sem crianças, o atendimento inicial é de uma cesta.')
        if data.get('identity_number','').strip() and not data.get('identity_kind'): self.add_error('identity_kind','Escolha o tipo do documento.')
        return data

class ExtensionForm(forms.Form):
    months=forms.TypedChoiceField(label='Por quantos meses deseja prorrogar?',choices=[(i,f'{i} mês' if i==1 else f'{i} meses') for i in range(1,4)],coerce=int)

class ScheduleAuthorizationForm(forms.Form):
    day=forms.DateField(label='Nova data autorizada',widget=forms.DateInput(format='%Y-%m-%d',attrs={'type':'date'}))
    time=forms.TimeField(label='Horário autorizado',required=True,widget=forms.TimeInput(format='%H:%M',attrs={'type':'time'}))
    supporting_document_seen=forms.BooleanField(label='Comprovante apresentado e conferido, quando solicitado',required=False)
    reason=forms.CharField(label='Justificativa excepcional da coordenação',min_length=10,max_length=300,widget=forms.Textarea(attrs={'rows':4}))
