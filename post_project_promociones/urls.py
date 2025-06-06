"""
URL configuration for post_project_promociones project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include 
from django.conf import settings 
from django.conf.urls.static import static 
from django.views.generic import TemplateView 
from django.contrib.auth import views as auth_views
from core import views  # Importamos las vistas de core


urlpatterns = [
    path('admin/', admin.site.urls),

    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),

    # Aquí agregaríamos las URLs de nuestras apps 
    # Cambiamos la URL raíz para que use la vista home de core/views.py
    path('', views.home, name='home'),
    path('core/', include('core.urls')),
    path('', views.home, name='home'),  # Usamos esta vista para la raíz
    path('empresa/<int:empresa_id>/', views.empresa_seleccionada, name='empresa_seleccionada'),
    path('agregar-producto/<uuid:articulo_id>/', views.agregar_producto, name='agregar_producto'),
    path('carrito/', views.vista_carrito, name='carrito'),
]

# Configuración estática
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



