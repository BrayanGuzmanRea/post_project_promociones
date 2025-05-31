from datetime import timezone
from decimal import Decimal
import uuid
from django.shortcuts import render, redirect
from .models import ProductosBeneficios, BonificacionAplicada, Carrito, Cliente, DescuentoAplicado, DetalleCarrito, DetallePedido, GrupoProveedor, LineaArticulo, Pedido, Promocion, Rango, ProductoBonificadoRango, Beneficio, VerificacionProducto
from django.contrib import messages
from .forms import PromocionForm
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.core.paginator import Paginator
from .forms import ArticuloForm
from core.models import Empresa, Sucursal, Articulo

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone

# Necesario para realizar las promociones
from core.promociones import evaluar_promociones

# Este sera para trabajar por medio de insomia
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
import json

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
            beneficios = evaluar_promociones(
                carrito_detalle=detalles,
                cliente=cliente,
                empresa=usuario.empresa,
                sucursal=usuario.sucursal
            )

            # Procesar promociones aplicadas
            promociones_aplicadas = beneficios.get('promociones_aplicadas', [])
            
            # PROCESAR BONIFICACIONES CON INFORMACIÓN DE ESCALABILIDAD
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
                
            # PROCESAR DESCUENTOS CON INFORMACIÓN DE ESCALABILIDAD
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

    # AGREGAR INFORMACIÓN DE DEBUG PARA ESCALABILIDAD
    for beneficio in beneficios_promociones:
        escalable_info = f" (Escalable {beneficio['veces_aplicable']}x)" if beneficio['escalable'] else ""
        print(f"      - {beneficio['descripcion']}: {beneficio['cantidad']} unidades{escalable_info}")
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

def obtener_sucursales_por_empresa(request):
    empresa_id = request.GET.get('empresa_id')
    if not empresa_id:
        return JsonResponse([], safe=False)
    
    try:
        sucursales = Sucursal.objects.filter(empresa_id=empresa_id).values('sucursal_id', 'nombre')
        return JsonResponse(list(sucursales), safe=False)
    except Exception as e:
        return JsonResponse([], safe=False)

def obtener_marcas_por_empresa(request):
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
                    desc_monto = subtotal * (Decimal(str(descuento['porcentaje'])) / 100)
                    total_descuento += desc_monto
            
            total_final = subtotal - total_descuento
            
            pedido = Pedido.objects.create(
                cliente=cliente,
                sucursal=usuario.sucursal or detalles.first().articulo.sucursal,
                usuario=usuario,
                fecha=timezone.now().date(),
                total=total_final
            )
            
            for detalle in detalles:
                DetallePedido.objects.create(
                    pedido=pedido,
                    articulo=detalle.articulo,
                    cantidad=detalle.cantidad,
                    precio_unitario=detalle.articulo.precio
                )
            
            guardar_beneficios_en_pedido(pedido, beneficios)
            
            # Limpiar carrito
            carrito.delete()
            
            messages.success(request, f"Pedido #{pedido.pedido_id} creado exitosamente")
            return redirect('home')  # o redirigir a vista de pedidos
            
    except Exception as e:
        messages.error(request, f"Error al procesar el pedido: {str(e)}")
        return redirect('vista_carrito')


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
        monto_descuento = desc.get('monto_descuento', 0)
        if monto_descuento == 0 and desc.get('porcentaje'):
            monto_descuento = 0  # Por ahora, mejorar según necesidades
        
        DescuentoAplicado.objects.create(
            pedido=pedido,
            promocion=desc['promocion'],
            porcentaje_descuento=desc.get('porcentaje', 0),
            monto_descuento=monto_descuento
        )


# Apartir de aca inicia lo que tiene que ver con registrar la promocion
def registrar_promocion(request):
    if request.method == 'POST':
        return procesar_nueva_promocion(request)
    else:
        form = PromocionForm()
        return render(request, 'core/promociones/registrar_promocion.html', {'form': form})

def procesar_nueva_promocion(request):    
    descripcion = request.POST.get('descripcion', '').strip()
 
    if not descripcion:
        messages.error(request, "La descripción es obligatoria")
        form = PromocionForm()
        return render(request, 'core/promociones/registrar_promocion.html', {'form': form})
    
    try:
        with transaction.atomic():            
            # CREAR LA PROMOCIÓN BASE 
            promocion = Promocion.objects.create(
                descripcion=descripcion,
                empresa_id=request.POST.get('empresa'),
                sucursal_id=request.POST.get('sucursal') if request.POST.get('sucursal') else None,
                canal_cliente_id=request.POST.get('canal_cliente'),
                fecha_inicio=request.POST.get('fecha_inicio'),
                fecha_fin=request.POST.get('fecha_fin'),
                escalable=request.POST.get('promocion_escalable') == '1',
                estado=request.POST.get('estado', 1)
            )
            
            escalable_text = " (ESCALABLE)" if promocion.escalable else ""
            
            tipo_filtro = request.POST.get('tipo_filtro', 'productos_especificos')
            
            if tipo_filtro == 'linea_marca':
                marca_id = request.POST.get('grupo_proveedor')
                linea_id = request.POST.get('linea_articulo')
                monto_minimo = request.POST.get('monto_minimo_productos')
                
                if marca_id:
                    promocion.grupo_proveedor_id = marca_id
                
                if linea_id:
                    promocion.linea_articulo_id = linea_id
                
                if monto_minimo:
                    promocion.monto_minimo = float(monto_minimo)
                
                promocion.save()
                
            else:
                productos_condicion = request.POST.getlist('productos_condicion')
                productos_validos = [p for p in productos_condicion if p]
                                
                for producto_id in productos_validos:
                    VerificacionProducto.objects.create(
                        articulo_id=producto_id,
                        promocion=promocion
                    )
            
            procesar_condiciones_rangos_ilimitados(request, promocion)
            
            tipo_beneficio = request.POST.get('tipo_beneficio')
            
            if tipo_beneficio:
                tipo_beneficio_texto = ''
                if tipo_beneficio == '1':
                    tipo_beneficio_texto = 'bonificacion'
                elif tipo_beneficio == '2':
                    tipo_beneficio_texto = 'descuento'
                elif tipo_beneficio == '3':
                    tipo_beneficio_texto = 'ambos'
                                
                descuento_general = None
                if tipo_beneficio_texto in ['descuento', 'ambos']:
                    if tipo_beneficio_texto == 'descuento':
                        descuento_general = request.POST.get('porcentaje_descuento')
                    else:  # ambos
                        descuento_general = request.POST.get('porcentaje_descuento_ambos')
                
                beneficio = Beneficio.objects.create(
                    promocion=promocion,
                    tipo_beneficio=tipo_beneficio_texto,
                    descuento=float(descuento_general) if descuento_general else None
                )
                                
                # Configurar productos beneficiados si aplica
                if tipo_beneficio_texto in ['bonificacion', 'ambos']:
                    
                    if tipo_beneficio_texto == 'ambos':
                        productos = request.POST.getlist('productos_bonificados_ambos[]')
                        cantidades = request.POST.getlist('cantidad_bonificada_ambos[]')
                    else:  # bonificacion
                        productos = request.POST.getlist('productos_bonificados[]')
                        cantidades = request.POST.getlist('cantidad_bonificada[]')
                                        
                    for producto_id, cantidad in zip(productos, cantidades):
                        if producto_id and cantidad:
                            ProductosBeneficios.objects.create(
                                beneficio=beneficio,
                                articulo_id=producto_id,
                                cantidad=int(cantidad)
                            )
            else:
                print("No hay beneficios de promoción definidos")
            
            # Contar elementos relacionados
            verificaciones = VerificacionProducto.objects.filter(promocion=promocion).count()
            rangos = Rango.objects.filter(promocion=promocion).count()
            beneficios = Beneficio.objects.filter(promocion=promocion).count()
            productos_bonificados_total = ProductoBonificadoRango.objects.filter(rango__promocion=promocion).count()
            
            messages.success(request, f'Promoción "{promocion.descripcion}" creada exitosamente')
            return redirect('home')
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        messages.error(request, f"Error al registrar la promoción: {str(e)}")
        form = PromocionForm()
        return render(request, 'core/promociones/registrar_promocion.html', {'form': form})

def procesar_condiciones_rangos_ilimitados(request, promocion):
    
    tipo_condicion = request.POST.get('tipo_condicion')
    
    if not tipo_condicion:
        print("No hay condiciones de activación definidas")
        return
        
    if tipo_condicion == 'cantidad':
        procesar_rangos_cantidad_ilimitados(request, promocion)
    elif tipo_condicion == 'monto':
        procesar_rangos_monto_ilimitados(request, promocion)


def procesar_rangos_cantidad_ilimitados(request, promocion):
    cantidades_min = request.POST.getlist('cantidad_min[]')
    cantidades_max = request.POST.getlist('cantidad_max[]')
    descuentos = request.POST.getlist('porcentaje_descuento_cantidad[]')
    
    rangos_validos = [(i, cm) for i, cm in enumerate(cantidades_min) if cm and cm.strip()]
    total_rangos = len(rangos_validos)
    
    print(f"Rangos de cantidad válidos encontrados: {total_rangos}")
    
    rangos_guardados = 0
    productos_guardados_total = 0
    
    # PROCESAR TODOS LOS RANGOS DINÁMICAMENTE
    for posicion_real, (indice_original, cantidad_min) in enumerate(rangos_validos):        
        # Obtener datos del rango
        cantidad_max = cantidades_max[indice_original] if indice_original < len(cantidades_max) and cantidades_max[indice_original] else None
        descuento = descuentos[indice_original] if indice_original < len(descuentos) and descuentos[indice_original] else None
        
        # Crear el rango en la base de datos
        rango = Rango.objects.create(
            promocion=promocion,
            tipo_rango='cantidad',
            minimo=int(cantidad_min),
            maximo=int(cantidad_max) if cantidad_max else None,
            descuento=float(descuento) if descuento else None
        )
        
        rangos_guardados += 1
        
        productos_rango_key = f'producto_bonificado_cantidad_{indice_original}[]'
        cantidades_rango_key = f'cantidad_bonificada_cantidad_{indice_original}[]'
        
        productos_bonificados_rango = request.POST.getlist(productos_rango_key)
        cantidades_bonificadas_rango = request.POST.getlist(cantidades_rango_key)
        
        productos_rango_guardados = 0
        for j, producto_id in enumerate(productos_bonificados_rango):
            if (producto_id and 
                j < len(cantidades_bonificadas_rango) and 
                cantidades_bonificadas_rango[j]):
                
                producto_bonif = ProductoBonificadoRango.objects.create(
                    rango=rango,
                    articulo_id=producto_id,
                    cantidad=int(cantidades_bonificadas_rango[j])
                )
                productos_rango_guardados += 1
                productos_guardados_total += 1


def procesar_rangos_monto_ilimitados(request, promocion):    
    montos_min = request.POST.getlist('monto_minimo[]')
    montos_max = request.POST.getlist('monto_maximo[]')
    descuentos = request.POST.getlist('porcentaje_descuento_monto[]')
    
    rangos_validos = [(i, mm) for i, mm in enumerate(montos_min) if mm and mm.strip()]
    total_rangos = len(rangos_validos)
        
    rangos_guardados = 0
    productos_guardados_total = 0
    
    # PROCESAR TODOS LOS RANGOS DINÁMICAMENTE
    for posicion_real, (indice_original, monto_min) in enumerate(rangos_validos):        
        # Obtener datos del rango
        monto_max = montos_max[indice_original] if indice_original < len(montos_max) and montos_max[indice_original] else None
        descuento = descuentos[indice_original] if indice_original < len(descuentos) and descuentos[indice_original] else None
        
        # Crear el rango en la base de datos
        rango = Rango.objects.create(
            promocion=promocion,
            tipo_rango='monto',
            minimo=int(float(monto_min)),
            maximo=int(float(monto_max)) if monto_max else None,
            descuento=float(descuento) if descuento else None
        )
        
        rangos_guardados += 1
        
        # PROCESAR PRODUCTOS BONIFICADOS ESPECÍFICOS DE ESTE RANGO
        productos_rango_key = f'producto_bonificado_monto_{indice_original}[]'
        cantidades_rango_key = f'cantidad_bonificada_monto_{indice_original}[]'
        
        productos_bonificados_rango = request.POST.getlist(productos_rango_key)
        cantidades_bonificadas_rango = request.POST.getlist(cantidades_rango_key)
        
        # Guardar productos bonificados específicos de este rango
        productos_rango_guardados = 0
        for j, producto_id in enumerate(productos_bonificados_rango):
            if (producto_id and 
                j < len(cantidades_bonificadas_rango) and 
                cantidades_bonificadas_rango[j]):
                
                producto_bonif = ProductoBonificadoRango.objects.create(
                    rango=rango,
                    articulo_id=producto_id,
                    cantidad=int(cantidades_bonificadas_rango[j])
                )
                productos_rango_guardados += 1
                productos_guardados_total += 1
                

# F cuasa la cantidad se realiza por medio de insomnia
@csrf_exempt
@require_http_methods(["POST"])
def api_crear_promocion_completa(request):
    
    try:
        data = json.loads(request.body)
        
        # Validar campos requeridos
        campos_requeridos = ['descripcion', 'empresa', 'sucursal', 'canal_cliente', 'fecha_inicio', 'fecha_fin']
        for campo in campos_requeridos:
            if campo not in data:
                return JsonResponse({'error': f'Campo requerido: {campo}'}, status=400)
        
        with transaction.atomic():
            print(f"\n CREANDO PROMOCIÓN VÍA API ")
            
            promocion = Promocion.objects.create(
                descripcion=data['descripcion'],
                empresa_id=data['empresa'],
                sucursal_id=data['sucursal'],
                canal_cliente_id=data['canal_cliente'],
                fecha_inicio=data['fecha_inicio'],
                fecha_fin=data['fecha_fin'],
                grupo_proveedor_id=data.get('grupo_proveedor_id'),
                linea_articulo_id=data.get('linea_articulo_id'),
                monto_minimo=data.get('monto_minimo'),
                cantidad_minima=data.get('cantidad_minima'),  # ← NUEVO CAMPO
                escalable=data.get('escalable', False),
                estado=data.get('estado', 1)
            )
                        
            if 'productos_verificacion' in data and data['productos_verificacion']:
                for producto_id in data['productos_verificacion']:
                    VerificacionProducto.objects.create(
                        promocion=promocion,
                        articulo_id=producto_id
                    )
                    print(f"   ✅ Producto verificación: {producto_id}")
            
            if 'rangos' in data and data['rangos']:
                for rango_data in data['rangos']:
                    rango = Rango.objects.create(
                        promocion=promocion,
                        tipo_rango=rango_data['tipo'],  # 'cantidad' o 'monto'
                        minimo=rango_data['minimo'],
                        maximo=rango_data.get('maximo'),
                        descuento=rango_data.get('descuento')
                    )
                                        
                    if 'productos_bonificados' in rango_data:
                        for prod_bonif in rango_data['productos_bonificados']:
                            ProductoBonificadoRango.objects.create(
                                rango=rango,
                                articulo_id=prod_bonif['articulo_id'],
                                cantidad=prod_bonif['cantidad']
                            )
                            print(f"      🎁 Producto bonificado rango: {prod_bonif['cantidad']} x {prod_bonif['articulo_id']}")
            
            if 'beneficios' in data and data['beneficios']:
                for beneficio_data in data['beneficios']:
                    beneficio = Beneficio.objects.create(
                        promocion=promocion,
                        tipo_beneficio=beneficio_data['tipo'],  # 'bonificacion', 'descuento', 'ambos'
                        descuento=beneficio_data.get('descuento')
                    )
                                        
                    # Crear productos beneficiados generales
                    if 'productos_bonificados' in beneficio_data:
                        for prod_benef in beneficio_data['productos_bonificados']:
                            ProductosBeneficios.objects.create(
                                beneficio=beneficio,
                                articulo_id=prod_benef['articulo_id'],
                                cantidad=prod_benef['cantidad']
                            )
                        
            return JsonResponse({
                'success': True,
                'promocion_id': promocion.promocion_id,
                'mensaje': f'Promoción completa "{promocion.descripcion}" creada exitosamente',
                'data': {
                    'id': promocion.promocion_id,
                    'descripcion': promocion.descripcion,
                    'fecha_inicio': promocion.fecha_inicio,
                    'fecha_fin': promocion.fecha_fin,
                    'cantidad_minima': promocion.cantidad_minima,
                    'escalable': promocion.escalable,
                    'rangos_creados': len(data.get('rangos', [])),
                    'beneficios_creados': len(data.get('beneficios', []))
                }
            }, status=201)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)