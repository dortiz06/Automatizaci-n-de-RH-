from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from .models import Perfil, SolicitudVacaciones, Departamento


class PerfilInline(admin.StackedInline):
    model = Perfil
    can_delete = False
    verbose_name_plural = 'Perfil'
    fields = ('tipo_perfil', 'departamento', 'numero_empleado', 'puesto', 'fecha_contratacion', 'salario', 'supervisor', 'activo')


class CustomUserAdmin(UserAdmin):
    inlines = (PerfilInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_tipo_perfil', 'get_departamento')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'perfil__tipo_perfil', 'perfil__departamento')
    
    def get_tipo_perfil(self, obj):
        try:
            return obj.perfil.get_tipo_perfil_display()
        except:
            return 'Sin perfil'
    get_tipo_perfil.short_description = 'Tipo de Perfil'
    
    def get_departamento(self, obj):
        try:
            return obj.perfil.departamento.nombre if obj.perfil.departamento else 'Sin departamento'
        except:
            return 'Sin departamento'
    get_departamento.short_description = 'Departamento'


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('numero_empleado', 'usuario', 'get_nombre_completo', 'tipo_perfil', 'departamento', 'puesto', 'activo')
    list_filter = ('tipo_perfil', 'departamento', 'activo', 'fecha_contratacion')
    search_fields = ('numero_empleado', 'usuario__username', 'usuario__first_name', 'usuario__last_name', 'puesto')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('usuario', 'tipo_perfil', 'numero_empleado', 'telefono', 'direccion', 'fecha_nacimiento')
        }),
        ('Información Laboral', {
            'fields': ('departamento', 'puesto', 'fecha_contratacion', 'salario', 'supervisor')
        }),
        ('Vacaciones', {
            'fields': ('dias_vacaciones_anuales', 'dias_vacaciones_usados')
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    def get_nombre_completo(self, obj):
        return obj.nombre_completo
    get_nombre_completo.short_description = 'Nombre Completo'


@admin.register(SolicitudVacaciones)
class SolicitudVacacionesAdmin(admin.ModelAdmin):
    list_display = ('empleado', 'fecha_inicio', 'fecha_fin', 'dias_solicitados', 'tipo', 'estado', 'fecha_solicitud')
    list_filter = ('estado', 'tipo', 'fecha_solicitud', 'empleado__departamento')
    search_fields = ('empleado__usuario__username', 'empleado__usuario__first_name', 'empleado__usuario__last_name')
    readonly_fields = ('fecha_solicitud', 'dias_solicitados')
    date_hierarchy = 'fecha_solicitud'
    
    fieldsets = (
        ('Información de la Solicitud', {
            'fields': ('empleado', 'fecha_inicio', 'fecha_fin', 'dias_solicitados', 'tipo', 'motivo', 'estado')
        }),
        ('Aprobación por Jefe', {
            'fields': ('aprobado_por_jefe', 'comentarios_jefe', 'fecha_aprobacion_jefe')
        }),
        ('Aprobación por RH', {
            'fields': ('aprobado_por_rh', 'comentarios_rh', 'fecha_aprobacion_rh')
        }),
        ('Auditoría', {
            'fields': ('fecha_solicitud',),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('empleado', 'fecha_inicio', 'fecha_fin', 'tipo', 'motivo')
        return self.readonly_fields


@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'jefe', 'get_empleados_count', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre', 'descripcion')
    
    def get_empleados_count(self, obj):
        count = obj.perfil_set.filter(activo=True).count()
        return format_html('<span style="color: #0066cc; font-weight: bold;">{}</span>', count)
    get_empleados_count.short_description = 'Empleados Activos'


# Reemplazar el UserAdmin por defecto
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Configuración del sitio de administración
admin.site.site_header = "Sistema de Recursos Humanos - Grupo Keila"
admin.site.site_title = "RH Admin"
admin.site.index_title = "Panel de Administración"