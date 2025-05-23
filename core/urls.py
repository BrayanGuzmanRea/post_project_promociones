from django.urls import path
from . import views

from django.urls import register_converter
import uuid

class UUIDConverter:
    regex = '[0-9a-f-]{36}'

    def to_python(self, value):
        return uuid.UUID(value)

    def to_url(self, value):
        return str(value)

register_converter(UUIDConverter, 'uuid')

urlpatterns = [
    
    # path('vendedores/', views.vendedores_list, name='vendedores_list'),
    # path('usuarios/', views.usuarios_list, name='usuarios_list'),
    # path('usuarios/nuevo/', views.usuario_create, name='usuario_create'),

    path('articulos/', views.articulos_list, name='articulos_list'), 
    path('articulos/nuevo/', views.articulo_create, name='articulo_create'),
    path('articulos/<uuid:articulo_id>/', views.articulo_detail, name='articulo_detail'), 
    path('articulos/<uuid:articulo_id>/editar/', views.articulo_edit, name='articulo_edit'),
    path('articulos/<uuid:articulo_id>/eliminar/', views.articulo_delete, name='articulo_delete'),

    path('carrito/agregar/<uuid:articulo_id>/', views.agregar_producto, name='agregar_producto'),
    path('carrito/', views.vista_carrito, name='cart_detail'),

    #Nuevo Cambio agregado:
    path('carrito/', views.vista_carrito, name='vista_carrito'),
    path('carrito/eliminar/<int:detalle_id>/', views.eliminar_detalle_carrito, name='eliminar_detalle_carrito'),

    #Todo lo que tiene que ver con promociones
    path('promociones/registrar/', views.registrar_promocion, name='registrar_promocion'),
    path('api/sucursales/', views.obtener_sucursales_por_empresa, name='api_sucursales'),
    path('api/articulos_por_sucursal/', views.obtener_articulos_por_sucursal, name='api_articulos_por_sucursal'),
]
