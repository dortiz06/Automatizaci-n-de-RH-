from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Q
from .models import Perfil, Departamento, SolicitudVacaciones, ConfiguracionSistema
from datetime import date, timedelta


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    """Admin personalizado para gestión de perfiles de empleados"""
    
    list_display = [
        'numero_empleado', 'nombre_completo', 'tipo_perfil', 'departamento', 
        'fecha_contratacion', 'antiguedad_display', 'puede_vacaciones', 
        'dias_vacaciones_info', 'activo_status'
    ]
    
    list_filter = [
        'tipo_perfil', 'departamento', 'activo', 'fecha_contratacion',
        ('fecha_contratacion', admin.DateFieldListFilter),
    ]
    
    search_fields = [
        'usuario__username', 'usuario__first_name', 'usuario__last_name',
        'numero_empleado', 'puesto', 'departamento__nombre'
    ]
    
    readonly_fields = [
        'antiguedad_display', 'puede_vacaciones', 'dias_vacaciones_info',
        'fecha_creacion', 'fecha_actualizacion'
    ]
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('usuario', 'numero_empleado', 'tipo_perfil', 'activo')
        }),
        ('Información Laboral', {
            'fields': ('departamento', 'puesto', 'salario', 'supervisor')
        }),
        ('Fechas Importantes', {
            'fields': ('fecha_contratacion', 'fecha_nacimiento', 'antiguedad_display'),
            'description': 'La fecha de contratación determina los días de vacaciones según antigüedad. Puedes modificarla para hacer pruebas.'
        }),
        ('Control de Vacaciones', {
            'fields': (
                'puede_vacaciones', 
                'dias_vacaciones_anuales', 
                'dias_vacaciones_usados', 
                'dias_vacaciones_acumulados',
                'dias_vacaciones_extraordinarios',
                'ultimo_reset_vacaciones',
                'dias_vacaciones_info'
            ),
            'description': 'Los días anuales se calculan automáticamente según antigüedad. Puedes ajustar manualmente para pruebas.',
            'classes': ('collapse',)
        }),
        ('Información de Contacto', {
            'fields': ('telefono', 'direccion'),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['usuario__last_name', 'usuario__first_name']
    
    def antiguedad_display(self, obj):
        """Muestra la antigüedad de forma legible"""
        anos = obj.antiguedad_anos
        if anos == 0:
            return format_html('<span style="color: orange;">Menos de 1 año</span>')
        elif anos == 1:
            return format_html('<span style="color: green;">1 año</span>')
        else:
            return format_html('<span style="color: green;">{} años</span>', anos)
    antiguedad_display.short_description = 'Antigüedad'
    
    def puede_vacaciones(self, obj):
        """Indica si el empleado puede solicitar vacaciones"""
        if not obj.fecha_contratacion:
            return format_html('<span style="color: gray;">Sin fecha</span>')
        
        if obj.antiguedad_anos >= 1:
            return format_html('<span style="color: green;">✓ Puede solicitar</span>')
        else:
            dias_restantes = 365 - (date.today() - obj.fecha_contratacion).days
            return format_html(
                '<span style="color: orange;">✗ Falta {} días</span>', 
                dias_restantes
            )
    puede_vacaciones.short_description = 'Puede Vacaciones'
    
    def dias_vacaciones_info(self, obj):
        """Muestra información detallada de vacaciones"""
        disponibles = obj.dias_vacaciones_disponibles
        usados = obj.dias_vacaciones_usados
        total = obj.dias_vacaciones_anuales
        
        if disponibles > 0:
            color = 'green'
        elif disponibles == 0:
            color = 'orange'
        else:
            color = 'red'
            
        return format_html(
            '<span style="color: {};">{} disponibles / {} usados / {} total</span>',
            color, disponibles, usados, total
        )
    dias_vacaciones_info.short_description = 'Estado Vacaciones'
    
    def activo_status(self, obj):
        """Muestra el estado activo con colores"""
        if obj.activo:
            return format_html('<span style="color: green;">✓ Activo</span>')
        else:
            return format_html('<span style="color: red;">✗ Inactivo</span>')
    activo_status.short_description = 'Estado'
    
    def get_queryset(self, request):
        """Optimizar consultas"""
        return super().get_queryset(request).select_related(
            'usuario', 'departamento', 'supervisor'
        )
    
    actions = [
        'marcar_como_activos', 'marcar_como_inactivos', 'resetear_vacaciones',
        'simular_1_ano', 'simular_2_anos', 'simular_5_anos', 'actualizar_dias_vacaciones'
    ]
    
    def marcar_como_activos(self, request, queryset):
        """Marcar empleados seleccionados como activos"""
        updated = queryset.update(activo=True)
        self.message_user(request, f'{updated} empleados marcados como activos.')
    marcar_como_activos.short_description = "Marcar como activos"
    
    def marcar_como_inactivos(self, request, queryset):
        """Marcar empleados seleccionados como inactivos"""
        updated = queryset.update(activo=False)
        self.message_user(request, f'{updated} empleados marcados como inactivos.')
    marcar_como_inactivos.short_description = "Marcar como inactivos"
    
    def resetear_vacaciones(self, request, queryset):
        """Resetear días de vacaciones usados"""
        updated = queryset.update(dias_vacaciones_usados=0)
        self.message_user(request, f'Vacaciones reseteadas para {updated} empleados.')
    resetear_vacaciones.short_description = "Resetear vacaciones"
    
    def simular_1_ano(self, request, queryset):
        """Simular que el empleado tiene 1 año de antigüedad (para pruebas)"""
        fecha_hace_1_ano = date.today() - timedelta(days=365)
        updated = queryset.update(fecha_contratacion=fecha_hace_1_ano)
        for perfil in queryset:
            perfil.actualizar_dias_vacaciones()
        self.message_user(request, f'{updated} empleados ajustados a 1 año de antigüedad (12 días).')
    simular_1_ano.short_description = "🧪 Simular 1 año de antigüedad"
    
    def simular_2_anos(self, request, queryset):
        """Simular que el empleado tiene 2 años de antigüedad (para pruebas)"""
        fecha_hace_2_anos = date.today() - timedelta(days=730)
        updated = queryset.update(fecha_contratacion=fecha_hace_2_anos)
        for perfil in queryset:
            perfil.actualizar_dias_vacaciones()
        self.message_user(request, f'{updated} empleados ajustados a 2 años de antigüedad (14 días).')
    simular_2_anos.short_description = "🧪 Simular 2 años de antigüedad"
    
    def simular_5_anos(self, request, queryset):
        """Simular que el empleado tiene 5 años de antigüedad (para pruebas)"""
        fecha_hace_5_anos = date.today() - timedelta(days=1825)
        updated = queryset.update(fecha_contratacion=fecha_hace_5_anos)
        for perfil in queryset:
            perfil.actualizar_dias_vacaciones()
        self.message_user(request, f'{updated} empleados ajustados a 5 años de antigüedad (20 días).')
    simular_5_anos.short_description = "🧪 Simular 5 años de antigüedad"
    
    def actualizar_dias_vacaciones(self, request, queryset):
        """Actualizar días de vacaciones según antigüedad actual"""
        for perfil in queryset:
            perfil.actualizar_dias_vacaciones()
        self.message_user(request, f'Días de vacaciones actualizados para {queryset.count()} empleados.')
    actualizar_dias_vacaciones.short_description = "🔄 Actualizar días según antigüedad"


@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    """Admin para gestión de departamentos"""
    
    list_display = ['nombre', 'jefe', 'empleados_count', 'activo']
    list_filter = ['activo']
    search_fields = ['nombre', 'descripcion']
    ordering = ['nombre']


@admin.register(SolicitudVacaciones)
class SolicitudVacacionesAdmin(admin.ModelAdmin):
    """Admin para gestión de solicitudes de vacaciones"""
    
    list_display = [
        'empleado', 'fecha_inicio', 'fecha_fin', 'dias_solicitados',
        'tipo', 'estado', 'fecha_solicitud'
    ]
    
    list_filter = [
        'estado', 'tipo', 'fecha_solicitud',
        ('fecha_solicitud', admin.DateFieldListFilter),
    ]
    
    search_fields = [
        'empleado__usuario__username', 'empleado__usuario__first_name',
        'empleado__usuario__last_name', 'empleado__numero_empleado'
    ]
    
    readonly_fields = ['fecha_solicitud', 'dias_solicitados']
    
    fieldsets = (
        ('Información de la Solicitud', {
            'fields': ('empleado', 'fecha_inicio', 'fecha_fin', 'dias_solicitados', 'tipo', 'motivo')
        }),
        ('Estado y Aprobaciones', {
            'fields': ('estado', 'aprobado_por_jefe', 'aprobado_por_rh')
        }),
        ('Comentarios', {
            'fields': ('comentarios_jefe', 'comentarios_rh')
        }),
        ('Fechas', {
            'fields': ('fecha_solicitud', 'fecha_aprobacion_jefe', 'fecha_aprobacion_rh')
        }),
    )
    
    ordering = ['-fecha_solicitud']


@admin.register(ConfiguracionSistema)
class ConfiguracionSistemaAdmin(admin.ModelAdmin):
    """Admin para configuraciones del sistema"""
    
    list_display = ['nombre', 'valor', 'descripcion']
    search_fields = ['nombre', 'descripcion']


# Personalizar el admin de Django
admin.site.site_header = "Sistema de Recursos Humanos - Grupo Keila"
admin.site.site_title = "RH Admin"
admin.site.index_title = "Panel de Administración"
