from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from datetime import date

User = get_user_model()


class Perfil(models.Model):
    """Modelo unificado para todos los perfiles de usuario"""
    TIPOS_PERFIL = [
        ('EMPLEADO', 'Empleado'),
        ('JEFE_AREA', 'Jefe de Área'), 
        ('RH', 'Recursos Humanos'),
        ('ADMIN', 'Administrador'),
    ]
    
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Usuario")
    tipo_perfil = models.CharField(max_length=20, choices=TIPOS_PERFIL, verbose_name="Tipo de Perfil")
    departamento = models.ForeignKey('Departamento', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Departamento")
    fecha_contratacion = models.DateField(verbose_name="Fecha de Contratación")
    numero_empleado = models.CharField(max_length=20, unique=True, verbose_name="Número de Empleado")
    puesto = models.CharField(max_length=100, verbose_name="Puesto")
    salario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Salario")
    supervisor = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Supervisor")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    
    # Información personal adicional
    telefono = models.CharField(max_length=15, blank=True, verbose_name="Teléfono")
    direccion = models.TextField(blank=True, verbose_name="Dirección")
    fecha_nacimiento = models.DateField(null=True, blank=True, verbose_name="Fecha de Nacimiento")
    
    # Información de vacaciones
    dias_vacaciones_anuales = models.PositiveIntegerField(default=20, verbose_name="Días de Vacaciones Anuales")
    dias_vacaciones_usados = models.PositiveIntegerField(default=0, verbose_name="Días de Vacaciones Usados")
    
    # Auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfiles"
        ordering = ['usuario__last_name', 'usuario__first_name']
    
    def __str__(self):
        return f"{self.usuario.get_full_name()} - {self.get_tipo_perfil_display()}"
    
    @property
    def nombre_completo(self):
        return self.usuario.get_full_name() or self.usuario.username
    
    @property
    def dias_vacaciones_disponibles(self):
        return self.dias_vacaciones_anuales - self.dias_vacaciones_usados
    
    @property
    def antiguedad_anos(self):
        if not self.fecha_contratacion:
            return 0
        today = date.today()
        return today.year - self.fecha_contratacion.year - ((today.month, today.day) < (self.fecha_contratacion.month, self.fecha_contratacion.day))
    
    def es_jefe_area(self):
        return self.tipo_perfil == 'JEFE_AREA'
    
    def es_rh(self):
        return self.tipo_perfil == 'RH'
    
    def es_admin(self):
        return self.tipo_perfil == 'ADMIN'
    
    def es_empleado(self):
        return self.tipo_perfil == 'EMPLEADO'


class Departamento(models.Model):
    """Departamentos de la empresa"""
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    jefe = models.ForeignKey(Perfil, on_delete=models.SET_NULL, null=True, blank=True, 
                            related_name='departamento_dirigido', verbose_name="Jefe de Departamento")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    
    class Meta:
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre
    
    @property
    def empleados_count(self):
        return self.perfil_set.filter(activo=True).count()


class SolicitudVacaciones(models.Model):
    """Solicitudes de vacaciones con flujo de aprobación"""
    ESTADOS = [
        ('PENDIENTE_JEFE', 'Pendiente Jefe de Área'),
        ('APROBADO_JEFE', 'Aprobado por Jefe'),
        ('RECHAZADO_JEFE', 'Rechazado por Jefe'),
        ('PENDIENTE_RH', 'Pendiente RH'),
        ('APROBADO_RH', 'Aprobado por RH'),
        ('RECHAZADO_RH', 'Rechazado por RH'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    TIPOS = [
        ('NORMAL', 'Vacación Normal'),
        ('EXTRAORDINARIA', 'Vacación Extraordinaria'),
        ('EMERGENCIA', 'Vacación de Emergencia'),
    ]
    
    empleado = models.ForeignKey(Perfil, on_delete=models.CASCADE, related_name='solicitudes_vacaciones', 
                                verbose_name="Empleado")
    fecha_inicio = models.DateField(verbose_name="Fecha de Inicio")
    fecha_fin = models.DateField(verbose_name="Fecha de Fin")
    dias_solicitados = models.PositiveIntegerField(verbose_name="Días Solicitados")
    tipo = models.CharField(max_length=20, choices=TIPOS, default='NORMAL', verbose_name="Tipo")
    motivo = models.TextField(verbose_name="Motivo")
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE_JEFE', verbose_name="Estado")
    
    # Campos de aprobación
    aprobado_por_jefe = models.ForeignKey(Perfil, on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='vacaciones_aprobadas_jefe', verbose_name="Aprobado por Jefe")
    aprobado_por_rh = models.ForeignKey(Perfil, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='vacaciones_aprobadas_rh', verbose_name="Aprobado por RH")
    
    comentarios_jefe = models.TextField(blank=True, verbose_name="Comentarios del Jefe")
    comentarios_rh = models.TextField(blank=True, verbose_name="Comentarios de RH")
    
    # Auditoría
    fecha_solicitud = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Solicitud")
    fecha_aprobacion_jefe = models.DateTimeField(null=True, blank=True, verbose_name="Fecha Aprobación Jefe")
    fecha_aprobacion_rh = models.DateTimeField(null=True, blank=True, verbose_name="Fecha Aprobación RH")
    
    class Meta:
        verbose_name = "Solicitud de Vacaciones"
        verbose_name_plural = "Solicitudes de Vacaciones"
        ordering = ['-fecha_solicitud']
    
    def __str__(self):
        return f"{self.empleado.nombre_completo} - {self.fecha_inicio} a {self.fecha_fin}"
    
    def save(self, *args, **kwargs):
        # Calcular días solicitados automáticamente
        if self.fecha_inicio and self.fecha_fin:
            delta = self.fecha_fin - self.fecha_inicio
            self.dias_solicitados = delta.days + 1
        super().save(*args, **kwargs)
    
    def puede_ser_aprobada_por_jefe(self):
        """Verifica si puede ser aprobada por jefe"""
        return self.estado == 'PENDIENTE_JEFE'
    
    def puede_ser_aprobada_por_rh(self):
        """Verifica si puede ser aprobada por RH"""
        return self.estado == 'PENDIENTE_RH'
    
    def aprobar_por_jefe(self, jefe, comentario=""):
        """Aprobar solicitud por jefe de área"""
        if not self.puede_ser_aprobada_por_jefe():
            return False
        
        self.estado = 'APROBADO_JEFE'
        self.aprobado_por_jefe = jefe
        self.comentarios_jefe = comentario
        self.fecha_aprobacion_jefe = models.DateTimeField(auto_now=True)
        
        # Si es empleado normal, va directo a RH
        if self.tipo == 'NORMAL':
            self.estado = 'PENDIENTE_RH'
        
        self.save()
        return True
    
    def rechazar_por_jefe(self, jefe, comentario=""):
        """Rechazar solicitud por jefe de área"""
        if not self.puede_ser_aprobada_por_jefe():
            return False
        
        self.estado = 'RECHAZADO_JEFE'
        self.aprobado_por_jefe = jefe
        self.comentarios_jefe = comentario
        self.fecha_aprobacion_jefe = models.DateTimeField(auto_now=True)
        self.save()
        return True
    
    def aprobar_por_rh(self, rh_user, comentario=""):
        """Aprobar solicitud por RH"""
        if not self.puede_ser_aprobada_por_rh():
            return False
        
        self.estado = 'APROBADO_RH'
        self.aprobado_por_rh = rh_user
        self.comentarios_rh = comentario
        self.fecha_aprobacion_rh = models.DateTimeField(auto_now=True)
        
        # Actualizar días usados del empleado
        self.empleado.dias_vacaciones_usados += self.dias_solicitados
        self.empleado.save()
        
        self.save()
        return True
    
    def rechazar_por_rh(self, rh_user, comentario=""):
        """Rechazar solicitud por RH"""
        if not self.puede_ser_aprobada_por_rh():
            return False
        
        self.estado = 'RECHAZADO_RH'
        self.aprobado_por_rh = rh_user
        self.comentarios_rh = comentario
        self.fecha_aprobacion_rh = models.DateTimeField(auto_now=True)
        self.save()
        return True


class ConfiguracionSistema(models.Model):
    """Configuraciones generales del sistema"""
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    valor = models.TextField(verbose_name="Valor")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    
    class Meta:
        verbose_name = "Configuración del Sistema"
        verbose_name_plural = "Configuraciones del Sistema"
    
    def __str__(self):
        return f"{self.nombre}: {self.valor}"


# Señales para mantener sincronización con User model
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """Crear perfil automáticamente cuando se crea un usuario"""
    if created:
        # Solo crear perfil si no existe
        if not hasattr(instance, 'perfil'):
            Perfil.objects.create(
                usuario=instance,
                tipo_perfil='EMPLEADO',  # Default
                fecha_contratacion=date.today(),
                numero_empleado=f"EMP{instance.id:04d}",
                puesto="Por definir",
                salario=0.00  # Valor por defecto
            )
