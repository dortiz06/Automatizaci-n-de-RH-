from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from .models import Empleado, Vacacion, Departamento


class EmpleadoInline(admin.StackedInline):
    model = Empleado
    can_delete = False
    verbose_name_plural = 'Perfil de Empleado'
    fields = ('numero_empleado', 'departamento', 'puesto', 'supervisor', 'activo')


class CustomUserAdmin(UserAdmin):
    inlines = (EmpleadoInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_empleado_info')
    
    def get_empleado_info(self, obj):
        try:
            empleado = obj.empleado
            return format_html(
                '<span style="color: #0038A8;">{}</span> - {}',
                empleado.numero_empleado,
                empleado.puesto
            )
        except:
            return "Sin perfil de empleado"
    get_empleado_info.short_description = 'Información de Empleado'


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('numero_empleado', 'nombre_completo', 'departamento', 'puesto', 'fecha_ingreso', 'antiguedad_anos', 'activo')
    list_filter = ('departamento', 'activo', 'fecha_ingreso', 'genero')
    search_fields = ('numero_empleado', 'nombre', 'apellido_paterno', 'apellido_materno', 'email')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion', 'antiguedad_anos')
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('numero_empleado', 'nombre', 'apellido_paterno', 'apellido_materno', 
                      'fecha_nacimiento', 'genero', 'estado_civil', 'user')
        }),
        ('Información de Contacto', {
            'fields': ('telefono', 'email', 'direccion')
        }),
        ('Información Laboral', {
            'fields': ('departamento', 'puesto', 'fecha_ingreso', 'salario', 'supervisor')
        }),
        ('Gestión de Vacaciones', {
            'fields': ('dias_vacaciones_anuales', 'dias_vacaciones_usados', 'dias_vacaciones_disponibles')
        }),
        ('Estado y Auditoría', {
            'fields': ('activo', 'fecha_creacion', 'fecha_actualizacion')
        }),
    )
    
    def antiguedad_anos(self, obj):
        return f"{obj.antiguedad_anos} años"
    antiguedad_anos.short_description = 'Antigüedad'


@admin.register(Vacacion)
class VacacionAdmin(admin.ModelAdmin):
    list_display = ('empleado', 'fecha_inicio', 'fecha_fin', 'dias_solicitados', 'tipo', 'etapa', 'estado', 'fecha_solicitud')
    list_filter = ('estado', 'tipo', 'etapa', 'fecha_solicitud', 'empleado__departamento')
    search_fields = ('empleado__nombre', 'empleado__apellido_paterno', 'empleado__apellido_materno')
    readonly_fields = ('fecha_solicitud', 'dias_solicitados')
    
    fieldsets = (
        ('Información de la Solicitud', {
            'fields': ('empleado', 'fecha_inicio', 'fecha_fin', 'dias_solicitados', 'motivo')
        }),
        ('Tipo y Estado', {
            'fields': ('tipo', 'etapa', 'estado', 'motivo_extraordinario')
        }),
        ('Proceso de Aprobación', {
            'fields': ('aprobado_jefe', 'aprobado_rh', 'comentarios_rh', 'aprobado_por')
        }),
        ('Auditoría', {
            'fields': ('fecha_solicitud', 'fecha_aprobacion')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('empleado', 'empleado__departamento')


@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'get_empleados_count')
    search_fields = ('nombre', 'descripcion')
    
    def get_empleados_count(self, obj):
        return obj.empleado_set.filter(activo=True).count()
    get_empleados_count.short_description = 'Empleados Activos'


# Desregistrar el UserAdmin por defecto y registrar el personalizado
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)