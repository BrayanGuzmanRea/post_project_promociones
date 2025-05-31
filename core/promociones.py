from decimal import Decimal
from datetime import datetime
from django.utils import timezone
from django.db.models import Q, Sum

from .models import Promocion, Rango, ProductoBonificadoRango, Beneficio, ProductosBeneficios,  VerificacionProducto

def evaluar_promociones(carrito_detalle, cliente, empresa=None, sucursal=None):
    
    resultado = {
        'promociones_aplicadas': [],
        'bonificaciones': [],
        'descuentos': [],
        'errores': []
    }
    
    try:
        # Obtener promociones elegibles
        promociones_elegibles = obtener_promociones_elegibles(cliente, empresa, sucursal)
        
        if not promociones_elegibles:
            print("No hay promociones elegibles para este cliente/empresa")
            return resultado
        
        
        # Evaluar cada promoción
        for promocion in promociones_elegibles:            
            try:
                beneficios_promocion = evaluar_promocion_individual(
                    promocion, carrito_detalle, cliente
                )
                
                if beneficios_promocion['aplica']:
                    resultado['promociones_aplicadas'].append({
                        'promocion_id': promocion.promocion_id,
                        'nombre': promocion.descripcion,
                        'fecha_inicio': promocion.fecha_inicio,
                        'fecha_fin': promocion.fecha_fin,
                        'escalable': promocion.escalable
                    })
                    
                    for bonif in beneficios_promocion['bonificaciones']:
                        bonif['promocion'] = promocion
                        resultado['bonificaciones'].append(bonif)
                    
                    for desc in beneficios_promocion['descuentos']:
                        desc['promocion'] = promocion
                        resultado['descuentos'].append(desc)
                    
                else:
                    print(f"Promoción no aplica: {beneficios_promocion.get('razon', 'Razón desconocida')}")
                    
            except Exception as e:
                error_msg = f"Error evaluando promoción {promocion.descripcion}: {str(e)}"
                print(f"{error_msg}")
                resultado['errores'].append(error_msg)
        
        return resultado
        
    except Exception as e:
        error_msg = f"Error general en evaluación de promociones: {str(e)}"
        print(f"{error_msg}")
        resultado['errores'].append(error_msg)
        return resultado


def obtener_promociones_elegibles(cliente, empresa=None, sucursal=None):
    hoy = timezone.now().date()
    
    filtros = Q(
        estado=1,  # Promociones activas 1 y si es 9 no esta activa
        fecha_inicio__lte=hoy,  
        fecha_fin__gte=hoy      
    )
    
    # Este es para ver cuales se aplican a un cliente específico y ver si es para todos
    if cliente and hasattr(cliente, 'canal_cliente'):
        filtro_canal = Q(canal_cliente=cliente.canal_cliente) | Q(canal_cliente_id=5)
        filtros &= filtro_canal
    
    if empresa:
        filtros &= Q(empresa=empresa)
    
    if sucursal:
        filtros &= Q(Q(sucursal=sucursal) | Q(sucursal__isnull=True))
    
    promociones = Promocion.objects.filter(filtros).order_by('promocion_id')
    
    for promo in promociones:
        escalable_text = " (ESCALABLE)" if promo.escalable else ""
        canal_info = f" [Canal: {promo.canal_cliente.nombre}]" if hasattr(promo.canal_cliente, 'nombre') else f" [Canal ID: {promo.canal_cliente_id}]"
        print(f"   - {promo.descripcion}{escalable_text}{canal_info}")
    
    return promociones


def evaluar_promocion_individual(promocion, carrito_detalle, cliente):
    resultado = {
        'aplica': False,
        'bonificaciones': [],
        'descuentos': [],
        'razon': ''
    }
    try:
        productos_validos = verificar_productos_requeridos(promocion, carrito_detalle)
        
        if not productos_validos['cumple']:
            resultado['razon'] = productos_validos['razon']
            return resultado
        
        rangos = Rango.objects.filter(promocion=promocion).order_by('minimo')
        
        if rangos.exists():
            return evaluar_promocion_con_rangos(promocion, carrito_detalle, productos_validos, rangos)
        else:
            return evaluar_promocion_sin_rangos(promocion, carrito_detalle, productos_validos)
            
    except Exception as e:
        resultado['razon'] = f"Error en evaluación: {str(e)}"
        print(f" {resultado['razon']}")
        return resultado


def verificar_productos_requeridos(promocion, carrito_detalle):
    resultado = {
        'cumple': False,
        'productos_aplicables': [],
        'cantidad_total': 0,
        'monto_total': Decimal('0'),
        'razon': ''
    }
    
    if promocion.grupo_proveedor_id or promocion.linea_articulo_id:        
        filtros_productos = Q()
        
        if promocion.grupo_proveedor_id:
            filtros_productos &= Q(articulo__grupo_proveedor_id=promocion.grupo_proveedor_id)
            print(f"Marca: {promocion.grupo_proveedor_id}")
        
        if promocion.linea_articulo_id:
            filtros_productos &= Q(articulo__linea_articulo_id=promocion.linea_articulo_id)
            print(f"Línea: {promocion.linea_articulo_id}")
        
        productos_aplicables = carrito_detalle.filter(filtros_productos)
        
        if not productos_aplicables.exists():
            resultado['razon'] = "No hay productos de la marca/línea especificada en el carrito"
            return resultado
        
        # Calcular totales
        for detalle in productos_aplicables:
            resultado['productos_aplicables'].append(detalle)
            resultado['cantidad_total'] += detalle.cantidad
            resultado['monto_total'] += detalle.articulo.precio * detalle.cantidad
        
        # Verificar cantidad mínima
        if promocion.cantidad_minima and resultado['cantidad_total'] < promocion.cantidad_minima:
            resultado['razon'] = f"Cantidad insuficiente: {resultado['cantidad_total']} < {promocion.cantidad_minima} unidades"
            print(f"{resultado['razon']}")
            return resultado
        
        # Verificar monto mínimo si está especificado
        if promocion.monto_minimo and resultado['monto_total'] < promocion.monto_minimo:
            resultado['razon'] = f"Monto insuficiente: S/{resultado['monto_total']} < S/{promocion.monto_minimo}"
            print(f"{resultado['razon']}")
            return resultado
        
        
        # MOSTRAR VALIDACIONES APROBADAS
        if promocion.cantidad_minima:
            print(f"Cantidad mínima cumplida: {resultado['cantidad_total']} >= {promocion.cantidad_minima}")
        if promocion.monto_minimo:
            print(f"Monto mínimo cumplido: S/{resultado['monto_total']} >= S/{promocion.monto_minimo}")
        
        resultado['cumple'] = True
        return resultado
    
    verificaciones = VerificacionProducto.objects.filter(promocion=promocion)
    
    if verificaciones.exists():        
        productos_requeridos = [v.articulo_id for v in verificaciones]
        productos_en_carrito = []
        
        for detalle in carrito_detalle:
            if detalle.articulo.articulo_id in productos_requeridos:
                productos_en_carrito.append(detalle.articulo.articulo_id)
                resultado['productos_aplicables'].append(detalle)
                resultado['cantidad_total'] += detalle.cantidad
                resultado['monto_total'] += detalle.articulo.precio * detalle.cantidad
        
        productos_faltantes = set(productos_requeridos) - set(productos_en_carrito)
        
        if productos_faltantes:
            resultado['razon'] = f"Faltan productos requeridos: {len(productos_faltantes)} de {len(productos_requeridos)}"
            return resultado
        
        resultado['cumple'] = True
        return resultado
        
    for detalle in carrito_detalle:
        resultado['productos_aplicables'].append(detalle)
        resultado['cantidad_total'] += detalle.cantidad
        resultado['monto_total'] += detalle.articulo.precio * detalle.cantidad
    
    resultado['cumple'] = True
    return resultado


def evaluar_promocion_con_rangos(promocion, carrito_detalle, productos_validos, rangos):
    
    resultado = {
        'aplica': False,
        'bonificaciones': [],
        'descuentos': [],
        'razon': ''
    }
    
    primer_rango = rangos.first()
    tipo_rango = primer_rango.tipo_rango
        
    if tipo_rango == 'cantidad':
        valor_comparar = productos_validos['cantidad_total']
        print(f"🔢 Cantidad total a evaluar: {valor_comparar}")
    else: 
        valor_comparar = float(productos_validos['monto_total'])
        print(f"💰 Monto total a evaluar: S/{valor_comparar}")
    
    rango_aplicable = None
    for rango in rangos:
        if valor_comparar >= rango.minimo:
            if rango.maximo is None or valor_comparar <= rango.maximo:
                rango_aplicable = rango
                print(f"Rango aplicable encontrado: {rango.minimo} - {rango.maximo or '∞'}")
                break
    
    if not rango_aplicable:
        resultado['razon'] = f"Valor {valor_comparar} no alcanza ningún rango"
        return resultado
    
    veces_aplicable = 1
    if promocion.escalable:
        if tipo_rango == 'cantidad':
            veces_aplicable = int(valor_comparar // rango_aplicable.minimo)
        else:
            veces_aplicable = int(valor_comparar // rango_aplicable.minimo)
        
        print(f"♾️ Promoción escalable: se aplicará {veces_aplicable} veces")
    
    # Aplicar descuento del rango
    if rango_aplicable.descuento and rango_aplicable.descuento > 0:
        descuento = {
            'tipo': 'porcentaje_rango',
            'porcentaje': float(rango_aplicable.descuento),
            'monto_descuento': 0,  
            'escalable': promocion.escalable,
            'veces_aplicable': veces_aplicable
        }
        
        if tipo_rango == 'monto':
            monto_base = productos_validos['monto_total']
        else:
            monto_base = productos_validos['monto_total']
        
        descuento['monto_descuento'] = float(monto_base * Decimal(str(rango_aplicable.descuento)) / 100)
        
        if promocion.escalable:
            descuento['monto_descuento'] *= veces_aplicable
        
        resultado['descuentos'].append(descuento)
    
    # Aplicar productos bonificados del rango
    productos_bonificados_rango = ProductoBonificadoRango.objects.filter(rango=rango_aplicable)
    
    for prod_bonif in productos_bonificados_rango:
        cantidad_bonificar = prod_bonif.cantidad
        
        if promocion.escalable:
            cantidad_bonificar *= veces_aplicable
        
        bonificacion = {
            'articulo': prod_bonif.articulo,
            'cantidad': cantidad_bonificar,
            'escalable': promocion.escalable,
            'veces_aplicable': veces_aplicable
        }
        
        resultado['bonificaciones'].append(bonificacion)
    
    # Aplicar beneficios generales adicionales
    beneficios_generales = aplicar_beneficios_generales(promocion, veces_aplicable if promocion.escalable else 1)
    resultado['bonificaciones'].extend(beneficios_generales['bonificaciones'])
    resultado['descuentos'].extend(beneficios_generales['descuentos'])
    
    resultado['aplica'] = True
    return resultado


def evaluar_promocion_sin_rangos(promocion, carrito_detalle, productos_validos):
    resultado = {
        'aplica': False,
        'bonificaciones': [],
        'descuentos': [],
        'razon': ''
    }
    
    # Verificar monto mínimo si está especificado
    if promocion.monto_minimo and productos_validos['monto_total'] < promocion.monto_minimo:
        resultado['razon'] = f"Monto insuficiente: S/{productos_validos['monto_total']} < S/{promocion.monto_minimo}"
        return resultado
    
    # Calcular escalabilidad si aplica
    veces_aplicable = 1
    if promocion.escalable:
        # Para promociones sin rangos, usar el monto o cantidad total
        if promocion.monto_minimo:
            veces_aplicable = int(productos_validos['monto_total'] // promocion.monto_minimo)
        else:
            veces_aplicable = 1
            
    beneficios_generales = aplicar_beneficios_generales(promocion, veces_aplicable)
    resultado['bonificaciones'].extend(beneficios_generales['bonificaciones'])
    resultado['descuentos'].extend(beneficios_generales['descuentos'])
    
    if beneficios_generales['bonificaciones'] or beneficios_generales['descuentos']:
        resultado['aplica'] = True
    else:
        resultado['razon'] = "No hay beneficios configurados para esta promoción"
    
    return resultado


def aplicar_beneficios_generales(promocion, veces_aplicable=1):
    resultado = {
        'bonificaciones': [],
        'descuentos': []
    }
    
    beneficios = Beneficio.objects.filter(promocion=promocion)
    
    for beneficio in beneficios:        
        # Descuento general
        if beneficio.descuento and beneficio.descuento > 0:
            descuento = {
                'tipo': 'general',
                'porcentaje': float(beneficio.descuento),
                'monto_descuento': 0,  # Se calculará en la vista
                'escalable': promocion.escalable,
                'veces_aplicable': veces_aplicable
            }
            resultado['descuentos'].append(descuento)
        
        # Productos beneficiados
        productos_beneficios = ProductosBeneficios.objects.filter(beneficio=beneficio)
        
        for prod_benef in productos_beneficios:
            cantidad_bonificar = prod_benef.cantidad * veces_aplicable
            
            bonificacion = {
                'articulo': prod_benef.articulo,
                'cantidad': cantidad_bonificar,
                'escalable': promocion.escalable,
                'veces_aplicable': veces_aplicable
            }
            
            resultado['bonificaciones'].append(bonificacion)
    
    return resultado

#comentario para poder hacer el commit y ver si funciona