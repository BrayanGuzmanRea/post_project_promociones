from datetime import timezone
from decimal import Decimal
import uuid
from django.shortcuts import render, redirect
from .models import Bonificacion, BonificacionAplicada, Carrito, Cliente, Descuento, DescuentoAplicado, DetalleCarrito, DetallePedido, GrupoProveedor, LineaArticulo, Pedido, Promocion, PromocionProducto, StockSucursal, Usuario, Rol, VerificacionProducto
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

#Funcion sin usooo...
# def vendedores_list(request):
#     try:
#         rol_vendedor = Rol.objects.get(nombre='Vendedor')  # Ajusta el nombre si es distinto
#         vendedores = Usuario.objects.filter(perfil=rol_vendedor)
#     except Rol.DoesNotExist:
#         vendedores = Usuario.objects.none()

#     return render(request, 'core/vendedores/list.html', {'vendedores': vendedores})

#Funcion sin usooo...
# def usuario_create(request):
#     if request.method == 'POST':
#         form = UsuarioForm(request.POST)
#         if form.is_valid():
#             form.save()
#             messages.success(request, 'Usuario registrado correctamente')
#             return redirect('usuarios_list')  # Cambia por la URL que quieras
#     else:
#         form = UsuarioForm()
#     return render(request, 'core/usuarios/form.html', {'form': form})


# def usuarios_list(request):
#     usuarios = Usuario.objects.all()
#     return render(request, 'core/usuarios/list.html', {'usuarios': usuarios})

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


#Desde aqui inicia los cambios de la vista de los articulos


# def vista_carrito(request):
#     usuario = request.user

#     # Buscar el carrito activo del usuario, si no hay, carrito es None
#     carrito = Carrito.objects.filter(usuario=usuario).order_by('-fecha_creacion').first()

#     articulos_carrito = []

#     if carrito:
#         detalles = DetalleCarrito.objects.filter(carrito=carrito).select_related('articulo', 'articulo__sucursal')

#         for detalle in detalles:
#             articulo = detalle.articulo
#             articulos_carrito.append({
#                 'codigo': articulo.codigo,
#                 'articulo': articulo,
#                 'sucursal': articulo.sucursal.nombre if articulo.sucursal else 'Sin sucursal',
#                 'cantidad': detalle.cantidad,
#                 'precio': articulo.precio,
#                 'total': articulo.precio * detalle.cantidad,
#             })
    
#     total_venta = sum(item['total'] for item in articulos_carrito)

#     return render(request, 'core/carrito/vistacarrito.html', {
#         'articulos_carrito': articulos_carrito,
#         'usuario_nombre': usuario.username,
#         'total_venta': total_venta,
#     })



# def vista_carrito(request):
#     usuario = request.user
#     carrito = Carrito.objects.filter(usuario=usuario).order_by('-fecha_creacion').first()

#     articulos_carrito = []
#     promociones_aplicadas = []
#     beneficios_promociones = []

#     if carrito:
#         detalles = DetalleCarrito.objects.filter(carrito=carrito).select_related('articulo', 'articulo__sucursal')

#         for detalle in detalles:
#             articulo = detalle.articulo
#             articulos_carrito.append({
#                 'id': detalle.detalle_carrito_id,
#                 'codigo': articulo.codigo,
#                 'articulo': articulo,
#                 'sucursal': articulo.sucursal.nombre if articulo.sucursal else 'Sin sucursal',
#                 'cantidad': detalle.cantidad,
#                 'precio': articulo.precio,
#                 'total': articulo.precio * detalle.cantidad,
#             })

#         # Obtener cliente asociado
#         cliente = Cliente.objects.filter(usuario=usuario).first()

#         # Llamar a evaluar_promociones con detalles reales y cliente
#         #beneficios = evaluar_promociones(
#          #   carrito_detalle=detalles,
#           #  cliente=cliente,
#            # empresa=usuario.empresa,
#             #sucursal=usuario.sucursal
#         #)

#         # promociones_aplicadas son las promociones que generan bonificaciones y descuentos
#         # promociones_aplicadas = []
#         # for bonificacion in beneficios.get('bonificaciones', []):
#         #     promo = bonificacion['promocion']
#         #     if promo not in promociones_aplicadas:
#         #         promociones_aplicadas.append(promo)
#         #     beneficios_promociones.append({
#         #         'codigo': bonificacion['articulo'].codigo,
#         #         'descripcion': bonificacion['articulo'].descripcion,
#         #         'cantidad': bonificacion['cantidad'],
#         #         'valor': 0,  # Podrías poner valor monetario si es necesario
#         #     })

#         # for descuento in beneficios.get('descuentos', []):
#         #     promo = descuento['promocion']
#         #     if promo not in promociones_aplicadas:
#         #         promociones_aplicadas.append(promo)
#         #     # Si quieres mostrar descuentos en beneficios, agregalos aquí

#     total_venta = sum(item['total'] for item in articulos_carrito)

#     return render(request, 'core/carrito/vistacarrito.html', {
#         'articulos_carrito': articulos_carrito,
#         'usuario_nombre': usuario.username,
#         'total_venta': total_venta,
#         'promociones_aplicadas': promociones_aplicadas,
#         'beneficios_promociones': beneficios_promociones
#     })


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

        # Evaluar promociones
        try:
            beneficios = evaluar_promociones(
                carrito_detalle=detalles,
                cliente=cliente,
                empresa=usuario.empresa,
                sucursal=usuario.sucursal
            )

            # Procesar promociones aplicadas
            promociones_aplicadas = beneficios.get('promociones_aplicadas', [])
            
            # ✅ PROCESAR BONIFICACIONES CON INFORMACIÓN DE ESCALABILIDAD
            for bonificacion in beneficios.get('bonificaciones', []):
                beneficios_promociones.append({
                    'promocion': bonificacion['promocion'].nombre,
                    'codigo': bonificacion['articulo'].codigo,
                    'descripcion': bonificacion['articulo'].descripcion,
                    'cantidad': bonificacion['cantidad'],
                    'valor': 0,  # Productos gratis
                    'tipo': 'bonificacion',
                    'escalable': bonificacion.get('escalable', False),  # ← NUEVO
                    'veces_aplicable': bonificacion.get('veces_aplicable', 1)  # ← NUEVO
                })

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
                    'promocion': descuento['promocion'].nombre,
                    'tipo': descuento.get('tipo', 'general'),
                    'porcentaje': descuento.get('porcentaje', 0),
                    'monto_descuento': float(monto_desc),
                    'descripcion': f"Descuento {descuento.get('porcentaje', 0)}% - {descuento['promocion'].nombre}",
                    'escalable': descuento.get('escalable', False),  # ← NUEVO
                    'veces_aplicable': descuento.get('veces_aplicable', 1)  # ← NUEVO
                })
                
                total_descuento += monto_desc

            # Mostrar errores si los hay (para debugging)
            if beneficios.get('errores'):
                for error in beneficios['errores']:
                    messages.warning(request, f"Error en promociones: {error}")

        except Exception as e:
            messages.error(request, f"Error al evaluar promociones: {str(e)}")
            print(f"🚨 Error en vista_carrito: {str(e)}")  # Para debug

    # Calcular totales
    subtotal = sum(item['total'] for item in articulos_carrito)
    total_venta = subtotal - total_descuento

    # ✅ AGREGAR INFORMACIÓN DE DEBUG PARA ESCALABILIDAD
    print(f"🛒 Carrito procesado:")
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

    return render(request, 'core/carrito/vistacarrito.html', {
        'articulos_carrito': articulos_carrito,
        'usuario_nombre': usuario.username,
        'subtotal': subtotal,
        'total_descuento': total_descuento,
        'total_venta': total_venta,
        'promociones_aplicadas': promociones_aplicadas,
        'beneficios_promociones': beneficios_promociones,
        'descuentos_aplicados': descuentos_aplicados
    })

# Agregar estas funciones a tu views.py si no las tienes

@login_required
def obtener_sucursales_por_empresa(request):
    """API para obtener sucursales filtradas por empresa"""
    empresa_id = request.GET.get('empresa_id')
    if not empresa_id:
        return JsonResponse([], safe=False)
    
    try:
        sucursales = Sucursal.objects.filter(empresa_id=empresa_id).values('sucursal_id', 'nombre')
        return JsonResponse(list(sucursales), safe=False)
    except Exception as e:
        return JsonResponse([], safe=False)

def obtener_marcas_por_empresa(request):
    """API para obtener marcas/proveedores filtrados por empresa"""
    empresa_id = request.GET.get('empresa_id')
    if not empresa_id:
        return JsonResponse([], safe=False)

    try:
        marcas = GrupoProveedor.objects.filter(
            empresa_id=empresa_id, 
            estado=1
        ).values('grupo_proveedor_id', 'nombre')
        return JsonResponse(list(marcas), safe=False)
    except Exception as e:
        return JsonResponse([], safe=False)

def obtener_lineas_por_marca(request):
    """API para obtener líneas de artículos filtradas por marca"""
    marca_id = request.GET.get('marca_id')
    if not marca_id:
        return JsonResponse([], safe=False)

    try:
        lineas = LineaArticulo.objects.filter(
            grupo_proveedor_id=marca_id
        ).values('linea_articulo_id', 'nombre')
        return JsonResponse(list(lineas), safe=False)
    except Exception as e:
        return JsonResponse([], safe=False)   

def obtener_articulos_por_sucursal(request):
    """API para obtener artículos filtrados por sucursal"""
    sucursal_id = request.GET.get('sucursal_id')

    try:
        sucursal_id = int(sucursal_id)
    except (ValueError, TypeError):
        return JsonResponse([], safe=False)

    try:
        articulos = Articulo.objects.filter(sucursal_id=sucursal_id)

        data = [
            {
                'articulo_id': str(art.articulo_id),
                'codigo': art.codigo,
                'descripcion': art.descripcion or ''
            }
            for art in articulos
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse([], safe=False)


def procesar_pedido(request):
    """
    Nueva vista para procesar el pedido y guardar los beneficios aplicados
    """
    if request.method != 'POST':
        return redirect('vista_carrito')
    
    usuario = request.user
    carrito = Carrito.objects.filter(usuario=usuario).order_by('-fecha_creacion').first()
    
    if not carrito:
        messages.error(request, "No tienes productos en tu carrito")
        return redirect('vista_carrito')
    
    try:
        with transaction.atomic():
            # Obtener datos necesarios
            detalles = DetalleCarrito.objects.filter(carrito=carrito).select_related('articulo')
            cliente = Cliente.objects.filter(usuario=usuario).first()
            
            if not cliente:
                messages.error(request, "No se encontró información del cliente")
                return redirect('vista_carrito')
            
            # Evaluar promociones una vez más para asegurar consistencia
            beneficios = evaluar_promociones(
                carrito_detalle=detalles,
                cliente=cliente,
                empresa=usuario.empresa,
                sucursal=usuario.sucursal
            )
            
            # Calcular totales
            subtotal = sum(detalle.articulo.precio * detalle.cantidad for detalle in detalles)
            total_descuento = Decimal('0')
            
            for descuento in beneficios.get('descuentos', []):
                if descuento.get('monto_descuento'):
                    total_descuento += Decimal(str(descuento['monto_descuento']))
                elif descuento.get('porcentaje'):
                    # Calcular descuento sobre subtotal
                    desc_monto = subtotal * (Decimal(str(descuento['porcentaje'])) / 100)
                    total_descuento += desc_monto
            
            total_final = subtotal - total_descuento
            
            # Crear el pedido
            pedido = Pedido.objects.create(
                cliente=cliente,
                sucursal=usuario.sucursal or detalles.first().articulo.sucursal,
                usuario=usuario,
                fecha=timezone.now().date(),
                total=total_final
            )
            
            # Crear detalles del pedido
            for detalle in detalles:
                DetallePedido.objects.create(
                    pedido=pedido,
                    articulo=detalle.articulo,
                    cantidad=detalle.cantidad,
                    precio_unitario=detalle.articulo.precio
                )
            
            # Guardar beneficios aplicados
            guardar_beneficios_en_pedido(pedido, beneficios)
            
            # Limpiar carrito
            carrito.delete()
            
            messages.success(request, f"Pedido #{pedido.pedido_id} creado exitosamente")
            return redirect('home')  # o redirigir a vista de pedidos
            
    except Exception as e:
        messages.error(request, f"Error al procesar el pedido: {str(e)}")
        return redirect('vista_carrito')


def guardar_beneficios_en_pedido(pedido, beneficios):
    """
    Guarda los beneficios aplicados en el pedido (función ya existente actualizada)
    """
    # Guardar bonificaciones
    for bon in beneficios.get('bonificaciones', []):
        BonificacionAplicada.objects.create(
            pedido=pedido,
            promocion=bon['promocion'],
            articulo=bon['articulo'],
            cantidad=bon['cantidad']
        )
    
    # Guardar descuentos
    for desc in beneficios.get('descuentos', []):
        # Calcular monto si no está calculado
        monto_descuento = desc.get('monto_descuento', 0)
        if monto_descuento == 0 and desc.get('porcentaje'):
            # Necesitarías el monto base para calcular
            monto_descuento = 0  # Por ahora, mejorar según necesidades
        
        DescuentoAplicado.objects.create(
            pedido=pedido,
            promocion=desc['promocion'],
            porcentaje_descuento=desc.get('porcentaje', 0),
            monto_descuento=monto_descuento
        )





def registrar_promocion(request):
    if request.method == 'POST':
        return procesar_nueva_promocion(request)
    else:
        form = PromocionForm()
        return render(request, 'core/promociones/registrar_promocion.html', {'form': form})

def procesar_nueva_promocion(request):
    """
    Procesa el nuevo formulario paso a paso de promociones
    """
    try:
        with transaction.atomic():
            # PASO 1: Crear la promoción base
            promocion_data = extraer_datos_promocion_base(request.POST)
            promocion = crear_promocion_base(promocion_data)
            
            # PASO 2: Configurar filtros de productos
            configurar_filtros_productos(request.POST, promocion)
            
            # PASO 3: Configurar condiciones
            configurar_condiciones_promocion(request.POST, promocion)
            
            # PASO 4: Configurar beneficios
            configurar_beneficios_promocion(request.POST, promocion)
            
            messages.success(request, f'Promoción "{promocion.nombre}" creada exitosamente')
            return redirect('home')
            
    except Exception as e:
        print(f"❌ ERROR al procesar promoción: {str(e)}")
        messages.error(request, f"Error al registrar la promoción: {str(e)}")
        form = PromocionForm()
        return render(request, 'core/promociones/registrar_promocion.html', {'form': form})

def extraer_datos_promocion_base(post_data):
    """
    Extrae los datos básicos de la promoción del formulario
    """
    return {
        'nombre': post_data.get('nombre', '').strip(),
        'empresa_id': post_data.get('empresa'),
        'sucursal_id': post_data.get('sucursal') if post_data.get('sucursal') else None,
        'canal_cliente_id': post_data.get('canal_cliente'),
        'fecha_inicio': post_data.get('fecha_inicio'),
        'fecha_fin': post_data.get('fecha_fin'),
        'tipo_condicion': post_data.get('tipo_condicion'),
        'tipo_beneficio_id': post_data.get('tipo_beneficio'),
        'escalable': post_data.get('promocion_escalable') == '1',  # ← NUEVO CAMPO
        'estado': post_data.get('estado', 1)
    }

def crear_promocion_base(data):
    """
    Crea el registro base de la promoción
    """
    promocion = Promocion.objects.create(
        nombre=data['nombre'],
        empresa_id=data['empresa_id'],
        sucursal_id=data['sucursal_id'],
        canal_cliente_id=data['canal_cliente_id'],
        fecha_inicio=data['fecha_inicio'],
        fecha_fin=data['fecha_fin'],
        tipo_condicion=data['tipo_condicion'],
        tipo_beneficio_id=data['tipo_beneficio_id'],
        escalable=data['escalable'],  # ← NUEVO CAMPO
        estado=data['estado']
    )
    escalable_text = " (ESCALABLE)" if data['escalable'] else ""
    print(f"✅ Promoción base creada: {promocion.nombre}{escalable_text}")
    return promocion

def configurar_filtros_productos(post_data, promocion):
    """
    Configura los filtros de productos (línea/marca o productos específicos)
    """
    tipo_filtro = post_data.get('tipo_filtro', 'productos_especificos')
    
    if tipo_filtro == 'linea_marca':
        # Caso: Promoción para línea y marca específica (Casos 2, 5 del PDF)
        marca_id = post_data.get('grupo_proveedor')
        linea_id = post_data.get('linea_articulo')
        
        if marca_id:
            promocion.grupo_proveedor_id = marca_id
            print(f"✅ Filtro por marca: {marca_id}")
        
        if linea_id:
            promocion.linea_articulo_id = linea_id
            print(f"✅ Filtro por línea: {linea_id}")
        
        promocion.save()
        
    else:
        # Caso: Productos específicos (Casos 1, 3, 4, etc.)
        productos_condicion = post_data.getlist('productos_condicion')
        productos_validos = [p for p in productos_condicion if p]
        
        for producto_id in productos_validos:
            VerificacionProducto.objects.create(
                articulo_id=producto_id,
                promocion=promocion
            )
            print(f"✅ Producto condición agregado: {producto_id}")

def configurar_condiciones_promocion(post_data, promocion):
    """
    Configura las condiciones de activación de la promoción
    """
    tipo_condicion = promocion.tipo_condicion
    
    if tipo_condicion == 'cantidad':
        configurar_condiciones_cantidad(post_data, promocion)
    elif tipo_condicion == 'monto':
        configurar_condiciones_monto(post_data, promocion)

def configurar_condiciones_cantidad(post_data, promocion):
    """
    Configura condiciones por cantidad (Casos 1, 3, 4, 7, 8 del PDF)
    """
    productos_condicion = post_data.getlist('productos_condicion')
    productos_validos = [p for p in productos_condicion if p]
    
    if len(productos_validos) == 1:
        # Un solo producto: configuración detallada con rangos
        producto_id = productos_validos[0]
        configurar_rangos_cantidad_producto(post_data, promocion, producto_id)
    else:
        # Múltiples productos: promoción por combinación (Caso 13)
        print(f"✅ Promoción por combinación de {len(productos_validos)} productos")
        # Los productos ya se guardaron en VerificacionProducto

def configurar_rangos_cantidad_producto(post_data, promocion, producto_id):
    """
    Configura rangos de cantidad para un producto específico
    """
    tipo_beneficio = post_data.get('tipo_beneficio_cantidad', '')
    
    # Obtener todos los rangos configurados
    cantidades_min = post_data.getlist('cantidad_min')
    cantidades_max = post_data.getlist('cantidad_max')
    valores_beneficio = post_data.getlist('valor_beneficio')
    
    for i, cantidad_min in enumerate(cantidades_min):
        if not cantidad_min:
            continue
            
        cantidad_max = cantidades_max[i] if i < len(cantidades_max) else None
        valor = valores_beneficio[i] if i < len(valores_beneficio) else None
        
        if not valor:
            continue
        
        # Crear registro en PromocionProducto
        promocion_producto = PromocionProducto.objects.create(
            promocion=promocion,
            articulo_id=producto_id,
            cantidad_min=int(cantidad_min),
            cantidad_max=int(cantidad_max) if cantidad_max else None,
            tipo_seleccion=tipo_beneficio,
            valor=valor
        )
        
        print(f"✅ Rango cantidad creado: {cantidad_min}-{cantidad_max or '∞'} = {valor}")
        
        # Si es porcentaje, crear también registro en Descuento
        if tipo_beneficio == 'porcentaje_descuento':
            Descuento.objects.create(
                promocion=promocion,
                valor_minimo=cantidad_min,
                valor_maximo=cantidad_max,
                porcentaje=valor
            )
            print(f"✅ Descuento por cantidad creado: {valor}%")

def configurar_condiciones_monto(post_data, promocion):
    """
    Configura condiciones por monto (Casos 2, 5, 6, 9, 10, 11 del PDF)
    """
    montos_min = post_data.getlist('monto_minimo')
    montos_max = post_data.getlist('monto_maximo')
    porcentajes = post_data.getlist('porcentaje_descuento')
    
    for i, monto_min in enumerate(montos_min):
        if not monto_min or not porcentajes[i]:
            continue
            
        monto_max = montos_max[i] if i < len(montos_max) and montos_max[i] else None
        porcentaje = porcentajes[i]
        
        Descuento.objects.create(
            promocion=promocion,
            valor_minimo=monto_min,
            valor_maximo=monto_max,
            porcentaje=porcentaje
        )
        
        print(f"✅ Descuento por monto creado: S/{monto_min}-{monto_max or '∞'} = {porcentaje}%")

def configurar_beneficios_promocion(post_data, promocion):
    """
    Configura los beneficios de la promoción
    """
    tipo_beneficio_obj = promocion.tipo_beneficio
    if not tipo_beneficio_obj:
        return
    
    tipo_beneficio_nombre = tipo_beneficio_obj.nombre.lower()
    
    if 'bonificación' in tipo_beneficio_nombre and 'ambos' not in tipo_beneficio_nombre:
        # Solo bonificación
        configurar_bonificaciones_simples(post_data, promocion)
    elif 'descuento' in tipo_beneficio_nombre and 'ambos' not in tipo_beneficio_nombre:
        # Solo descuento adicional
        configurar_descuento_adicional(post_data, promocion)
    elif 'ambos' in tipo_beneficio_nombre:
        # Bonificación + Descuento (Casos 9, 12 del PDF)
        configurar_bonificaciones_ambos(post_data, promocion)
        configurar_descuento_adicional_ambos(post_data, promocion)

def configurar_bonificaciones_simples(post_data, promocion):
    """
    Configura bonificaciones simples
    """
    productos_bonificados = post_data.getlist('productos_bonificados[]')
    cantidades_bonificadas = post_data.getlist('cantidad_bonificada[]')
    
    for producto_id, cantidad in zip(productos_bonificados, cantidades_bonificadas):
        if producto_id and cantidad:
            Bonificacion.objects.create(
                promocion=promocion,
                articulo_id=producto_id,
                cantidad=int(cantidad)
            )
            print(f"✅ Bonificación creada: {cantidad} unidades de producto {producto_id}")

def configurar_bonificaciones_ambos(post_data, promocion):
    """
    Configura bonificaciones para tipo "ambos"
    """
    productos_bonificados = post_data.getlist('productos_bonificados_ambos[]')
    cantidades_bonificadas = post_data.getlist('cantidad_bonificada_ambos[]')
    
    for producto_id, cantidad in zip(productos_bonificados, cantidades_bonificadas):
        if producto_id and cantidad:
            Bonificacion.objects.create(
                promocion=promocion,
                articulo_id=producto_id,
                cantidad=int(cantidad)
            )
            print(f"✅ Bonificación (ambos) creada: {cantidad} unidades de producto {producto_id}")

def configurar_descuento_adicional(post_data, promocion):
    """
    Configura descuento adicional general
    """
    porcentaje_descuento = post_data.get('porcentaje_descuento')
    
    if porcentaje_descuento:
        Descuento.objects.create(
            promocion=promocion,
            porcentaje=porcentaje_descuento
        )
        print(f"✅ Descuento adicional creado: {porcentaje_descuento}%")

def configurar_descuento_adicional_ambos(post_data, promocion):
    """
    Configura descuento adicional para tipo "ambos"
    """
    porcentaje_descuento = post_data.get('porcentaje_descuento_ambos')
    
    if porcentaje_descuento:
        Descuento.objects.create(
            promocion=promocion,
            porcentaje=porcentaje_descuento
        )
        print(f"✅ Descuento adicional (ambos) creado: {porcentaje_descuento}%")

# Función auxiliar para debugging
def imprimir_datos_formulario(post_data):
    """
    Función para debugging - imprime todos los datos del formulario
    """
    print("\n=== DATOS DEL FORMULARIO ===")
    for key, value in post_data.items():
        if isinstance(value, list):
            print(f"{key}: {value}")
        else:
            print(f"{key}: {value}")
    print("=== FIN DATOS FORMULARIO ===\n")