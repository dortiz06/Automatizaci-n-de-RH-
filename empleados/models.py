from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from datetime import date, timedelta

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
    dias_vacaciones_extraordinarios = models.PositiveIntegerField(default=0, verbose_name="Días de Vacaciones Extraordinarios Usados")
    dias_vacaciones_acumulados = models.PositiveIntegerField(default=0, verbose_name="Días de Vacaciones Acumulados del Año Anterior")
    ultimo_reset_vacaciones = models.DateField(null=True, blank=True, verbose_name="Último Reset de Vacaciones")
    
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
    def dias_vacaciones_segun_antiguedad(self):
        """Calcula días de vacaciones según tabla de antigüedad"""
        if not self.fecha_contratacion:
            return 0  # Sin fecha de contratación
        
        anos = self.antiguedad_anos
        
        if anos < 1:
            # Cálculo proporcional para empleados con menos de 1 año
            # 12 días del primer año / 12 meses = 1 día por mes
            dias_trabajados = (date.today() - self.fecha_contratacion).days
            meses_trabajados = dias_trabajados / 30.44  # promedio días por mes
            dias_acumulados = (12 / 12) * meses_trabajados
            return round(dias_acumulados, 2)
        elif anos == 1:
            return 12
        elif anos == 2:
            return 14
        elif anos == 3:
            return 16
        elif anos == 4:
            return 18
        elif anos == 5:
            return 20
        elif 6 <= anos <= 10:
            return 22
        elif 11 <= anos <= 15:
            return 24
        elif 16 <= anos <= 20:
            return 26
        elif 21 <= anos <= 25:
            return 28
        elif 26 <= anos <= 30:
            return 30
        elif anos >= 31:
            return 32
        else:
            return 12  # default


    @property
    def dias_vacaciones_disponibles(self):
        # Actualizar automáticamente los días anuales según antigüedad
        dias_anuales_calculados = int(self.dias_vacaciones_segun_antiguedad)
        if self.dias_vacaciones_anuales != dias_anuales_calculados:
            self.dias_vacaciones_anuales = dias_anuales_calculados
            self.save(update_fields=['dias_vacaciones_anuales'])
        
        # Incluir días acumulados del año anterior
        return (self.dias_vacaciones_anuales + self.dias_vacaciones_acumulados) - self.dias_vacaciones_usados
    
    @property
    def dias_vacaciones_extraordinarios_disponibles(self):
        """Días extraordinarios disponibles (para empleados con menos de 1 año)"""
        if self.antiguedad_anos >= 1:
            return 0
        # Los empleados nuevos pueden tener hasta 5 días extraordinarios
        return max(0, 5 - self.dias_vacaciones_extraordinarios)
    
    @property
    def antiguedad_anos(self):
        if not self.fecha_contratacion:
            return 0
        today = date.today()
        # Calcular años completos trabajados
        years = today.year - self.fecha_contratacion.year
        if today.month < self.fecha_contratacion.month or (today.month == self.fecha_contratacion.month and today.day < self.fecha_contratacion.day):
            years -= 1
        return max(0, years)
    
    def es_jefe_area(self):
        return self.tipo_perfil == 'JEFE_AREA'
    
    def es_rh(self):
        return self.tipo_perfil == 'RH'
    
    def es_admin(self):
        return self.tipo_perfil == 'ADMIN'
    
    def es_empleado(self):
        return self.tipo_perfil == 'EMPLEADO'
    
    def actualizar_dias_vacaciones(self):
        """Actualiza los días de vacaciones según antigüedad"""
        self.dias_vacaciones_anuales = int(self.dias_vacaciones_segun_antiguedad)
        self.save(update_fields=['dias_vacaciones_anuales'])
    
    def calcular_acumulacion_mensual(self):
        """Calcula cuántos días acumula por mes según su antigüedad"""
        if self.antiguedad_anos < 1:
            return 0  # Los empleados nuevos no acumulan mensualmente
        
        dias_anuales = self.dias_vacaciones_segun_antiguedad
        return round(dias_anuales / 12, 4)  # Días por mes con 4 decimales
    
    def calcular_dias_acumulados_hasta_hoy(self):
        """Calcula cuántos días ha acumulado hasta el día de hoy en el año actual"""
        from datetime import date
        
        if not self.fecha_contratacion:
            return 0
        
        # Para empleados con menos de 1 año, usar el cálculo proporcional
        if self.antiguedad_anos < 1:
            return self.dias_vacaciones_segun_antiguedad
        
        # Para empleados con 1+ años, calcular proporcional al año
        hoy = date.today()
        
        # Calcular cuántos meses del año han pasado
        # Si estamos en octubre y el último reset fue en enero, han pasado ~10 meses
        if self.ultimo_reset_vacaciones:
            inicio_periodo = self.ultimo_reset_vacaciones
        else:
            # Si no hay reset, usar inicio de año o aniversario
            inicio_periodo = date(hoy.year, 1, 1)
        
        # Calcular meses transcurridos desde el inicio del período
        meses_transcurridos = (hoy.year - inicio_periodo.year) * 12 + (hoy.month - inicio_periodo.month)
        
        # Si ya pasó la fecha del mes, contar ese mes completo
        if hoy.day >= inicio_periodo.day:
            meses_transcurridos += 1
        
        # Calcular días acumulados proporcionalmente
        dias_anuales = self.dias_vacaciones_segun_antiguedad
        dias_por_mes = dias_anuales / 12
        dias_acumulados_periodo = dias_por_mes * meses_transcurridos
        
        return round(dias_acumulados_periodo, 2)
    
    def procesar_acumulacion_mensual(self):
        """Procesa la acumulación mensual de vacaciones"""
        from datetime import date
        
        if self.antiguedad_anos < 1:
            return False  # Los empleados nuevos no acumulan mensualmente
        
        # Calcular días a acumular este mes
        dias_por_mes = self.calcular_acumulacion_mensual()
        
        # Agregar días acumulados
        self.dias_vacaciones_acumulados += dias_por_mes
        
        self.save(update_fields=['dias_vacaciones_acumulados'])
        return True
    
    def procesar_acumulacion_anual(self):
        """Procesa la acumulación de vacaciones al inicio del año"""
        from datetime import date
        
        # Verificar si ya se procesó este año
        if self.ultimo_reset_vacaciones and self.ultimo_reset_vacaciones.year == date.today().year:
            return False
        
        # Calcular días no usados del año anterior
        dias_no_usados = max(0, self.dias_vacaciones_anuales - self.dias_vacaciones_usados)
        
        # Acumular TODOS los días no usados (sin límite)
        dias_a_acumular = dias_no_usados
        
        # Actualizar días anuales según nueva antigüedad ANTES de resetear
        nuevos_dias_anuales = int(self.dias_vacaciones_segun_antiguedad)
        
        # Resetear contadores del año
        self.dias_vacaciones_usados = 0
        self.ultimo_reset_vacaciones = date.today()
        self.dias_vacaciones_anuales = nuevos_dias_anuales
        
        # Acumular días no usados del año anterior
        if dias_a_acumular > 0:
            self.dias_vacaciones_acumulados = dias_a_acumular
        
        self.save(update_fields=[
            'dias_vacaciones_acumulados', 
            'dias_vacaciones_usados', 
            'ultimo_reset_vacaciones',
            'dias_vacaciones_anuales'
        ])
        
        return True


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
    
    @staticmethod
    def calcular_dias_laborables(fecha_inicio, fecha_fin):
        """Calcula días laborables excluyendo domingos"""
        if not fecha_inicio or not fecha_fin:
            return 0
        
        dias_totales = 0
        fecha_actual = fecha_inicio
        
        while fecha_actual <= fecha_fin:
            # weekday() retorna 0=Lunes, 6=Domingo
            if fecha_actual.weekday() != 6:  # 6 = Domingo
                dias_totales += 1
            fecha_actual += timedelta(days=1)
        
        return dias_totales
    
    def save(self, *args, **kwargs):
        # Calcular días solicitados automáticamente (excluyendo domingos)
        if self.fecha_inicio and self.fecha_fin:
            self.dias_solicitados = self.calcular_dias_laborables(self.fecha_inicio, self.fecha_fin)
        super().save(*args, **kwargs)
    
    def puede_ser_aprobada_por_jefe(self):
        """Verifica si puede ser aprobada por jefe"""
        return self.estado == 'PENDIENTE_JEFE'
    
    def puede_ser_aprobada_por_rh(self):
        """Verifica si puede ser aprobada por RH"""
        return self.estado == 'PENDIENTE_RH'
    
    def aprobar_por_jefe(self, jefe, comentario=""):
        """Aprobar solicitud por jefe de área"""
        from django.utils import timezone
        
        if not self.puede_ser_aprobada_por_jefe():
            return False
        
        self.estado = 'APROBADO_JEFE'
        self.aprobado_por_jefe = jefe
        self.comentarios_jefe = comentario
        self.fecha_aprobacion_jefe = timezone.now()
        
        # Si es empleado normal, va directo a RH
        if self.tipo == 'NORMAL':
            self.estado = 'PENDIENTE_RH'
        
        self.save()
        return True
    
    def rechazar_por_jefe(self, jefe, comentario=""):
        """Rechazar solicitud por jefe de área"""
        from django.utils import timezone
        
        if not self.puede_ser_aprobada_por_jefe():
            return False
        
        self.estado = 'RECHAZADO_JEFE'
        self.aprobado_por_jefe = jefe
        self.comentarios_jefe = comentario
        self.fecha_aprobacion_jefe = timezone.now()
        self.save()
        return True
    
    def aprobar_por_rh(self, rh_user, comentario=""):
        """Aprobar solicitud por RH"""
        from django.utils import timezone
        
        if not self.puede_ser_aprobada_por_rh():
            return False
        
        self.estado = 'APROBADO_RH'
        self.aprobado_por_rh = rh_user
        self.comentarios_rh = comentario
        self.fecha_aprobacion_rh = timezone.now()
        
        # Actualizar días usados del empleado
        self.empleado.dias_vacaciones_usados += self.dias_solicitados
        self.empleado.save()
        
        self.save()
        return True
    
    def rechazar_por_rh(self, rh_user, comentario=""):
        """Rechazar solicitud por RH"""
        from django.utils import timezone
        
        if not self.puede_ser_aprobada_por_rh():
            return False
        
        self.estado = 'RECHAZADO_RH'
        self.aprobado_por_rh = rh_user
        self.comentarios_rh = comentario
        self.fecha_aprobacion_rh = timezone.now()
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
