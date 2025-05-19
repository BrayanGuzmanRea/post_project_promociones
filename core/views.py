import uuid
from django.shortcuts import render, redirect
from .models import Usuario, Rol
from django.contrib import messages
from .forms import UsuarioForm
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from .forms import ArticuloForm
from core.models import Empresa, Sucursal, Articulo

def home(request):
    """
    Vista para la página principal que muestra las empresas.
    """
    empresas = Empresa.objects.all()
    context = {
        'empresas': empresas,
        # Agrega aquí otras variables que necesites para tu plantilla
    }
    return render(request, 'core/index.html', context)

def empresa_detail(request, empresa_id):
    """
    Vista para mostrar detalle de una empresa específica.
    """
    empresa = get_object_or_404(Empresa, pk=empresa_id)
    context = {
        'empresas': empresa,
    }
    return render(request, 'core/empresa_detail.html', context)

def empresa_seleccionada(request, empresa_id):
    empresa = get_object_or_404(Empresa, pk=empresa_id)
    sucursales = Sucursal.objects.filter(empresa_id=empresa.empresa_id)
    sucursales_con_articulos = []
    for suc in sucursales:
        articulos = Articulo.objects.filter(sucursal_id=suc.sucursal_id)
        sucursales_con_articulos.append({
            'sucursal': suc,
            'articulos': articulos,
        })

    context = {
        'empresa': empresa,
        'sucursales_con_articulos': sucursales_con_articulos,
    }
    return render(request, 'core/empresas/empresaSeleccionada.html', context)

def agregar_producto(request, articulo_id):
    # Obtener el producto que se desea agregar al carrito
    articulo = get_object_or_404(Articulo, pk=articulo_id)
    
    # Lógica para agregar el producto al carrito (esto se debe implementar)
    # Ejemplo de agregarlo a la sesión:
    carrito = request.session.get('carrito', [])
    carrito.append(articulo_id)  # Guardar solo el ID del producto, o el objeto completo si prefieres
    request.session['carrito'] = carrito

    # Redirigir al usuario a la misma página para continuar visualizando productos
    return redirect(request.META.get('HTTP_REFERER'))
  
def vendedores_list(request):
    try:
        rol_vendedor = Rol.objects.get(nombre='Vendedor')  # Ajusta el nombre si es distinto
        vendedores = Usuario.objects.filter(perfil=rol_vendedor)
    except Rol.DoesNotExist:
        vendedores = Usuario.objects.none()

    return render(request, 'core/vendedores/list.html', {'vendedores': vendedores})


def usuario_create(request):
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario registrado correctamente')
            return redirect('usuarios_list')  # Cambia por la URL que quieras
    else:
        form = UsuarioForm()
    return render(request, 'core/usuarios/form.html', {'form': form})


def usuarios_list(request):
    usuarios = Usuario.objects.all()
    return render(request, 'core/usuarios/list.html', {'usuarios': usuarios})

###############ARTICULOS###############

# @login_required
def articulos_list(request):
    """Vista para listar artículos"""
    articulos_list = Articulo.objects.all()

    # Filtros (podrías expandir esto)
    q = request.GET.get("q")
    if q:
        articulos_list = articulos_list.filter(descripcion__icontains=q)

    # Paginación
    paginator = Paginator(articulos_list, 15)  # 15 artículos por página
    page_number = request.GET.get("page")
    articulos = paginator.get_page(page_number)

    context = {
        "articulos": articulos,
    }
    return render(request, "core/articulos/new_list.html", context)

#@login_required
def articulo_detail(request, articulo_id):
    """Vista para ver el detalle de un artículo"""
    articulo = get_object_or_404(Articulo, articulo_id=articulo_id)

    # Guardar en el historial de productos visitados

    if 'viewed_products' not in request.session: 
        request.session['viewed_products'] = [] 
    
    # Convertir UUID a string para poder guardarlo en sesión 
    producto_actual = str(articulo.articulo_id) 
    viewed_products = request.session['viewed_products'] 

    # Eliminar si ya existe y añadir al principio 
    if producto_actual in viewed_products: 
        viewed_products.remove(producto_actual) 
    
    # Añadir al principio y mantener solo los últimos 5 
    viewed_products.insert(0, producto_actual) 
    request.session['viewed_products'] = viewed_products[:5] 
    request.session.modified = True 
    
    # Obtener productos visitados recientemente 
    recent_products = [] 
    if viewed_products: 
        recent_uuids = [uuid.UUID(id_str) for id_str in viewed_products[1:6]]  
    
    # Excluir el actual 
    if recent_uuids: 
        recent_products = Articulo.objects.filter(articulo_id__in=recent_uuids) 

    context = {
        "articulo": articulo,
        'recent_products': recent_products,
    }
    return render(request, "core/articulos/detail.html", context)

#@login_required
def articulo_edit(request, articulo_id):
    """Vista para editar un artículo existente"""
    articulo = get_object_or_404(Articulo, articulo_id=articulo_id)
    #lista_precio = get_object_or_404(ListaPrecio, articulo=articulo)

    if request.method == "POST":
        form = ArticuloForm(request.POST, instance=articulo)
        #precio_form = ListaPrecioForm(request.POST, instance=lista_precio)

        #if form.is_valid() and precio_form.is_valid():
        #    form.save()
        #    precio_form.save()

        #    messages.success(request, "Artículo actualizado correctamente.")
        #    return redirect("articulo_detail", articulo_id=articulo.articulo_id)
    else:
        form = ArticuloForm(instance=articulo)
        #precio_form = ListaPrecioForm(instance=lista_precio)

    context = {
        "form": form,
        #"precio_form": precio_form,
    }
    return render(request, "core/articulos/form.html", context)

#@login_required
def articulo_create(request):
    """Vista para crear un nuevo artículo"""
    if request.method == "POST":
        form = ArticuloForm(request.POST)
        #precio_form = ListaPrecioForm(request.POST)

        if form.is_valid() and precio_form.is_valid():

            try:
                # Generar ID para el artículo
                articulo = form.save(commit=False)
                articulo.articulo_id = uuid.uuid4()
                articulo.save()

                # Guardar precios
                lista_precio = precio_form.save(commit=False)
                lista_precio.articulo = articulo
                lista_precio.save()
                messages.success(request, f'¡Artículo "{articulo.descripcion}"creado correctamente!')

                return redirect("articulo_detail", articulo_id=articulo.articulo_id)
            except Exception as e: 
                messages.error(request, f'Error al crear el artículo:{str(e)}')

        else: 
            messages.warning(request, 'Por favor corrija los errores en el formulario.')  
    else:
        form = ArticuloForm()
        #precio_form = ListaPrecioForm()

    context = {
        "form": form,
        #"precio_form": precio_form,
    }
    return render(request, "core/articulos/form.html", context)

#@login_required
def articulo_delete(request, articulo_id):
    """Vista para eliminar un artículo"""
    articulo = get_object_or_404(Articulo, articulo_id=articulo_id)

    if request.method == "POST":
        articulo.delete()

        messages.success(request, "Artículo eliminado correctamente.")
        return redirect("articulos_list")

    context = {
        "articulo": articulo,
    }
    return render(request, "core/articulos/delete.html", context)

#################################
