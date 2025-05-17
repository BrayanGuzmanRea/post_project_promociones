# Agragado por Branz Saul
from django.shortcuts import render
from .models import Usuario, Rol

def vendedores_list(request):
    try:
        rol_vendedor = Rol.objects.get(nombre='Vendedor')  # Ajusta el nombre si es distinto
        vendedores = Usuario.objects.filter(perfil=rol_vendedor)
    except Rol.DoesNotExist:
        vendedores = Usuario.objects.none()

    return render(request, 'core/vendedores/list.html', {'vendedores': vendedores})
##############################
