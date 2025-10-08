from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect
from .models import Perfil


def login_view(request):
    """Vista de login personalizada"""
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, f'¡Bienvenido, {user.first_name or user.username}!')
                    
                    # Redirigir según el perfil del usuario
                    next_url = request.GET.get('next', 'empleados:dashboard')
                    if next_url == 'empleados:dashboard':
                        # Verificar si tiene perfil
                        try:
                            perfil = Perfil.objects.get(usuario=user)
                            if perfil.es_admin():
                                next_url = 'empleados:admin_dashboard'
                            elif perfil.es_rh():
                                next_url = 'empleados:rh_dashboard'
                            elif perfil.es_jefe_area():
                                next_url = 'empleados:jefe_dashboard'
                            else:
                                next_url = 'empleados:empleado_dashboard'
                        except Perfil.DoesNotExist:
                            # No tiene perfil
                            next_url = 'empleados:dashboard'
                    
                    return redirect(next_url)
                else:
                    messages.error(request, 'Tu cuenta está desactivada.')
            else:
                messages.error(request, 'Usuario o contraseña incorrectos.')
        else:
            messages.error(request, 'Por favor, completa todos los campos.')
    
    return render(request, 'empleados/login.html')


@login_required
def logout_view(request):
    """Vista de logout personalizada"""
    logout(request)
    messages.info(request, 'Has cerrado sesión exitosamente.')
    return redirect('login')


@login_required
def perfil_usuario(request):
    """Vista del perfil del usuario actual"""
    try:
        empleado = Empleado.objects.get(user=request.user)
        tiene_perfil = True
    except Empleado.DoesNotExist:
        empleado = None
        tiene_perfil = False
    
    # Obtener información de grupos
    grupos = request.user.groups.all()
    es_rh = request.user.groups.filter(name='RH').exists()
    es_jefe = request.user.groups.filter(name='JEFES').exists()
    es_empleado = request.user.groups.filter(name='EMPLEADOS').exists()
    
    context = {
        'user': request.user,
        'empleado': empleado,
        'tiene_perfil': tiene_perfil,
        'grupos': grupos,
        'es_rh': es_rh,
        'es_jefe': es_jefe,
        'es_empleado': es_empleado,
    }
    
    return render(request, 'empleados/perfil_usuario.html', context)
