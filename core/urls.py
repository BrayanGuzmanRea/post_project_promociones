from django.urls import path
from . import views

urlpatterns = [
    # otras rutas
    path('vendedores/', views.vendedores_list, name='vendedores_list'),
]
