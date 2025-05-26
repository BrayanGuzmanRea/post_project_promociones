from datetime import timezone
from decimal import Decimal
import uuid
from django.shortcuts import render, redirect
from .models import Bonificacion, BonificacionAplicada, Carrito, Cliente, Descuento, DescuentoAplicado, DetalleCarrito, DetallePedido, GrupoProveedor, LineaArticulo, Pedido, PromocionProducto, StockSucursal, Usuario, Rol, VerificacionProducto
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
            
            # Procesar bonificaciones
            for bonificacion in beneficios.get('bonificaciones', []):
                beneficios_promociones.append({
                    'promocion': bonificacion['promocion'].nombre,
                    'codigo': bonificacion['articulo'].codigo,
                    'descripcion': bonificacion['articulo'].descripcion,
                    'cantidad': bonificacion['cantidad'],
                    'valor': 0,  # Productos gratis
                    'tipo': 'bonificacion'
                })

            # Procesar descuentos
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
                    'descripcion': f"Descuento {descuento.get('porcentaje', 0)}% - {descuento['promocion'].nombre}"
                })
                
                total_descuento += monto_desc

            # Mostrar errores si los hay (para debugging)
            if beneficios.get('errores'):
                for error in beneficios['errores']:
                    messages.warning(request, f"Error en promociones: {error}")

        except Exception as e:
            messages.error(request, f"Error al evaluar promociones: {str(e)}")

    # Calcular totales
    subtotal = sum(item['total'] for item in articulos_carrito)
    total_venta = subtotal - total_descuento

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





@login_required
def registrar_promocion(request):
    form = PromocionForm()
    return render(request, 'core/promociones/registrar_promocion.html', {'form': form})

def obtener_sucursales_por_empresa(request):
    empresa_id = request.GET.get('empresa_id')
    if not empresa_id:
        return JsonResponse([], safe=False)
    sucursales = Sucursal.objects.filter(empresa_id=empresa_id).values('sucursal_id', 'nombre')
    return JsonResponse(list(sucursales), safe=False)

def obtener_marcas_por_empresa(request):
    empresa_id = request.GET.get('empresa_id')
    if not empresa_id:
        return JsonResponse([], safe=False)

    marcas = GrupoProveedor.objects.filter(empresa_id=empresa_id, estado=1).values('grupo_proveedor_id', 'nombre')
    return JsonResponse(list(marcas), safe=False)

def obtener_lineas_por_marca(request):
    marca_id = request.GET.get('marca_id')
    if not marca_id:
        return JsonResponse([], safe=False)

    lineas = LineaArticulo.objects.filter(grupo_proveedor_id=marca_id).values('linea_articulo_id', 'nombre')
    return JsonResponse(list(lineas), safe=False)   

def obtener_articulos_por_sucursal(request):
    sucursal_id = request.GET.get('sucursal_id')

    try:
        sucursal_id = int(sucursal_id)
    except (ValueError, TypeError):
        return JsonResponse([], safe=False)

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


def registrar_promocion(request):
    if request.method == 'POST':
        form = PromocionForm(request.POST)
        empresa_id = request.POST.get('empresa')

        if empresa_id:
            form.fields['sucursal'].queryset = Sucursal.objects.filter(empresa_id=empresa_id)

        if form.is_valid():
            try:
                with transaction.atomic():
                    promocion = form.save()

                    # Asignar marca y línea si fueron seleccionadas
                    marca_id = request.POST.get('grupo_proveedor')
                    linea_id = request.POST.get('linea_articulo')
                    if marca_id:
                        promocion.grupo_proveedor_id = marca_id
                    if linea_id:
                        promocion.linea_articulo_id = linea_id
                    promocion.save()

                    # 🎁 Bonificaciones
                    productos_bonificados = request.POST.getlist('productos_bonificados[]')
                    cantidades_bonificadas = request.POST.getlist('cantidad_bonificada[]')
                    for art_id, cantidad in zip(productos_bonificados, cantidades_bonificadas):
                        if art_id and cantidad:
                            Bonificacion.objects.create(
                                promocion=promocion,
                                articulo_id=art_id,
                                cantidad=int(cantidad)
                            )

                    # 🧩 Condición por cantidad
                    if promocion.tipo_condicion == 'cantidad':
                        productos_ids = request.POST.getlist('productos_condicion')
                        for producto_id in productos_ids:
                            base = f"productos_configurados[{producto_id}]"
                            tipo_seleccion = request.POST.get(f"{base}[tipo_seleccion]")
                            cantidades_min = request.POST.getlist(f"{base}[cantidad_min][]")
                            cantidades_max = request.POST.getlist(f"{base}[cantidad_max][]")
                            valores = request.POST.getlist(f"{base}[valor][]")

                            for cantidad_min, cantidad_max, valor in zip(cantidades_min, cantidades_max, valores):
                                if any([cantidad_min, cantidad_max, valor]):
                                    PromocionProducto.objects.create(
                                        promocion=promocion,
                                        articulo_id=producto_id,
                                        cantidad_min=cantidad_min or None,
                                        cantidad_max=cantidad_max or None,
                                        tipo_seleccion=tipo_seleccion or None,
                                        valor=valor or None,
                                    )

                                    # Registrar como descuento si es tipo porcentaje
                                    if tipo_seleccion == 'porcentaje' and valor:
                                        Descuento.objects.create(
                                            promocion=promocion,
                                            valor_minimo=cantidad_min or None,
                                            valor_maximo=cantidad_max or None,
                                            porcentaje=valor
                                        )

                    # 💸 Condición por monto
                    if promocion.tipo_condicion == 'monto':
                        minimos = request.POST.getlist('rangos_descuento[minimo]')
                        maximos = request.POST.getlist('rangos_descuento[maximo]')
                        porcentajes = request.POST.getlist('rangos_descuento[porcentaje]')
                        for minimo, maximo, porcentaje in zip(minimos, maximos, porcentajes):
                            if porcentaje:
                                Descuento.objects.create(
                                    promocion=promocion,
                                    valor_minimo=minimo or None,
                                    valor_maximo=maximo or None,
                                    porcentaje=porcentaje
                                )

                    # ✅ Registro adicional si tipo de beneficio es "Descuento"
                    tipo_beneficio = request.POST.get('tipo_beneficio')
                    porcentaje_directo = request.POST.get('porcentaje_descuento')
                    print("🧩 tipo_beneficio recibido:", tipo_beneficio)
                    print("→ Porcentaje descuento directo:", porcentaje_directo)

                    if tipo_beneficio == '2' or str(promocion.tipo_beneficio_id) == '2':
                        if porcentaje_directo:
                            Descuento.objects.create(
                                promocion=promocion,
                                porcentaje=porcentaje_directo
                            )

                    # 🔐 Registro de productos para verificación
                    productos_condicion_ids = request.POST.getlist('productos_condicion')
                    for producto_id in productos_condicion_ids:
                        VerificacionProducto.objects.create(
                            articulo_id=producto_id,
                            promocion=promocion
                        )

                    return redirect('home')

            except Exception as e:
                print("❌ ERROR:", e)
                messages.error(request, f"Error al registrar la promoción: {str(e)}")
        else:
            print("❌ FORMULARIO NO VÁLIDO:", form.errors)
            messages.error(request, "Error en el formulario. Verifique los datos ingresados.")
    else:
        form = PromocionForm()

    return render(request, 'core/promociones/registrar_promocion.html', {'form': form})



def guardar_beneficios_en_pedido(pedido, beneficios):
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
        DescuentoAplicado.objects.create(
            pedido=pedido,
            promocion=desc['promocion'],
            porcentaje_descuento=desc['porcentaje'],
            monto_descuento=desc['monto_descuento']
        )
