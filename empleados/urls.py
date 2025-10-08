from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from . import auth_views


app_name = 'empleados'

urlpatterns = [
    # === RUTAS PRINCIPALES ===
    path('', auth_views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', auth_views.logout_view, name='logout'),
    
    # === DASHBOARDS POR PERFIL ===
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('rh/', views.rh_dashboard, name='rh_dashboard'),
    path('jefe/', views.jefe_dashboard, name='jefe_dashboard'),
    path('empleado/', views.empleado_dashboard, name='empleado_dashboard'),
    
    # === GESTIÓN DE USUARIOS ===
    path('usuarios/', views.gestion_usuarios, name='gestion_usuarios'),
    path('usuarios/crear/', views.crear_usuario, name='crear_usuario'),
    path('usuarios/<int:perfil_id>/editar/', views.editar_perfil, name='editar_perfil'),
    
    # === GESTIÓN DE VACACIONES ===
    path('vacaciones/solicitar/', views.solicitar_vacaciones, name='solicitar_vacaciones'),
    path('vacaciones/<int:solicitud_id>/aprobar-jefe/', views.aprobar_jefe, name='aprobar_jefe'),
    path('vacaciones/<int:solicitud_id>/aprobar-rh/', views.aprobar_rh, name='aprobar_rh'),
    
    # === GESTIÓN DE DEPARTAMENTOS ===
    path('departamentos/', views.gestion_departamentos, name='gestion_departamentos'),
    path('departamentos/crear/', views.crear_departamento, name='crear_departamento'),
    
    # === API ENDPOINTS ===
    path('api/validar-antiguedad/', views.validar_antiguedad, name='validar_antiguedad'),
    
    # === PERFIL DE USUARIO ===
    path('perfil/', auth_views.perfil_usuario, name='perfil_usuario'),
]

# URLs de error
handler403 = views.error_403
handler404 = views.error_404
handler500 = views.error_500

# Servir archivos estáticos en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
