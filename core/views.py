from datetime import timezone
from decimal import Decimal
import uuid
from django.shortcuts import render, redirect
from .models import (
    # Modelos actualizados según nueva estructura
    ProductosBeneficios, BonificacionAplicada, Carrito, Cliente, 
    DescuentoAplicado, DetalleCarrito, DetallePedido, GrupoProveedor, 
    LineaArticulo, Pedido, Promocion, Rango, ProductoBonificadoRango,
    Beneficio, StockSucursal, Usuario, Rol, VerificacionProducto
)
from django.contrib import messages
from .forms import PromocionForm, UsuarioForm
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from .forms import ArticuloForm
from core.models import Empresa, Sucursal, Articulo

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone

# Necesario para realizar las promociones
from core.promociones import evaluar_promociones
from core.models import CanalCliente


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
    articulo = get_object_or_404(Articulo, pk=articulo_id)

    try:
        cantidad_str = request.POST.get('cantidad', '').strip()
        if not cantidad_str.isdigit() or int(cantidad_str) < 1:
            messages.error(request, 'La cantidad no puede ser 0 ni estar vacía.')
            return redirect(request.META.get('HTTP_REFERER', 'home'))

        cantidad = int(cantidad_str)

        usuario = request.user

        with transaction.atomic():
            carrito, created = Carrito.objects.get_or_create(
                usuario=usuario,
                defaults={'fecha_creacion': timezone.now()}
            )

            detalle, detalle_created = DetalleCarrito.objects.get_or_create(
                carrito=carrito,
                articulo=articulo,
                defaults={'cantidad': cantidad}
            )

            if not detalle_created:
                detalle.cantidad += cantidad
                detalle.save()

        messages.success(request, f'"{articulo.descripcion}" agregado correctamente al carrito.')

    except Exception as e:
        # Mostrar error completo para depuración
        messages.error(request, f'No se pudo agregar a su carrito, intente nuevamente. Error: {str(e)}')

    return redirect(request.META.get('HTTP_REFERER', 'home'))

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

    if request.method == "POST":
        form = ArticuloForm(request.POST, instance=articulo)

        if form.is_valid():
            form.save()
            messages.success(request, "Artículo actualizado correctamente.")
            return redirect("articulo_detail", articulo_id=articulo.articulo_id)
    else:
        form = ArticuloForm(instance=articulo)

    context = {
        "form": form,
    }
    return render(request, "core/articulos/form.html", context)

#@login_required
def articulo_create(request):
    """Vista para crear un nuevo artículo"""
    if request.method == "POST":
        form = ArticuloForm(request.POST)

        if form.is_valid():
            try:
                # Generar ID para el artículo
                articulo = form.save(commit=False)
                articulo.articulo_id = uuid.uuid4()
                articulo.save()

                messages.success(request, f'¡Artículo "{articulo.descripcion}"creado correctamente!')

                return redirect("articulo_detail", articulo_id=articulo.articulo_id)
            except Exception as e: 
                messages.error(request, f'Error al crear el artículo:{str(e)}')

        else: 
            messages.warning(request, 'Por favor corrija los errores en el formulario.')  
    else:
        form = ArticuloForm()

    context = {
        "form": form,
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

@login_required
def eliminar_detalle_carrito(request, detalle_id):
    detalle = get_object_or_404(DetalleCarrito, pk=detalle_id)

    # Validar que el detalle sea del carrito del usuario actual
    if detalle.carrito.usuario == request.user:
        detalle.delete()

    return redirect('vista_carrito')  # Redirige al carrito actualizado


def vista_carrito(request):
    usuario = request.user
    carrito = Carrito.objects.filter(usuario=usuario).order_by('-fecha_creacion').first()

    articulos_carrito = []
    promociones_aplicadas = []
    beneficios_promociones = []
    descuentos_aplicados = []
    total_descuento = Decimal('0')

    if carrito:
        detalles = DetalleCarrito.objects.filter(carrito=carrito).select_related('articulo', 'articulo__sucursal')

        # Construir lista de artículos del carrito
        for detalle in detalles:
            articulo = detalle.articulo
            articulos_carrito.append({
                'id': detalle.detalle_carrito_id,
                'codigo': articulo.codigo,
                'articulo': articulo,
                'sucursal': articulo.sucursal.nombre if articulo.sucursal else 'Sin sucursal',
                'cantidad': detalle.cantidad,
                'precio': articulo.precio,
                'total': articulo.precio * detalle.cantidad,
            })

        # Obtener cliente asociado
        cliente = Cliente.objects.filter(usuario=usuario).first()

        # Evaluar promociones usando la nueva función
        try:
            print(f"\n🛒 === EVALUANDO PROMOCIONES PARA CARRITO ===")
            print(f"👤 Usuario: {usuario.username}")
            print(f"🎯 Cliente: {cliente}")
            print(f"🏢 Empresa: {usuario.empresa}")
            print(f"🏪 Sucursal: {usuario.sucursal}")
            
            beneficios = evaluar_promociones(
                carrito_detalle=detalles,
                cliente=cliente,
                empresa=usuario.empresa,
                sucursal=usuario.sucursal
            )

            # Procesar promociones aplicadas
            promociones_aplicadas = beneficios.get('promociones_aplicadas', [])
            print(f"🎉 Promociones aplicadas: {len(promociones_aplicadas)}")
            
            # ✅ PROCESAR BONIFICACIONES CON INFORMACIÓN DE ESCALABILIDAD
            for bonificacion in beneficios.get('bonificaciones', []):
                beneficios_promociones.append({
                    'promocion': bonificacion['promocion'].descripcion,
                    'codigo': bonificacion['articulo'].codigo,
                    'descripcion': bonificacion['articulo'].descripcion,
                    'cantidad': bonificacion['cantidad'],
                    'valor': 0,  # Productos gratis
                    'tipo': 'bonificacion',
                    'escalable': bonificacion.get('escalable', False),
                    'veces_aplicable': bonificacion.get('veces_aplicable', 1)
                })
                
                print(f"🎁 Bonificación procesada: {bonificacion['cantidad']} x {bonificacion['articulo'].descripcion}")

            # ✅ PROCESAR DESCUENTOS CON INFORMACIÓN DE ESCALABILIDAD
            for descuento in beneficios.get('descuentos', []):
                # Calcular monto de descuento si no está calculado
                if descuento.get('monto_descuento', 0) == 0 and descuento.get('porcentaje', 0) > 0:
                    if descuento.get('tipo') == 'general':
                        # Descuento general sobre el total
                        total_carrito = sum(item['total'] for item in articulos_carrito)
                        monto_desc = total_carrito * (Decimal(str(descuento['porcentaje'])) / 100)
                    elif descuento.get('tipo') == 'porcentaje_producto' and descuento.get('articulo'):
                        # Descuento específico sobre un producto
                        for item in articulos_carrito:
                            if item['articulo'].articulo_id == descuento['articulo'].articulo_id:
                                monto_desc = item['total'] * (Decimal(str(descuento['porcentaje'])) / 100)
                                break
                        else:
                            monto_desc = 0
                    else:
                        monto_desc = Decimal(str(descuento.get('monto_descuento', 0)))
                else:
                    monto_desc = Decimal(str(descuento.get('monto_descuento', 0)))

                descuentos_aplicados.append({
                    'promocion': descuento['promocion'].descripcion,
                    'tipo': descuento.get('tipo', 'general'),
                    'porcentaje': descuento.get('porcentaje', 0),
                    'monto_descuento': float(monto_desc),
                    'descripcion': f"Descuento {descuento.get('porcentaje', 0)}% - {descuento['promocion'].descripcion}",
                    'escalable': descuento.get('escalable', False),
                    'veces_aplicable': descuento.get('veces_aplicable', 1)
                })
                
                total_descuento += monto_desc
                print(f"💰 Descuento procesado: {descuento.get('porcentaje', 0)}% = S/{float(monto_desc)}")

            # Mostrar errores si los hay (para debugging)
            if beneficios.get('errores'):
                for error in beneficios['errores']:
                    messages.warning(request, f"Error en promociones: {error}")
                    print(f"⚠️ Error: {error}")

        except Exception as e:
            error_msg = f"Error al evaluar promociones: {str(e)}"
            messages.error(request, error_msg)
            print(f"🚨 {error_msg}")
            import traceback
            traceback.print_exc()

    # Calcular totales
    subtotal = sum(item['total'] for item in articulos_carrito)
    total_venta = subtotal - total_descuento

    # ✅ AGREGAR INFORMACIÓN DE DEBUG PARA ESCALABILIDAD
    print(f"\n🛒 === RESUMEN FINAL DEL CARRITO ===")
    print(f"   📦 Productos: {len(articulos_carrito)}")
    print(f"   🎉 Promociones: {len(promociones_aplicadas)}")
    print(f"   🎁 Bonificaciones: {len(beneficios_promociones)}")
    for beneficio in beneficios_promociones:
        escalable_info = f" (Escalable {beneficio['veces_aplicable']}x)" if beneficio['escalable'] else ""
        print(f"      - {beneficio['descripcion']}: {beneficio['cantidad']} unidades{escalable_info}")
    print(f"   💰 Descuentos: {len(descuentos_aplicados)}")
    for descuento in descuentos_aplicados:
        escalable_info = f" (Escalable {descuento['veces_aplicable']}x)" if descuento['escalable'] else ""
        print(f"      - {descuento['descripcion']}: S/{descuento['monto_descuento']}{escalable_info}")
    print(f"   💵 Subtotal: S/{subtotal}")
    print(f"   🔻 Total descuentos: S/{total_descuento}")
    print(f"   💲 TOTAL FINAL: S/{total_venta}")
    print(f"=== FIN RESUMEN ===\n")

    return render(request, 'core/carrito/vistacarrito.html', {
        'articulos_carrito': articulos_carrito,
        'usuario_nombre': usuario.username,
        'subtotal': subtotal,
        'total_descuento': total_descuento,
        'total_venta': total_venta,
    })
