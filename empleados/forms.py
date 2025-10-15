from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from .models import Perfil, Departamento, SolicitudVacaciones


class UsuarioConPerfilForm(UserCreationForm):
    """Formulario para crear usuario con perfil"""
    TIPOS_PERFIL = [
        ('EMPLEADO', 'Empleado'),
        ('JEFE_AREA', 'Jefe de Área'),
        ('RH', 'Recursos Humanos'),
        ('ADMIN', 'Administrador'),
    ]
    
    # Campos de usuario
    first_name = forms.CharField(max_length=30, label='Nombre', required=True)
    last_name = forms.CharField(max_length=30, label='Apellidos', required=True)
    email = forms.EmailField(label='Correo electrónico', required=True)
    
    # Campos de perfil
    tipo_perfil = forms.ChoiceField(choices=TIPOS_PERFIL, label='Tipo de Perfil')
    departamento = forms.ModelChoiceField(
        queryset=Departamento.objects.filter(activo=True),
        label='Departamento',
        required=False
    )
    fecha_contratacion = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Fecha de Contratación',
        initial=timezone.now().date()
    )
    numero_empleado = forms.CharField(max_length=20, label='Número de Empleado')
    puesto = forms.CharField(max_length=100, label='Puesto')
    salario = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        label='Salario',
        help_text='Salario mensual'
    )
    supervisor = forms.ModelChoiceField(
        queryset=Perfil.objects.filter(activo=True, tipo_perfil__in=['JEFE_AREA', 'ADMIN']),
        label='Supervisor',
        required=False
    )
    
    # Información personal adicional
    telefono = forms.CharField(max_length=15, label='Teléfono', required=False)
    direccion = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}), 
        label='Dirección', 
        required=False
    )
    fecha_nacimiento = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Fecha de Nacimiento',
        required=False
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer campos más amigables
        self.fields['username'].help_text = 'Nombre de usuario único para iniciar sesión'
        self.fields['password1'].help_text = 'Mínimo 8 caracteres'
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Este nombre de usuario ya existe.')
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Este correo electrónico ya está registrado.')
        return email
    
    def clean_numero_empleado(self):
        numero_empleado = self.cleaned_data.get('numero_empleado')
        if Perfil.objects.filter(numero_empleado=numero_empleado).exists():
            raise forms.ValidationError('Este número de empleado ya existe.')
        return numero_empleado
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            
            # Crear perfil
            perfil = Perfil.objects.create(
                usuario=user,
                tipo_perfil=self.cleaned_data['tipo_perfil'],
                departamento=self.cleaned_data.get('departamento'),
                fecha_contratacion=self.cleaned_data['fecha_contratacion'],
                numero_empleado=self.cleaned_data['numero_empleado'],
                puesto=self.cleaned_data['puesto'],
                salario=self.cleaned_data['salario'],
                supervisor=self.cleaned_data.get('supervisor'),
                telefono=self.cleaned_data.get('telefono', ''),
                direccion=self.cleaned_data.get('direccion', ''),
                fecha_nacimiento=self.cleaned_data.get('fecha_nacimiento')
            )
        
        return user


class SolicitudVacacionesForm(forms.ModelForm):
    """Formulario para solicitar vacaciones"""
    
    class Meta:
        model = SolicitudVacaciones
        fields = ['fecha_inicio', 'fecha_fin', 'tipo', 'motivo']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date'}),
            'motivo': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe el motivo de tu solicitud de vacaciones...'}),
        }
        labels = {
            'fecha_inicio': 'Fecha de Inicio',
            'fecha_fin': 'Fecha de Fin',
            'tipo': 'Tipo de Vacación',
            'motivo': 'Motivo',
        }
    
    def __init__(self, *args, **kwargs):
        self.empleado = kwargs.pop('empleado', None)
        super().__init__(*args, **kwargs)
        
        # Mostrar información de elegibilidad
        if self.empleado:
            antiguedad = self.empleado.antiguedad_anos
            dias_calculados = self.empleado.dias_vacaciones_segun_antiguedad
            dias_disponibles = self.empleado.dias_vacaciones_disponibles
            
            if antiguedad < 1:
                self.fields['tipo'].choices = [
                    ('EXTRAORDINARIA', 'Vacación Extraordinaria'),
                    ('EMERGENCIA', 'Vacación de Emergencia'),
                ]
                meses_trabajados = ((timezone.now().date() - self.empleado.fecha_contratacion).days) / 30.44
                self.fields['tipo'].help_text = (
                    f'Tienes {antiguedad} año(s) de antigüedad ({meses_trabajados:.1f} meses). '
                    f'Días acumulados: {dias_calculados:.2f}. '
                    f'Días disponibles: {dias_disponibles}'
                )
            else:
                self.fields['tipo'].help_text = f'Antigüedad: {antiguedad} años. Días disponibles: {dias_disponibles}'
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        
        if fecha_inicio and fecha_fin:
            # Validar que la fecha fin sea posterior a la fecha inicio
            if fecha_fin < fecha_inicio:
                raise forms.ValidationError('La fecha de fin debe ser posterior a la fecha de inicio.')
            
            # Validar que no sea en el pasado
            hoy = timezone.now().date()
            if fecha_inicio < hoy:
                raise forms.ValidationError('No puedes solicitar vacaciones para fechas pasadas.')
            
            # Calcular días solicitados
            dias_solicitados = (fecha_fin - fecha_inicio).days + 1
            
            # Validar días disponibles
            if self.empleado and dias_solicitados > self.empleado.dias_vacaciones_disponibles:
                raise forms.ValidationError(
                    f'No tienes suficientes días de vacaciones disponibles. '
                    f'Disponibles: {self.empleado.dias_vacaciones_disponibles} días'
                )
        
        return cleaned_data


class AprobacionJefeForm(forms.Form):
    """Formulario para aprobación por jefe de área"""
    accion = forms.ChoiceField(
        choices=[
            ('aprobar', 'Aprobar Solicitud'),
            ('rechazar', 'Rechazar Solicitud'),
        ],
        widget=forms.RadioSelect,
        label='Acción'
    )
    comentario = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Comentarios sobre la decisión...'}),
        label='Comentarios',
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        self.solicitud = kwargs.pop('solicitud', None)
        super().__init__(*args, **kwargs)


class AprobacionRHForm(forms.Form):
    """Formulario para aprobación por RH"""
    accion = forms.ChoiceField(
        choices=[
            ('aprobar', 'Aprobar Solicitud'),
            ('rechazar', 'Rechazar Solicitud'),
        ],
        widget=forms.RadioSelect,
        label='Acción'
    )
    comentario = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Comentarios sobre la decisión...'}),
        label='Comentarios',
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        self.solicitud = kwargs.pop('solicitud', None)
        super().__init__(*args, **kwargs)


class EditarPerfilForm(forms.ModelForm):
    """Formulario para editar perfil de usuario"""
    
    class Meta:
        model = Perfil
        fields = ['telefono', 'direccion', 'fecha_nacimiento']
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
            'direccion': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'telefono': 'Teléfono',
            'direccion': 'Dirección',
            'fecha_nacimiento': 'Fecha de Nacimiento',
        }


class ConfigurarDepartamentoForm(forms.ModelForm):
    """Formulario para configurar departamentos"""
    
    class Meta:
        model = Departamento
        fields = ['nombre', 'descripcion', 'jefe']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'nombre': 'Nombre del Departamento',
            'descripcion': 'Descripción',
            'jefe': 'Jefe de Departamento',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo mostrar jefes de área como opciones para jefe de departamento
        self.fields['jefe'].queryset = Perfil.objects.filter(
            activo=True, 
            tipo_perfil__in=['JEFE_AREA', 'ADMIN']
        )
