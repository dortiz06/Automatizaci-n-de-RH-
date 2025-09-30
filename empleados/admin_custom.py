from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render
from .models import Departamento, Empleado, Vacacion


class EmpleadoAdminCustom(admin.ModelAdmin):
    """Admin personalizado para Empleado con diseño mejorado"""
    
    # Configuración de la lista
    list_display = [
        'foto_perfil', 'numero_empleado', 'nombre_completo', 'departamento', 
        'puesto', 'fecha_ingreso', 'dias_vacaciones_disponibles', 'estado_activo'
    ]
    list_filter = ['departamento', 'activo', 'genero', 'estado_civil', 'fecha_ingreso']
    search_fields = ['numero_empleado', 'nombre', 'apellido_paterno', 'apellido_materno', 'email']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion', 'dias_vacaciones_disponibles', 'antiguedad_anos']
    
    # Configuración de campos
    fieldsets = (
        ('👤 Información Personal', {
            'fields': (
                'numero_empleado', 
                ('nombre', 'apellido_paterno', 'apellido_materno'),
                ('fecha_nacimiento', 'genero', 'estado_civil'),
                ('telefono', 'email'),
                'direccion'
            ),
            'classes': ('wide', 'extrapretty'),
        }),
        ('🏢 Información Laboral', {
            'fields': (
                ('departamento', 'puesto'),
                ('fecha_ingreso', 'salario'),
                'supervisor'
            ),
            'classes': ('wide', 'extrapretty'),
        }),
        ('🏖️ Gestión de Vacaciones', {
            'fields': (
                ('dias_vacaciones_anuales', 'dias_vacaciones_usados'),
                'dias_vacaciones_disponibles'
            ),
            'classes': ('wide', 'extrapretty'),
        }),
        ('📊 Estado y Auditoría', {
            'fields': (
                'activo',
                ('fecha_creacion', 'fecha_actualizacion'),
                'antiguedad_anos'
            ),
            'classes': ('wide', 'extrapretty'),
        }),
    )
    
    # Campos personalizados para mostrar
    def foto_perfil(self, obj):
        """Muestra una foto de perfil con iniciales"""
        iniciales = f"{obj.nombre[0]}{obj.apellido_paterno[0]}"
        return format_html(
            '<div style="width: 40px; height: 40px; background: linear-gradient(135deg, #3498db, #5dade2); '
            'border-radius: 50%; display: flex; align-items: center; justify-content: center; '
            'color: white; font-weight: bold; font-size: 14px;">{}</div>',
            iniciales
        )
    foto_perfil.short_description = 'Foto'
    
    def estado_activo(self, obj):
        """Muestra el estado con un indicador visual"""
        if obj.activo:
            return format_html(
                '<span style="background: #27ae60; color: white; padding: 4px 8px; '
                'border-radius: 12px; font-size: 12px; font-weight: bold;">✓ ACTIVO</span>'
            )
        else:
            return format_html(
                '<span style="background: #e74c3c; color: white; padding: 4px 8px; '
                'border-radius: 12px; font-size: 12px; font-weight: bold;">✗ INACTIVO</span>'
            )
    estado_activo.short_description = 'Estado'
    
    # Configuración de formulario
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }
        js = ('admin/js/custom_admin.js',)


class VacacionAdminCustom(admin.ModelAdmin):
    """Admin personalizado para Vacación con diseño mejorado"""
    
    list_display = [
        'empleado_info', 'periodo_vacaciones', 'dias_solicitados', 
        'estado_badge', 'fecha_solicitud', 'motivo_corto'
    ]
    list_filter = ['estado', 'fecha_solicitud', 'empleado__departamento']
    search_fields = ['empleado__nombre', 'empleado__apellido_paterno', 'empleado__apellido_materno']
    readonly_fields = ['fecha_solicitud', 'dias_solicitados']
    
    fieldsets = (
        ('📋 Información de la Solicitud', {
            'fields': (
                'empleado',
                ('fecha_inicio', 'fecha_fin'),
                'dias_solicitados',
                'motivo'
            ),
            'classes': ('wide', 'extrapretty'),
        }),
        ('✅ Estado y Aprobación', {
            'fields': (
                'estado',
                'comentarios_rh',
                ('fecha_aprobacion', 'aprobado_por')
            ),
            'classes': ('wide', 'extrapretty'),
        }),
        ('📅 Auditoría', {
            'fields': ('fecha_solicitud',),
            'classes': ('wide', 'extrapretty'),
        }),
    )
    
    def empleado_info(self, obj):
        """Información del empleado con foto"""
        iniciales = f"{obj.empleado.nombre[0]}{obj.empleado.apellido_paterno[0]}"
        return format_html(
            '<div style="display: flex; align-items: center;">'
            '<div style="width: 30px; height: 30px; background: linear-gradient(135deg, #3498db, #5dade2); '
            'border-radius: 50%; display: flex; align-items: center; justify-content: center; '
            'color: white; font-weight: bold; font-size: 12px; margin-right: 10px;">{}</div>'
            '<div><strong>{}</strong><br><small style="color: #666;">{}</small></div>'
            '</div>',
            iniciales,
            obj.empleado.nombre_completo,
            obj.empleado.puesto
        )
    empleado_info.short_description = 'Empleado'
    
    def periodo_vacaciones(self, obj):
        """Período de vacaciones formateado"""
        return format_html(
            '<strong>{} - {}</strong>',
            obj.fecha_inicio.strftime('%d/%m/%Y'),
            obj.fecha_fin.strftime('%d/%m/%Y')
        )
    periodo_vacaciones.short_description = 'Período'
    
    def estado_badge(self, obj):
        """Estado con badge colorido"""
        colores = {
            'P': ('#f39c12', 'PENDIENTE'),
            'A': ('#27ae60', 'APROBADA'),
            'R': ('#e74c3c', 'RECHAZADA'),
            'C': ('#95a5a6', 'CANCELADA')
        }
        color, texto = colores.get(obj.estado, ('#95a5a6', 'DESCONOCIDO'))
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 8px; '
            'border-radius: 12px; font-size: 12px; font-weight: bold;">{}</span>',
            color, texto
        )
    estado_badge.short_description = 'Estado'
    
    def motivo_corto(self, obj):
        """Motivo truncado"""
        if obj.motivo:
            return obj.motivo[:50] + '...' if len(obj.motivo) > 50 else obj.motivo
        return 'Sin motivo especificado'
    motivo_corto.short_description = 'Motivo'
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }


class DepartamentoAdminCustom(admin.ModelAdmin):
    """Admin personalizado para Departamento"""
    
    list_display = ['nombre', 'descripcion', 'numero_empleados']
    search_fields = ['nombre', 'descripcion']
    
    def numero_empleados(self, obj):
        """Número de empleados en el departamento"""
        count = obj.empleado_set.filter(activo=True).count()
        return format_html(
            '<span style="background: #3498db; color: white; padding: 4px 8px; '
            'border-radius: 12px; font-size: 12px; font-weight: bold;">{} empleados</span>',
            count
        )
    numero_empleados.short_description = 'Empleados Activos'
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }


# Configuración del sitio de administración
admin.site.site_header = "🏢 Sistema de Recursos Humanos"
admin.site.site_title = "RH Admin"
admin.site.index_title = "Panel de Administración"

# Registrar los modelos con el admin personalizado
admin.site.register(Departamento, DepartamentoAdminCustom)
admin.site.register(Empleado, EmpleadoAdminCustom)
admin.site.register(Vacacion, VacacionAdminCustom)
