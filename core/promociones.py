# core/promociones.py - Motor de Evaluación de Promociones
from decimal import Decimal
from datetime import datetime
from django.utils import timezone
from django.db.models import Q, Sum
from typing import Dict, List, Any, Optional
import uuid

from .models import (
    Promocion, Rango, ProductoBonificadoRango, Beneficio, ProductosBeneficios,
    VerificacionProducto, Articulo, DetalleCarrito, Cliente, CanalCliente
)


def evaluar_promociones(carrito_detalle, cliente, empresa=None, sucursal=None):
    """
    Función principal que evalúa todas las promociones aplicables a un carrito
    
    Args:
        carrito_detalle: QuerySet de DetalleCarrito
        cliente: Instancia de Cliente
        empresa: Instancia de Empresa (opcional)
        sucursal: Instancia de Sucursal (opcional)
    
    Returns:
        Dict con promociones aplicadas y beneficios
    """
    
    print(f"\n🚀 === INICIANDO EVALUACIÓN DE PROMOCIONES ===")
    print(f"📅 Fecha actual: {timezone.now().date()}")
    print(f"👤 Cliente: {cliente}")
    print(f"🏢 Empresa: {empresa}")
    print(f"🏪 Sucursal: {sucursal}")
    print(f"🛒 Productos en carrito: {carrito_detalle.count()}")
    
    resultado = {
        'promociones_aplicadas': [],
        'bonificaciones': [],
        'descuentos': [],
        'errores': []
    }
    
    try:
        # 1. Obtener promociones elegibles
        promociones_elegibles = obtener_promociones_elegibles(cliente, empresa, sucursal)
        
        if not promociones_elegibles:
            print("❌ No hay promociones elegibles para este cliente/empresa")
            return resultado
        
        print(f"✅ Promociones elegibles encontradas: {len(promociones_elegibles)}")
        
        # 2. Evaluar cada promoción
        for promocion in promociones_elegibles:
            print(f"\n🎯 === EVALUANDO PROMOCIÓN: {promocion.descripcion} ===")
            
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
                    
                    # Agregar bonificaciones
                    for bonif in beneficios_promocion['bonificaciones']:
                        bonif['promocion'] = promocion
                        resultado['bonificaciones'].append(bonif)
                    
                    # Agregar descuentos
                    for desc in beneficios_promocion['descuentos']:
                        desc['promocion'] = promocion
                        resultado['descuentos'].append(desc)
                    
                    print(f"✅ Promoción aplicada exitosamente")
                else:
                    print(f"⚠️ Promoción no aplica: {beneficios_promocion.get('razon', 'Razón desconocida')}")
                    
            except Exception as e:
                error_msg = f"Error evaluando promoción {promocion.descripcion}: {str(e)}"
                print(f"❌ {error_msg}")
                resultado['errores'].append(error_msg)
        
        print(f"\n✅ === EVALUACIÓN COMPLETADA ===")
        print(f"🎉 Promociones aplicadas: {len(resultado['promociones_aplicadas'])}")
        print(f"🎁 Bonificaciones: {len(resultado['bonificaciones'])}")
        print(f"💰 Descuentos: {len(resultado['descuentos'])}")
        
        return resultado
        
    except Exception as e:
        error_msg = f"Error general en evaluación de promociones: {str(e)}"
        print(f"❌ {error_msg}")
        resultado['errores'].append(error_msg)
        return resultado


def obtener_promociones_elegibles(cliente, empresa=None, sucursal=None):
    """
    Obtiene promociones que cumplen los filtros básicos de elegibilidad
    """
    hoy = timezone.now().date()
    
    # Filtros básicos
    filtros = Q(
        estado=1,  # Promociones activas
        fecha_inicio__lte=hoy,  # Ya comenzaron
        fecha_fin__gte=hoy      # Aún vigentes
    )
    
    # Filtro por canal de cliente
    if cliente and hasattr(cliente, 'canal_cliente'):
        filtros &= Q(canal_cliente=cliente.canal_cliente)
        print(f"🎯 Filtro por canal: {cliente.canal_cliente}")
    
    # Filtro por empresa
    if empresa:
        filtros &= Q(empresa=empresa)
        print(f"🏢 Filtro por empresa: {empresa}")
    
    # Filtro por sucursal (opcional, algunas promociones aplican a todas)
    if sucursal:
        filtros &= Q(Q(sucursal=sucursal) | Q(sucursal__isnull=True))
        print(f"🏪 Filtro por sucursal: {sucursal}")
    
    promociones = Promocion.objects.filter(filtros).order_by('promocion_id')
    
    print(f"📊 Promociones elegibles: {promociones.count()}")
    for promo in promociones:
        escalable_text = " (ESCALABLE)" if promo.escalable else ""
        print(f"   - {promo.descripcion}{escalable_text}")
    
    return promociones


def evaluar_promocion_individual(promocion, carrito_detalle, cliente):
    """
    Evalúa una promoción específica contra el carrito
    """
    resultado = {
        'aplica': False,
        'bonificaciones': [],
        'descuentos': [],
        'razon': ''
    }
    
    try:
        # 1. Verificar productos requeridos
        productos_validos = verificar_productos_requeridos(promocion, carrito_detalle)
        
        if not productos_validos['cumple']:
            resultado['razon'] = productos_validos['razon']
            return resultado
        
        # 2. Evaluar rangos (si existen)
        rangos = Rango.objects.filter(promocion=promocion).order_by('minimo')
        
        if rangos.exists():
            print(f"🎯 Evaluando {rangos.count()} rangos")
            return evaluar_promocion_con_rangos(promocion, carrito_detalle, productos_validos, rangos)
        else:
            print(f"🎁 Evaluando beneficios generales (sin rangos)")
            return evaluar_promocion_sin_rangos(promocion, carrito_detalle, productos_validos)
            
    except Exception as e:
        resultado['razon'] = f"Error en evaluación: {str(e)}"
        print(f"❌ {resultado['razon']}")
        return resultado


def verificar_productos_requeridos(promocion, carrito_detalle):
    """
    Verifica si el carrito cumple con los productos requeridos por la promoción
    """
    resultado = {
        'cumple': False,
        'productos_aplicables': [],
        'cantidad_total': 0,
        'monto_total': Decimal('0'),
        'razon': ''
    }
    
    # CASO 1: Promoción por marca/línea completa
    if promocion.grupo_proveedor_id or promocion.linea_articulo_id:
        print(f"🏷️ Verificando por marca/línea")
        
        filtros_productos = Q()
        
        if promocion.grupo_proveedor_id:
            filtros_productos &= Q(articulo__grupo_proveedor_id=promocion.grupo_proveedor_id)
            print(f"   📦 Marca: {promocion.grupo_proveedor_id}")
        
        if promocion.linea_articulo_id:
            filtros_productos &= Q(articulo__linea_articulo_id=promocion.linea_articulo_id)
            print(f"   📋 Línea: {promocion.linea_articulo_id}")
        
        productos_aplicables = carrito_detalle.filter(filtros_productos)
        
        if not productos_aplicables.exists():
            resultado['razon'] = "No hay productos de la marca/línea especificada en el carrito"
            return resultado
        
        # Calcular totales
        for detalle in productos_aplicables:
            resultado['productos_aplicables'].append(detalle)
            resultado['cantidad_total'] += detalle.cantidad
            resultado['monto_total'] += detalle.articulo.precio * detalle.cantidad
        
        # Verificar monto mínimo si está especificado
        if promocion.monto_minimo and resultado['monto_total'] < promocion.monto_minimo:
            resultado['razon'] = f"Monto insuficiente: S/{resultado['monto_total']} < S/{promocion.monto_minimo}"
            return resultado
        
        print(f"   ✅ Productos aplicables: {len(resultado['productos_aplicables'])}")
        print(f"   📊 Cantidad total: {resultado['cantidad_total']}")
        print(f"   💰 Monto total: S/{resultado['monto_total']}")
        
        resultado['cumple'] = True
        return resultado
    
    # CASO 2: Productos específicos
    verificaciones = VerificacionProducto.objects.filter(promocion=promocion)
    
    if verificaciones.exists():
        print(f"📦 Verificando productos específicos ({verificaciones.count()} requeridos)")
        
        productos_requeridos = [v.articulo_id for v in verificaciones]
        productos_en_carrito = []
        
        for detalle in carrito_detalle:
            if detalle.articulo.articulo_id in productos_requeridos:
                productos_en_carrito.append(detalle.articulo.articulo_id)
                resultado['productos_aplicables'].append(detalle)
                resultado['cantidad_total'] += detalle.cantidad
                resultado['monto_total'] += detalle.articulo.precio * detalle.cantidad
        
        # Verificar que TODOS los productos requeridos están presentes
        productos_faltantes = set(productos_requeridos) - set(productos_en_carrito)
        
        if productos_faltantes:
            resultado['razon'] = f"Faltan productos requeridos: {len(productos_faltantes)} de {len(productos_requeridos)}"
            return resultado
        
        print(f"   ✅ Productos específicos encontrados: {len(resultado['productos_aplicables'])}")
        resultado['cumple'] = True
        return resultado
    
    # CASO 3: Sin restricciones específicas (promoción general)
    print(f"🌟 Promoción general (sin restricciones de productos)")
    
    for detalle in carrito_detalle:
        resultado['productos_aplicables'].append(detalle)
        resultado['cantidad_total'] += detalle.cantidad
        resultado['monto_total'] += detalle.articulo.precio * detalle.cantidad
    
    resultado['cumple'] = True
    return resultado


def evaluar_promocion_con_rangos(promocion, carrito_detalle, productos_validos, rangos):
    """
    Evalúa promociones que tienen rangos de cantidad o monto
    """
    resultado = {
        'aplica': False,
        'bonificaciones': [],
        'descuentos': [],
        'razon': ''
    }
    
    # Determinar el tipo de rango (cantidad o monto)
    primer_rango = rangos.first()
    tipo_rango = primer_rango.tipo_rango
    
    print(f"📊 Tipo de rango: {tipo_rango}")
    
    # Calcular valor a comparar
    if tipo_rango == 'cantidad':
        valor_comparar = productos_validos['cantidad_total']
        print(f"🔢 Cantidad total a evaluar: {valor_comparar}")
    else:  # monto
        valor_comparar = float(productos_validos['monto_total'])
        print(f"💰 Monto total a evaluar: S/{valor_comparar}")
    
    # Encontrar rango aplicable
    rango_aplicable = None
    for rango in rangos:
        if valor_comparar >= rango.minimo:
            if rango.maximo is None or valor_comparar <= rango.maximo:
                rango_aplicable = rango
                print(f"🎯 Rango aplicable encontrado: {rango.minimo} - {rango.maximo or '∞'}")
                break
    
    if not rango_aplicable:
        resultado['razon'] = f"Valor {valor_comparar} no alcanza ningún rango"
        return resultado
    
    # Calcular escalabilidad si aplica
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
            'monto_descuento': 0,  # Se calculará en la vista
            'escalable': promocion.escalable,
            'veces_aplicable': veces_aplicable
        }
        
        # Calcular monto de descuento
        if tipo_rango == 'monto':
            monto_base = productos_validos['monto_total']
        else:
            # Para rangos de cantidad, aplicar descuento al monto de los productos aplicables
            monto_base = productos_validos['monto_total']
        
        descuento['monto_descuento'] = float(monto_base * Decimal(str(rango_aplicable.descuento)) / 100)
        
        if promocion.escalable:
            descuento['monto_descuento'] *= veces_aplicable
        
        resultado['descuentos'].append(descuento)
        print(f"💰 Descuento aplicado: {rango_aplicable.descuento}% = S/{descuento['monto_descuento']}")
    
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
        print(f"🎁 Bonificación: {cantidad_bonificar} x {prod_bonif.articulo.descripcion}")
    
    # Aplicar beneficios generales adicionales
    beneficios_generales = aplicar_beneficios_generales(promocion, veces_aplicable if promocion.escalable else 1)
    resultado['bonificaciones'].extend(beneficios_generales['bonificaciones'])
    resultado['descuentos'].extend(beneficios_generales['descuentos'])
    
    resultado['aplica'] = True
    return resultado


def evaluar_promocion_sin_rangos(promocion, carrito_detalle, productos_validos):
    """
    Evalúa promociones que NO tienen rangos (beneficios directos)
    """
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
            # Si no hay monto mínimo, usar cantidad (ejemplo: 4 cajas → 2 gratis, escalable)
            # Necesitaríamos un criterio base, por ahora usar 1
            veces_aplicable = 1
        
        print(f"♾️ Promoción escalable sin rangos: se aplicará {veces_aplicable} veces")
    
    # Aplicar beneficios generales
    beneficios_generales = aplicar_beneficios_generales(promocion, veces_aplicable)
    resultado['bonificaciones'].extend(beneficios_generales['bonificaciones'])
    resultado['descuentos'].extend(beneficios_generales['descuentos'])
    
    if beneficios_generales['bonificaciones'] or beneficios_generales['descuentos']:
        resultado['aplica'] = True
    else:
        resultado['razon'] = "No hay beneficios configurados para esta promoción"
    
    return resultado


def aplicar_beneficios_generales(promocion, veces_aplicable=1):
    """
    Aplica beneficios generales de la promoción (tabla Beneficio y ProductosBeneficios)
    """
    resultado = {
        'bonificaciones': [],
        'descuentos': []
    }
    
    beneficios = Beneficio.objects.filter(promocion=promocion)
    
    for beneficio in beneficios:
        print(f"🎁 Aplicando beneficio: {beneficio.get_tipo_beneficio_display()}")
        
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
            print(f"💰 Descuento general: {beneficio.descuento}%")
        
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
            print(f"🎁 Bonificación general: {cantidad_bonificar} x {prod_benef.articulo.descripcion}")
    
    return resultado


def debug_carrito_promociones(carrito_detalle, cliente):
    """
    Función de debug para analizar el carrito y promociones disponibles
    """
    print(f"\n🔍 === DEBUG CARRITO Y PROMOCIONES ===")
    print(f"👤 Cliente: {cliente}")
    print(f"🛒 Productos en carrito: {carrito_detalle.count()}")
    
    # Debug productos en carrito
    for detalle in carrito_detalle:
        print(f"   📦 {detalle.articulo.codigo} - {detalle.articulo.descripcion}")
        print(f"       Cantidad: {detalle.cantidad}")
        print(f"       Precio: S/{detalle.articulo.precio}")
        print(f"       Total: S/{detalle.articulo.precio * detalle.cantidad}")
        print(f"       Marca: {detalle.articulo.grupo_proveedor.nombre}")
        print(f"       Línea: {detalle.articulo.linea_articulo.nombre}")
    
    # Debug promociones disponibles
    if cliente and hasattr(cliente, 'canal_cliente'):
        promociones = Promocion.objects.filter(
            estado=1,
            canal_cliente=cliente.canal_cliente,
            fecha_inicio__lte=timezone.now().date(),
            fecha_fin__gte=timezone.now().date()
        )
        
        print(f"\n🎯 Promociones disponibles para {cliente.canal_cliente}: {promociones.count()}")
        
        for promo in promociones:
            print(f"   🎉 {promo.descripcion}")
            print(f"       Vigencia: {promo.fecha_inicio} - {promo.fecha_fin}")
            print(f"       Escalable: {'Sí' if promo.escalable else 'No'}")
            
            if promo.grupo_proveedor_id:
                print(f"       Marca: {promo.grupo_proveedor_id}")
            if promo.linea_articulo_id:
                print(f"       Línea: {promo.linea_articulo_id}")
            if promo.monto_minimo:
                print(f"       Monto mínimo: S/{promo.monto_minimo}")
    
    print(f"=== FIN DEBUG ===\n")


# Función de utilidad para testing
def test_promocion_caso_especifico(promocion_id, carrito_detalle, cliente):
    """
    Función para testear una promoción específica
    """
    try:
        promocion = Promocion.objects.get(promocion_id=promocion_id)
        resultado = evaluar_promocion_individual(promocion, carrito_detalle, cliente)
        
        print(f"\n🧪 === TEST PROMOCIÓN: {promocion.descripcion} ===")
        print(f"✅ Aplica: {resultado['aplica']}")
        if not resultado['aplica']:
            print(f"❌ Razón: {resultado['razon']}")
        else:
            print(f"🎁 Bonificaciones: {len(resultado['bonificaciones'])}")
            print(f"💰 Descuentos: {len(resultado['descuentos'])}")
        
        return resultado
        
    except Promocion.DoesNotExist:
        print(f"❌ Promoción {promocion_id} no encontrada")
        return None