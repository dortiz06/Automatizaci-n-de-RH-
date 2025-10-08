from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from .models import Perfil, Departamento, SolicitudVacaciones, ConfiguracionSistema
from .forms import (
    UsuarioConPerfilForm, SolicitudVacacionesForm, 
    AprobacionJefeForm, AprobacionRHForm, EditarPerfilForm, ConfigurarDepartamentoForm
)
from datetime import date, timedelta


def get_user_profile(user):
    """Obtener perfil del usuario actual"""
    try:
        return user.perfil
    except Perfil.DoesNotExist:
        return None


@login_required
def dashboard(request):
    """Dashboard principal redirigido según tipo de perfil"""
    perfil = get_user_profile(request.user)
    
    if not perfil:
        messages.error(request, 'No tienes un perfil asignado. Contacta al administrador.')
        return redirect('logout')
    
    # Redirigir según tipo de perfil
    if perfil.es_admin():
        return redirect('admin_dashboard')
    elif perfil.es_rh():
        return redirect('rh_dashboard')
    elif perfil.es_jefe_area():
        return redirect('jefe_dashboard')
    else:
        return redirect('empleado_dashboard')


@login_required
def admin_dashboard(request):
    """Dashboard para administradores"""
    perfil = get_user_profile(request.user)
    if not perfil or not perfil.es_admin():
        raise PermissionDenied
    
    # Estadísticas generales
    stats = {
        'total_empleados': Perfil.objects.filter(activo=True).count(),
        'total_departamentos': Departamento.objects.filter(activo=True).count(),
        'solicitudes_pendientes': SolicitudVacaciones.objects.filter(
            estado__in=['PENDIENTE_JEFE', 'PENDIENTE_RH']
        ).count(),
        'solicitudes_este_mes': SolicitudVacaciones.objects.filter(
            fecha_solicitud__month=timezone.now().month
        ).count(),
    }
    
    # Solicitudes recientes
    solicitudes_recientes = SolicitudVacaciones.objects.filter(
        estado__in=['PENDIENTE_JEFE', 'PENDIENTE_RH']
    ).order_by('-fecha_solicitud')[:10]
    
    context = {
        'stats': stats,
        'solicitudes_recientes': solicitudes_recientes,
        'perfil': perfil,
    }
    return render(request, 'empleados/admin/dashboard.html', context)


@login_required
def rh_dashboard(request):
    """Dashboard para Recursos Humanos"""
    perfil = get_user_profile(request.user)
    if not perfil or not perfil.es_rh():
        raise PermissionDenied
    
    # Solicitudes pendientes de RH
    solicitudes_pendientes = SolicitudVacaciones.objects.filter(
        estado='PENDIENTE_RH'
    ).order_by('-fecha_solicitud')
    
    # Estadísticas
    stats = {
        'solicitudes_pendientes': solicitudes_pendientes.count(),
        'aprobadas_este_mes': SolicitudVacaciones.objects.filter(
            estado='APROBADO_RH',
            fecha_aprobacion_rh__month=timezone.now().month
        ).count(),
        'rechazadas_este_mes': SolicitudVacaciones.objects.filter(
            estado='RECHAZADO_RH',
            fecha_aprobacion_rh__month=timezone.now().month
        ).count(),
    }
    
    context = {
        'solicitudes_pendientes': solicitudes_pendientes,
        'stats': stats,
        'perfil': perfil,
    }
    return render(request, 'empleados/rh/dashboard.html', context)


@login_required
def jefe_dashboard(request):
    """Dashboard para Jefes de Área"""
    perfil = get_user_profile(request.user)
    if not perfil or not perfil.es_jefe_area():
        raise PermissionDenied
    
    # Solicitudes de empleados del departamento
    solicitudes_pendientes = SolicitudVacaciones.objects.filter(
        empleado__departamento=perfil.departamento,
        estado='PENDIENTE_JEFE'
    ).order_by('-fecha_solicitud')
    
    # Estadísticas del departamento
    empleados_departamento = Perfil.objects.filter(
        departamento=perfil.departamento,
        activo=True
    )
    
    stats = {
        'empleados_departamento': empleados_departamento.count(),
        'solicitudes_pendientes': solicitudes_pendientes.count(),
        'aprobadas_este_mes': SolicitudVacaciones.objects.filter(
            empleado__departamento=perfil.departamento,
            estado='APROBADO_JEFE',
            fecha_aprobacion_jefe__month=timezone.now().month
        ).count(),
    }
    
    context = {
        'solicitudes_pendientes': solicitudes_pendientes,
        'stats': stats,
        'perfil': perfil,
        'empleados_departamento': empleados_departamento,
    }
    return render(request, 'empleados/jefe/dashboard.html', context)


@login_required
def empleado_dashboard(request):
    """Dashboard para Empleados"""
    perfil = get_user_profile(request.user)
    if not perfil or not perfil.es_empleado():
        raise PermissionDenied
    
    # Solicitudes del empleado
    solicitudes = SolicitudVacaciones.objects.filter(
        empleado=perfil
    ).order_by('-fecha_solicitud')
    
    # Estadísticas personales
    stats = {
        'dias_disponibles': perfil.dias_vacaciones_disponibles,
        'dias_usados': perfil.dias_vacaciones_usados,
        'solicitudes_pendientes': solicitudes.filter(
            estado__in=['PENDIENTE_JEFE', 'PENDIENTE_RH']
        ).count(),
        'solicitudes_aprobadas': solicitudes.filter(estado='APROBADO_RH').count(),
    }
    
    context = {
        'solicitudes': solicitudes,
        'stats': stats,
        'perfil': perfil,
    }
    return render(request, 'empleados/empleado/dashboard.html', context)


# === GESTIÓN DE USUARIOS ===

@login_required
def gestion_usuarios(request):
    """Gestión de usuarios - Solo RH y Admin"""
    perfil = get_user_profile(request.user)
    if not perfil or not (perfil.es_rh() or perfil.es_admin()):
        raise PermissionDenied
    
    usuarios = Perfil.objects.filter(activo=True)
    
    # Filtros
    tipo_perfil = request.GET.get('tipo_perfil')
    departamento_id = request.GET.get('departamento')
    busqueda = request.GET.get('busqueda')
    
    if tipo_perfil:
        usuarios = usuarios.filter(tipo_perfil=tipo_perfil)
    
    if departamento_id:
        usuarios = usuarios.filter(departamento_id=departamento_id)
    
    if busqueda:
        usuarios = usuarios.filter(
            Q(usuario__username__icontains=busqueda) |
            Q(usuario__first_name__icontains=busqueda) |
            Q(usuario__last_name__icontains=busqueda) |
            Q(numero_empleado__icontains=busqueda)
        )
    
    departamentos = Departamento.objects.filter(activo=True)
    
    context = {
        'usuarios': usuarios,
        'departamentos': departamentos,
        'tipo_actual': tipo_perfil,
        'departamento_actual': departamento_id,
        'busqueda_actual': busqueda,
        'perfil': perfil,
    }
    return render(request, 'empleados/rh/gestion_usuarios.html', context)


@login_required
def crear_usuario(request):
    """Crear nuevo usuario con perfil"""
    perfil = get_user_profile(request.user)
    if not perfil or not (perfil.es_rh() or perfil.es_admin()):
        raise PermissionDenied
    
    if request.method == 'POST':
        form = UsuarioConPerfilForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Usuario {user.username} creado exitosamente.')
            return redirect('gestion_usuarios')
    else:
        form = UsuarioConPerfilForm()
    
    context = {
        'form': form,
        'perfil': perfil,
    }
    return render(request, 'empleados/rh/crear_usuario.html', context)


@login_required
def editar_perfil(request, perfil_id):
    """Editar perfil de usuario"""
    perfil = get_user_profile(request.user)
    perfil_editado = get_object_or_404(Perfil, id=perfil_id)
    
    # Verificar permisos
    if not (perfil.es_rh() or perfil.es_admin() or perfil == perfil_editado):
        raise PermissionDenied
    
    if request.method == 'POST':
        form = EditarPerfilForm(request.POST, instance=perfil_editado)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado exitosamente.')
            return redirect('gestion_usuarios')
    else:
        form = EditarPerfilForm(instance=perfil_editado)
    
    context = {
        'form': form,
        'perfil_editado': perfil_editado,
        'perfil': perfil,
    }
    return render(request, 'empleados/rh/editar_perfil.html', context)


# === GESTIÓN DE VACACIONES ===

@login_required
def solicitar_vacaciones(request):
    """Solicitar vacaciones - Solo empleados"""
    perfil = get_user_profile(request.user)
    if not perfil or not perfil.es_empleado():
        raise PermissionDenied
    
    if request.method == 'POST':
        form = SolicitudVacacionesForm(request.POST, empleado=perfil)
        if form.is_valid():
            solicitud = form.save(commit=False)
            solicitud.empleado = perfil
            solicitud.save()
            messages.success(request, 'Solicitud de vacaciones enviada exitosamente.')
            return redirect('empleado_dashboard')
    else:
        form = SolicitudVacacionesForm(empleado=perfil)
    
    context = {
        'form': form,
        'perfil': perfil,
    }
    return render(request, 'empleados/empleado/solicitar_vacaciones.html', context)


@login_required
def aprobar_jefe(request, solicitud_id):
    """Aprobar/rechazar solicitud por jefe de área"""
    perfil = get_user_profile(request.user)
    if not perfil or not perfil.es_jefe_area():
        raise PermissionDenied
    
    solicitud = get_object_or_404(SolicitudVacaciones, id=solicitud_id)
    
    # Verificar que el empleado pertenece al departamento del jefe
    if solicitud.empleado.departamento != perfil.departamento:
        raise PermissionDenied
    
    if request.method == 'POST':
        form = AprobacionJefeForm(request.POST, solicitud=solicitud)
        if form.is_valid():
            accion = form.cleaned_data['accion']
            comentario = form.cleaned_data['comentario']
            
            if accion == 'aprobar':
                if solicitud.aprobar_por_jefe(perfil, comentario):
                    messages.success(request, 'Solicitud aprobada exitosamente.')
                else:
                    messages.error(request, 'No se pudo aprobar la solicitud.')
            else:
                if solicitud.rechazar_por_jefe(perfil, comentario):
                    messages.success(request, 'Solicitud rechazada.')
                else:
                    messages.error(request, 'No se pudo rechazar la solicitud.')
            
            return redirect('jefe_dashboard')
    else:
        form = AprobacionJefeForm(solicitud=solicitud)
    
    context = {
        'form': form,
        'solicitud': solicitud,
        'perfil': perfil,
    }
    return render(request, 'empleados/jefe/aprobar_solicitud.html', context)


@login_required
def aprobar_rh(request, solicitud_id):
    """Aprobar/rechazar solicitud por RH"""
    perfil = get_user_profile(request.user)
    if not perfil or not perfil.es_rh():
        raise PermissionDenied
    
    solicitud = get_object_or_404(SolicitudVacaciones, id=solicitud_id)
    
    if request.method == 'POST':
        form = AprobacionRHForm(request.POST, solicitud=solicitud)
        if form.is_valid():
            accion = form.cleaned_data['accion']
            comentario = form.cleaned_data['comentario']
            
            if accion == 'aprobar':
                if solicitud.aprobar_por_rh(perfil, comentario):
                    messages.success(request, 'Solicitud aprobada exitosamente.')
                else:
                    messages.error(request, 'No se pudo aprobar la solicitud.')
            else:
                if solicitud.rechazar_por_rh(perfil, comentario):
                    messages.success(request, 'Solicitud rechazada.')
                else:
                    messages.error(request, 'No se pudo rechazar la solicitud.')
            
            return redirect('rh_dashboard')
    else:
        form = AprobacionRHForm(solicitud=solicitud)
    
    context = {
        'form': form,
        'solicitud': solicitud,
        'perfil': perfil,
    }
    return render(request, 'empleados/rh/aprobar_solicitud.html', context)


# === GESTIÓN DE DEPARTAMENTOS ===

@login_required
def gestion_departamentos(request):
    """Gestión de departamentos - Solo RH y Admin"""
    perfil = get_user_profile(request.user)
    if not perfil or not (perfil.es_rh() or perfil.es_admin()):
        raise PermissionDenied
    
    departamentos = Departamento.objects.filter(activo=True).annotate(
        empleados_count=Count('perfil')
    )
    
    context = {
        'departamentos': departamentos,
        'perfil': perfil,
    }
    return render(request, 'empleados/rh/gestion_departamentos.html', context)


@login_required
def crear_departamento(request):
    """Crear nuevo departamento"""
    perfil = get_user_profile(request.user)
    if not perfil or not (perfil.es_rh() or perfil.es_admin()):
        raise PermissionDenied
    
    if request.method == 'POST':
        form = ConfigurarDepartamentoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Departamento creado exitosamente.')
            return redirect('gestion_departamentos')
    else:
        form = ConfigurarDepartamentoForm()
    
    context = {
        'form': form,
        'perfil': perfil,
    }
    return render(request, 'empleados/rh/crear_departamento.html', context)


# === API ENDPOINTS ===

@login_required
def validar_antiguedad(request):
    """API para validar antigüedad de empleado"""
    perfil = get_user_profile(request.user)
    if not perfil:
        return JsonResponse({'error': 'Perfil no encontrado'}, status=400)
    
    antiguedad = perfil.antiguedad_anos
    puede_vacaciones_normales = antiguedad >= 1
    
    return JsonResponse({
        'antiguedad_anos': antiguedad,
        'puede_vacaciones_normales': puede_vacaciones_normales,
        'dias_disponibles': perfil.dias_vacaciones_disponibles,
    })


# === VISTAS DE ERROR ===

def error_403(request, exception=None):
    """Página de error 403 - Permisos insuficientes"""
    return render(request, 'empleados/errors/403.html', status=403)


def error_404(request, exception=None):
    """Página de error 404 - Página no encontrada"""
    return render(request, 'empleados/errors/404.html', status=404)


def error_500(request):
    """Página de error 500 - Error interno del servidor"""
    return render(request, 'empleados/errors/500.html', status=500)
