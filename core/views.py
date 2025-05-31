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
        'promociones_aplicadas': promociones_aplicadas,
        'beneficios_promociones': beneficios_promociones,
        'descuentos_aplicados': descuentos_aplicados
    }) 

# Agregar estas funciones a tu views.py si no las tienes

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
            #Esto es para pasar a la vista de detalle pedido
            return redirect('detalle_pedido', pedido_id=pedido.pedido_id)
            #return redirect('home')  # o redirigir a vista de pedidos
            
    except Exception as e:
        messages.error(request, f"Error al procesar el pedido: {str(e)}")
        return redirect('vista_carrito')


def guardar_beneficios_en_pedido(pedido, beneficios):
    """
    Guarda los beneficios aplicados en el pedido (función actualizada para nueva estructura)
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




# Apartir de aca inicia lo que tiene que ver con registrar la promocion
def registrar_promocion(request):
    """
    Vista principal para registrar promociones
    """
    if request.method == 'POST':
        return procesar_nueva_promocion(request)
    else:
        form = PromocionForm()
        return render(request, 'core/promociones/registrar_promocion.html', {'form': form})

def procesar_nueva_promocion(request):
    """
    Función unificada para procesar y guardar toda la información de la promoción
    VERSIÓN CORREGIDA PARA RANGOS ILIMITADOS
    """
    
    # ====== DEBUG: Verificar datos recibidos ======
    print(f"\n🚀 === PETICIÓN RECIBIDA ===")
    print(f"📊 Método: {request.method}")
    print(f"📊 Usuario: {request.user}")
    
    # Debug específico para rangos ilimitados
    debug_post_data_rangos_ilimitados(request)
    
    # Verificar datos críticos
    descripcion = request.POST.get('descripcion', '').strip()
    print(f"📋 Descripción: '{descripcion}'")
    
    if not descripcion:
        print("❌ ERROR: Descripción vacía")
        messages.error(request, "La descripción es obligatoria")
        form = PromocionForm()
        return render(request, 'core/promociones/registrar_promocion.html', {'form': form})
    
    try:
        with transaction.atomic():
            print("\n🚀 === INICIANDO PROCESAMIENTO UNIFICADO DE PROMOCIÓN ===")
            
            # ====== PASO 1: CREAR LA PROMOCIÓN BASE ======
            print("📋 Paso 1: Creando promoción base...")
            
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
            print(f"✅ Promoción base creada: {promocion.descripcion}{escalable_text}")
            
            # ====== PASO 2: CONFIGURACIÓN DE PRODUCTOS ======
            print("📦 Paso 2: Configurando productos...")
            
            tipo_filtro = request.POST.get('tipo_filtro', 'productos_especificos')
            print(f"   📊 Tipo de filtro: {tipo_filtro}")
            
            if tipo_filtro == 'linea_marca':
                # CASO: Por Marca/Línea completa → Guardar en campos de promoción
                marca_id = request.POST.get('grupo_proveedor')
                linea_id = request.POST.get('linea_articulo')
                monto_minimo = request.POST.get('monto_minimo_productos')
                
                if marca_id:
                    promocion.grupo_proveedor_id = marca_id
                    print(f"   ✅ Marca/Proveedor guardado: {marca_id}")
                
                if linea_id:
                    promocion.linea_articulo_id = linea_id
                    print(f"   ✅ Línea artículo guardada: {linea_id}")
                
                if monto_minimo:
                    promocion.monto_minimo = float(monto_minimo)
                    print(f"   ✅ Monto mínimo guardado: S/{monto_minimo}")
                
                promocion.save()
                
            else:
                # CASO: Productos específicos → Guardar en tabla verificacion_productos
                productos_condicion = request.POST.getlist('productos_condicion')
                productos_validos = [p for p in productos_condicion if p]
                
                print(f"   📦 Productos específicos seleccionados: {len(productos_validos)}")
                
                for producto_id in productos_validos:
                    VerificacionProducto.objects.create(
                        articulo_id=producto_id,
                        promocion=promocion
                    )
                    print(f"   ✅ Producto verificación guardado: {producto_id}")
            
            # ====== PASO 3: CONDICIONES DE ACTIVACIÓN (RANGOS ILIMITADOS) ======
            procesar_condiciones_rangos_ilimitados(request, promocion)
            
            # ====== PASO 4: BENEFICIOS DE LA PROMOCIÓN ======
            print("🎁 Paso 4: Configurando beneficios de la promoción...")
            
            tipo_beneficio = request.POST.get('tipo_beneficio')
            
            if tipo_beneficio:
                # Convertir el valor numérico a texto
                tipo_beneficio_texto = ''
                if tipo_beneficio == '1':
                    tipo_beneficio_texto = 'bonificacion'
                elif tipo_beneficio == '2':
                    tipo_beneficio_texto = 'descuento'
                elif tipo_beneficio == '3':
                    tipo_beneficio_texto = 'ambos'
                
                print(f"   📊 Tipo de beneficio: {tipo_beneficio_texto}")
                
                # Obtener descuento general según el tipo
                descuento_general = None
                if tipo_beneficio_texto in ['descuento', 'ambos']:
                    if tipo_beneficio_texto == 'descuento':
                        descuento_general = request.POST.get('porcentaje_descuento')
                    else:  # ambos
                        descuento_general = request.POST.get('porcentaje_descuento_ambos')
                
                # Crear el registro de beneficio
                beneficio = Beneficio.objects.create(
                    promocion=promocion,
                    tipo_beneficio=tipo_beneficio_texto,
                    descuento=float(descuento_general) if descuento_general else None
                )
                
                print(f"   ✅ Beneficio general creado: {tipo_beneficio_texto}, descuento: {descuento_general or '0'}%")
                
                # Configurar productos beneficiados si aplica
                if tipo_beneficio_texto in ['bonificacion', 'ambos']:
                    print("   🎁 Configurando productos beneficiados...")
                    
                    if tipo_beneficio_texto == 'ambos':
                        productos = request.POST.getlist('productos_bonificados_ambos[]')
                        cantidades = request.POST.getlist('cantidad_bonificada_ambos[]')
                    else:  # bonificacion
                        productos = request.POST.getlist('productos_bonificados[]')
                        cantidades = request.POST.getlist('cantidad_bonificada[]')
                    
                    print(f"   📦 Productos beneficiados encontrados: {len(productos)}")
                    
                    for producto_id, cantidad in zip(productos, cantidades):
                        if producto_id and cantidad:
                            ProductosBeneficios.objects.create(
                                beneficio=beneficio,
                                articulo_id=producto_id,
                                cantidad=int(cantidad)
                            )
                            print(f"   ✅ Producto beneficiado guardado: {cantidad} unidades del artículo {producto_id}")
            else:
                print("   ⚠️ No hay beneficios de promoción definidos")
            
            # ====== FINALIZACIÓN ======
            print(f"✅ === PROMOCIÓN GUARDADA EXITOSAMENTE: {promocion.descripcion} (ID: {promocion.promocion_id}) ===\n")
            
            # Verificación final
            verificar_guardado_productos_bonificados_completo(promocion)
            
            # Mostrar resumen final
            print("📊 RESUMEN FINAL:")
            print(f"   🏢 Empresa: {promocion.empresa.nombre}")
            print(f"   🏪 Sucursal: {promocion.sucursal.nombre if promocion.sucursal else 'Todas'}")
            print(f"   📅 Vigencia: {promocion.fecha_inicio} - {promocion.fecha_fin}")
            print(f"   ♾️ Escalable: {'Sí' if promocion.escalable else 'No'}")
            
            # Contar elementos relacionados
            verificaciones = VerificacionProducto.objects.filter(promocion=promocion).count()
            rangos = Rango.objects.filter(promocion=promocion).count()
            beneficios = Beneficio.objects.filter(promocion=promocion).count()
            productos_bonificados_total = ProductoBonificadoRango.objects.filter(rango__promocion=promocion).count()
            
            print(f"   📦 Productos verificación: {verificaciones}")
            print(f"   🎯 Rangos de condiciones: {rangos}")
            print(f"   🎁 Beneficios: {beneficios}")
            print(f"   🎁 Productos bonificados en rangos: {productos_bonificados_total}")
            
            messages.success(request, f'Promoción "{promocion.descripcion}" creada exitosamente')
            return redirect('home')
            
    except Exception as e:
        print(f"❌ ERROR al procesar promoción: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, f"Error al registrar la promoción: {str(e)}")
        form = PromocionForm()
        return render(request, 'core/promociones/registrar_promocion.html', {'form': form})


def debug_post_data_rangos_ilimitados(request):
    """
    Función de debug para verificar los datos POST relacionados con rangos - VERSIÓN ILIMITADA
    """
    print("\n🔍 === DEBUG POST DATA - RANGOS ILIMITADOS ===")
    
    # Debug rangos de cantidad
    cantidades_min = request.POST.getlist('cantidad_min[]')
    print(f"📊 TOTAL Rangos de cantidad detectados: {len(cantidades_min)}")
    
    if cantidades_min:
        print("🎯 DETALLE RANGOS DE CANTIDAD:")
        for i in range(len(cantidades_min)):
            if cantidades_min[i]:  # Solo procesar rangos con datos
                productos_key = f'producto_bonificado_cantidad_{i}[]'
                cantidades_key = f'cantidad_bonificada_cantidad_{i}[]'
                
                productos = request.POST.getlist(productos_key)
                cantidades = request.POST.getlist(cantidades_key)
                
                print(f"   🎯 Rango cantidad {i}:")
                print(f"      cantidad_min: {cantidades_min[i]}")
                print(f"      cantidad_max: {request.POST.getlist('cantidad_max[]')[i] if i < len(request.POST.getlist('cantidad_max[]')) else 'N/A'}")
                print(f"      descuento: {request.POST.getlist('porcentaje_descuento_cantidad[]')[i] if i < len(request.POST.getlist('porcentaje_descuento_cantidad[]')) else 'N/A'}%")
                print(f"      productos ({productos_key}): {productos}")
                print(f"      cantidades ({cantidades_key}): {cantidades}")
                print(f"      productos válidos: {len([p for p in productos if p])}")
    
    # Debug rangos de monto
    montos_min = request.POST.getlist('monto_minimo[]')
    print(f"📊 TOTAL Rangos de monto detectados: {len(montos_min)}")
    
    if montos_min:
        print("💰 DETALLE RANGOS DE MONTO:")
        for i in range(len(montos_min)):
            if montos_min[i]:  # Solo procesar rangos con datos
                productos_key = f'producto_bonificado_monto_{i}[]'
                cantidades_key = f'cantidad_bonificada_monto_{i}[]'
                
                productos = request.POST.getlist(productos_key)
                cantidades = request.POST.getlist(cantidades_key)
                
                print(f"   💰 Rango monto {i}:")
                print(f"      monto_min: S/{montos_min[i]}")
                print(f"      monto_max: S/{request.POST.getlist('monto_maximo[]')[i] if i < len(request.POST.getlist('monto_maximo[]')) else 'N/A'}")
                print(f"      descuento: {request.POST.getlist('porcentaje_descuento_monto[]')[i] if i < len(request.POST.getlist('porcentaje_descuento_monto[]')) else 'N/A'}%")
                print(f"      productos ({productos_key}): {productos}")
                print(f"      cantidades ({cantidades_key}): {cantidades}")
                print(f"      productos válidos: {len([p for p in productos if p])}")
    
    print(f"\n✅ RESUMEN TOTAL: {len(cantidades_min)} rangos cantidad + {len(montos_min)} rangos monto")
    print("=== FIN DEBUG POST DATA ===\n")


def procesar_condiciones_rangos_ilimitados(request, promocion):
    """
    Procesa las condiciones de activación (rangos) sin límite de cantidad - VERSIÓN COMPLETA
    """
    print("🎯 Paso 3: Configurando condiciones de activación (rangos ilimitados)...")
    
    tipo_condicion = request.POST.get('tipo_condicion')
    
    if not tipo_condicion:
        print("   ⚠️ No hay condiciones de activación definidas")
        return
    
    print(f"   📈 Tipo de condición: {tipo_condicion}")
    
    if tipo_condicion == 'cantidad':
        procesar_rangos_cantidad_ilimitados(request, promocion)
    elif tipo_condicion == 'monto':
        procesar_rangos_monto_ilimitados(request, promocion)


def procesar_rangos_cantidad_ilimitados(request, promocion):
    """
    Procesa rangos de cantidad sin límite - VERSIÓN CORREGIDA
    """
    print("   🔢 Procesando rangos de cantidad ilimitados...")
    
    cantidades_min = request.POST.getlist('cantidad_min[]')
    cantidades_max = request.POST.getlist('cantidad_max[]')
    descuentos = request.POST.getlist('porcentaje_descuento_cantidad[]')
    
    # Filtrar solo rangos con datos válidos
    rangos_validos = [(i, cm) for i, cm in enumerate(cantidades_min) if cm and cm.strip()]
    total_rangos = len(rangos_validos)
    
    print(f"   📊 Rangos de cantidad válidos encontrados: {total_rangos}")
    
    rangos_guardados = 0
    productos_guardados_total = 0
    
    # PROCESAR TODOS LOS RANGOS DINÁMICAMENTE
    for posicion_real, (indice_original, cantidad_min) in enumerate(rangos_validos):
        print(f"\n   🎯 === PROCESANDO RANGO CANTIDAD {posicion_real + 1} (índice frontend: {indice_original}) ===")
        
        # Obtener datos del rango
        cantidad_max = cantidades_max[indice_original] if indice_original < len(cantidades_max) and cantidades_max[indice_original] else None
        descuento = descuentos[indice_original] if indice_original < len(descuentos) and descuentos[indice_original] else None
        
        print(f"   📊 Datos del rango:")
        print(f"      Cantidad mínima: {cantidad_min}")
        print(f"      Cantidad máxima: {cantidad_max or 'Sin límite'}")
        print(f"      Descuento: {descuento or '0'}%")
        
        # Crear el rango en la base de datos
        rango = Rango.objects.create(
            promocion=promocion,
            tipo_rango='cantidad',
            minimo=int(cantidad_min),
            maximo=int(cantidad_max) if cantidad_max else None,
            descuento=float(descuento) if descuento else None
        )
        
        rangos_guardados += 1
        print(f"   ✅ Rango guardado en BD con ID: {rango.rango_id}")
        
        # PROCESAR PRODUCTOS BONIFICADOS ESPECÍFICOS DE ESTE RANGO
        productos_rango_key = f'producto_bonificado_cantidad_{indice_original}[]'
        cantidades_rango_key = f'cantidad_bonificada_cantidad_{indice_original}[]'
        
        productos_bonificados_rango = request.POST.getlist(productos_rango_key)
        cantidades_bonificadas_rango = request.POST.getlist(cantidades_rango_key)
        
        print(f"   🔍 Buscando productos bonificados para rango:")
        print(f"      Clave productos: {productos_rango_key}")
        print(f"      Clave cantidades: {cantidades_rango_key}")
        print(f"      Productos encontrados: {len(productos_bonificados_rango)}")
        print(f"      Cantidades encontradas: {len(cantidades_bonificadas_rango)}")
        
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
                
                print(f"   ✅ Producto bonificado {productos_rango_guardados} guardado:")
                print(f"      BD ID: {producto_bonif.pro_boni_id}")
                print(f"      Artículo: {producto_id}")
                print(f"      Cantidad: {cantidades_bonificadas_rango[j]}")
                print(f"      Asociado al rango BD ID: {rango.rango_id}")
        
        print(f"   📦 RESUMEN RANGO {posicion_real + 1}: {productos_rango_guardados} productos bonificados guardados")
    
    print(f"\n   🎯 === RESUMEN FINAL CANTIDAD ===")
    print(f"   📊 Total rangos guardados: {rangos_guardados}")
    print(f"   🎁 Total productos bonificados: {productos_guardados_total}")


def procesar_rangos_monto_ilimitados(request, promocion):
    """
    Procesa rangos de monto sin límite - VERSIÓN CORREGIDA
    """
    print("   💰 Procesando rangos de monto ilimitados...")
    
    montos_min = request.POST.getlist('monto_minimo[]')
    montos_max = request.POST.getlist('monto_maximo[]')
    descuentos = request.POST.getlist('porcentaje_descuento_monto[]')
    
    # Filtrar solo rangos con datos válidos
    rangos_validos = [(i, mm) for i, mm in enumerate(montos_min) if mm and mm.strip()]
    total_rangos = len(rangos_validos)
    
    print(f"   📊 Rangos de monto válidos encontrados: {total_rangos}")
    
    rangos_guardados = 0
    productos_guardados_total = 0
    
    # PROCESAR TODOS LOS RANGOS DINÁMICAMENTE
    for posicion_real, (indice_original, monto_min) in enumerate(rangos_validos):
        print(f"\n   💰 === PROCESANDO RANGO MONTO {posicion_real + 1} (índice frontend: {indice_original}) ===")
        
        # Obtener datos del rango
        monto_max = montos_max[indice_original] if indice_original < len(montos_max) and montos_max[indice_original] else None
        descuento = descuentos[indice_original] if indice_original < len(descuentos) and descuentos[indice_original] else None
        
        print(f"   📊 Datos del rango:")
        print(f"      Monto mínimo: S/{monto_min}")
        print(f"      Monto máximo: S/{monto_max or 'Sin límite'}")
        print(f"      Descuento: {descuento or '0'}%")
        
        # Crear el rango en la base de datos
        rango = Rango.objects.create(
            promocion=promocion,
            tipo_rango='monto',
            minimo=int(float(monto_min)),
            maximo=int(float(monto_max)) if monto_max else None,
            descuento=float(descuento) if descuento else None
        )
        
        rangos_guardados += 1
        print(f"   ✅ Rango guardado en BD con ID: {rango.rango_id}")
        
        # PROCESAR PRODUCTOS BONIFICADOS ESPECÍFICOS DE ESTE RANGO
        productos_rango_key = f'producto_bonificado_monto_{indice_original}[]'
        cantidades_rango_key = f'cantidad_bonificada_monto_{indice_original}[]'
        
        productos_bonificados_rango = request.POST.getlist(productos_rango_key)
        cantidades_bonificadas_rango = request.POST.getlist(cantidades_rango_key)
        
        print(f"   🔍 Buscando productos bonificados para rango:")
        print(f"      Clave productos: {productos_rango_key}")
        print(f"      Clave cantidades: {cantidades_rango_key}")
        print(f"      Productos encontrados: {len(productos_bonificados_rango)}")
        print(f"      Cantidades encontradas: {len(cantidades_bonificadas_rango)}")
        
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
                
                print(f"   ✅ Producto bonificado {productos_rango_guardados} guardado:")
                print(f"      BD ID: {producto_bonif.pro_boni_id}")
                print(f"      Artículo: {producto_id}")
                print(f"      Cantidad: {cantidades_bonificadas_rango[j]}")
                print(f"      Asociado al rango BD ID: {rango.rango_id}")
        
        print(f"   📦 RESUMEN RANGO {posicion_real + 1}: {productos_rango_guardados} productos bonificados guardados")
    
    print(f"\n   💰 === RESUMEN FINAL MONTO ===")
    print(f"   📊 Total rangos guardados: {rangos_guardados}")
    print(f"   🎁 Total productos bonificados: {productos_guardados_total}")


def verificar_guardado_productos_bonificados_completo(promocion):
    """
    Función para verificar que los productos bonificados se guardaron correctamente - VERSIÓN COMPLETA
    """
    print(f"\n🔍 === VERIFICACIÓN POST-GUARDADO COMPLETA ===")
    print(f"📋 Promoción: {promocion.descripcion} (ID: {promocion.promocion_id})")
    
    # Verificar rangos
    rangos = Rango.objects.filter(promocion=promocion).order_by('tipo_rango', 'minimo')
    print(f"📊 Rangos encontrados en BD: {rangos.count()}")
    
    total_productos_bonificados = 0
    
    for i, rango in enumerate(rangos):
        print(f"\n   🎯 Rango {i+1} (BD ID: {rango.rango_id}):")
        print(f"      Tipo: {rango.tipo_rango}")
        print(f"      Mínimo: {rango.minimo}")
        print(f"      Máximo: {rango.maximo or 'Sin límite'}")
        print(f"      Descuento: {rango.descuento or 0}%")
        
        # Verificar productos bonificados de este rango
        productos_bonif = ProductoBonificadoRango.objects.filter(rango=rango)
        print(f"      📦 Productos bonificados: {productos_bonif.count()}")
        
        for j, prod_bonif in enumerate(productos_bonif):
            print(f"         {j+1}. BD ID: {prod_bonif.pro_boni_id}")
            print(f"            Artículo: {prod_bonif.articulo.codigo} - {prod_bonif.articulo.descripcion}")
            print(f"            Cantidad: {prod_bonif.cantidad}")
            print(f"            Rango asociado: {prod_bonif.rango.rango_id}")
            total_productos_bonificados += 1
    
    print(f"\n✅ RESUMEN FINAL:")
    print(f"   📊 Total rangos: {rangos.count()}")
    print(f"   📦 Total productos bonificados: {total_productos_bonificados}")
    print(f"   ♾️ Escalable: {'Sí' if promocion.escalable else 'No'}")
    print(f"=== FIN VERIFICACIÓN COMPLETA ===\n")

#Este es para mostrar el detalle de pedidos.
@login_required
def detalle_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    detalles = DetallePedido.objects.filter(pedido=pedido).select_related('articulo')

    for item in detalles:
        item.subtotal = item.cantidad * item.articulo.precio

    bonificaciones = BonificacionAplicada.objects.filter(pedido=pedido).select_related('articulo', 'promocion')
    descuentos = DescuentoAplicado.objects.filter(pedido=pedido).select_related('promocion')

    context = {
        'pedido': pedido,
        'detalles': detalles,
        'bonificaciones': bonificaciones,
        'descuentos': descuentos,
    }
    return render(request, 'core/pedidos/detalle_pedido.html', context)

# Esto es para listar mis pedidos
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Pedido

@login_required
def mis_pedidos(request):
    pedidos = Pedido.objects.filter(usuario=request.user).order_by('-fecha')
    return render(request, 'core/pedidos/mis_pedidos.html', {'pedidos': pedidos})

@user_passes_test(lambda u: u.is_authenticated and u.id == 1)
def listar_pedidos(request):
    pedidos = Pedido.objects.all().order_by('-fecha')
    return render(request, 'core/pedidos/listar_pedidos.html', {'pedidos': pedidos})