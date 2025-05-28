from datetime import date
from decimal import Decimal
from django.utils import timezone
from django.db.models import Q
from .models import Bonificacion, BonificacionPorIntervalo, Descuento, Promocion, EstadoEntidades, PromocionProducto, VerificacionProducto

class MotorPromociones:
    """
    Motor de promociones COMPLETO que evalúa qué promociones aplican a un carrito
    y calcula los beneficios correspondientes con soporte completo para Caso 9
    """
    
    def __init__(self):
        self.promociones_aplicadas = []
        self.bonificaciones = []
        self.descuentos = []
        self.errores = []

    def evaluar_promociones(self, carrito_detalle, cliente=None, empresa=None, sucursal=None):
        """
        Método principal que evalúa todas las promociones aplicables
        """
        try:
            # Reiniciar variables
            self.promociones_aplicadas = []
            self.bonificaciones = []
            self.descuentos = []
            self.errores = []

            if not carrito_detalle:
                return self._construir_respuesta()

            print(f"🛒 Evaluando promociones para carrito con {len(carrito_detalle)} productos")

            # Obtener promociones activas
            promociones_activas = self._obtener_promociones_activas(empresa, sucursal, cliente)
            
            if not promociones_activas:
                print("ℹ️ No se encontraron promociones activas")
                return self._construir_respuesta()

            print(f"🎯 Evaluando {len(promociones_activas)} promociones activas")

            # Evaluar cada promoción
            for promocion in promociones_activas:
                try:
                    print(f"\n🔍 Evaluando promoción: {promocion.nombre}")
                    self._evaluar_promocion_individual(promocion, carrito_detalle)
                except Exception as e:
                    error_msg = f"Error evaluando promoción {promocion.nombre}: {str(e)}"
                    print(f"❌ {error_msg}")
                    self.errores.append(error_msg)

            return self._construir_respuesta()

        except Exception as e:
            error_msg = f"Error general en motor de promociones: {str(e)}"
            print(f"🚨 {error_msg}")
            self.errores.append(error_msg)
            return self._construir_respuesta()

    def _obtener_promociones_activas(self, empresa=None, sucursal=None, cliente=None):
        """
        Obtiene las promociones activas según criterios de filtrado
        """
        hoy = date.today()
        
        filtros = Q(
            fecha_inicio__lte=hoy,
            fecha_fin__gte=hoy,
            estado=1  # Activo
        )

        if empresa:
            filtros &= Q(empresa=empresa)
        
        if sucursal:
            filtros &= Q(Q(sucursal=sucursal) | Q(sucursal__isnull=True))
        
        if cliente and cliente.canal_cliente:
            filtros &= Q(Q(canal_cliente=cliente.canal_cliente) | Q(canal_cliente__isnull=True))

        promociones = Promocion.objects.filter(filtros).select_related(
            'empresa', 'sucursal', 'canal_cliente', 'tipo_beneficio'
        ).prefetch_related(
            'productos', 'bonificaciones', 'descuentos', 'verificaciones'
        )

        print(f"📋 Filtros aplicados - Empresa: {empresa}, Sucursal: {sucursal}, Cliente: {cliente}")
        print(f"📅 Fecha actual: {hoy}")
        
        return promociones

    def _evaluar_promocion_individual(self, promocion, carrito_detalle):
        """
        Evalúa una promoción específica contra el carrito
        """
        print(f"   🔎 Verificando productos condición...")
        
        # Verificar si hay productos específicos requeridos
        if not self._verificar_productos_condicion(promocion, carrito_detalle):
            print(f"   ❌ No cumple productos condición")
            return

        print(f"   ✅ Cumple productos condición")
        print(f"   🎯 Tipo condición: {promocion.tipo_condicion}")

        # Verificar condiciones según tipo
        if promocion.tipo_condicion == 'cantidad':
            self._evaluar_condicion_cantidad(promocion, carrito_detalle)
        elif promocion.tipo_condicion == 'monto':
            self._evaluar_condicion_monto(promocion, carrito_detalle)
        else:
            # Para promociones sin condición específica (solo verificar productos)
            self._aplicar_beneficios_promocion(promocion, carrito_detalle)

    def _verificar_productos_condicion(self, promocion, carrito_detalle):
        """
        Verifica si el carrito contiene los productos requeridos para la promoción
        """
        # Verificar si es promoción por línea/marca (Casos 2, 5 del PDF)
        if promocion.grupo_proveedor_id or promocion.linea_articulo_id:
            return self._verificar_promocion_linea_marca(promocion, carrito_detalle)
        
        # Obtener productos requeridos para esta promoción
        productos_requeridos = VerificacionProducto.objects.filter(promocion=promocion)
        
        if not productos_requeridos.exists():
            # Si no hay productos específicos requeridos, la promoción aplica
            return True

        # Verificar cada producto requerido
        articulos_carrito = {str(detalle.articulo.articulo_id): detalle for detalle in carrito_detalle}
        
        for producto_req in productos_requeridos:
            articulo_id = str(producto_req.articulo.articulo_id)
            if articulo_id not in articulos_carrito:
                print(f"   ❌ Falta producto requerido: {producto_req.articulo.descripcion}")
                return False

        print(f"   ✅ Todos los productos requeridos están en el carrito")
        return True

    def _evaluar_condicion_cantidad(self, promocion, carrito_detalle):
        """
        Evalúa promociones basadas en cantidad de productos
        """
        print(f"   🔢 Evaluando condición por cantidad...")
        
        productos_promocion = PromocionProducto.objects.filter(promocion=promocion)
        
        for producto_promo in productos_promocion:
            # Buscar el producto en el carrito
            detalle_producto = None
            for detalle in carrito_detalle:
                if detalle.articulo.articulo_id == producto_promo.articulo.articulo_id:
                    detalle_producto = detalle
                    break
            
            if not detalle_producto:
                print(f"   ❌ Producto {producto_promo.articulo.descripcion} no está en carrito")
                continue

            cantidad_carrito = detalle_producto.cantidad
            print(f"   📦 Producto: {producto_promo.articulo.descripcion}")
            print(f"   📊 Cantidad en carrito: {cantidad_carrito}")
            print(f"   📏 Rango: {producto_promo.cantidad_min}-{producto_promo.cantidad_max or '∞'}")
            
            # Verificar si cumple con las condiciones de cantidad
            if self._cumple_condicion_cantidad(cantidad_carrito, producto_promo):
                print(f"   ✅ Cumple condición de cantidad")
                self._aplicar_beneficios_por_cantidad(promocion, producto_promo, cantidad_carrito)
            else:
                print(f"   ❌ No cumple condición de cantidad")

    def _cumple_condicion_cantidad(self, cantidad_carrito, producto_promo):
        """
        Verifica si la cantidad del carrito cumple con las condiciones del producto promocional
        """
        if producto_promo.cantidad_min and cantidad_carrito < producto_promo.cantidad_min:
            return False
        
        if producto_promo.cantidad_max and cantidad_carrito > producto_promo.cantidad_max:
            return False
        
        return True

    def _aplicar_beneficios_por_cantidad(self, promocion, producto_promo, cantidad_carrito):
        """
        Aplica beneficios específicos por cantidad
        """
        if promocion not in self.promociones_aplicadas:
            self.promociones_aplicadas.append(promocion)

        # Calcular cuántas veces aplica la promoción
        if promocion.escalable:
            # Promoción escalable: se aplica múltiples veces
            veces_aplicable = cantidad_carrito // (producto_promo.cantidad_min or 1)
            print(f"   🔄 Promoción escalable: {cantidad_carrito} ÷ {producto_promo.cantidad_min} = {veces_aplicable} veces")
        else:
            # Promoción no escalable: se aplica solo una vez si cumple la condición
            veces_aplicable = 1 if cantidad_carrito >= (producto_promo.cantidad_min or 1) else 0
            print(f"   🎯 Promoción única: aplica {veces_aplicable} vez")

        # Si el tipo de selección es porcentaje, aplicar descuento
        if producto_promo.tipo_seleccion == 'porcentaje' and producto_promo.valor:
            self.descuentos.append({
                'promocion': promocion,
                'tipo': 'porcentaje_producto',
                'porcentaje': float(producto_promo.valor),
                'articulo': producto_promo.articulo,
                'monto_descuento': 0,  # Se calculará al aplicar
                'escalable': promocion.escalable,
                'veces_aplicable': veces_aplicable
            })
            print(f"   💰 Descuento agregado: {producto_promo.valor}%")

        # Si el tipo de selección es producto, aplicar bonificación
        elif producto_promo.tipo_seleccion == 'producto' and producto_promo.valor:
            cantidad_bonificada = int(producto_promo.valor) * veces_aplicable
            
            if cantidad_bonificada > 0:
                self.bonificaciones.append({
                    'promocion': promocion,
                    'articulo': producto_promo.articulo,
                    'cantidad': cantidad_bonificada,
                    'escalable': promocion.escalable,
                    'veces_aplicable': veces_aplicable
                })
                print(f"   🎁 Bonificación agregada: {cantidad_bonificada} unidades ({veces_aplicable} veces)")

        # Aplicar bonificaciones adicionales de la promoción
        self._aplicar_bonificaciones_promocion(promocion, veces_aplicable)

    def _evaluar_condicion_monto(self, promocion, carrito_detalle):
        """
        VERSIÓN MEJORADA - Evalúa promociones basadas en monto de compra con soporte completo para Caso 9
        """
        print(f"   💰 Evaluando condición por monto...")
        
        # Calcular monto total del carrito (considerando filtros de línea/marca si aplica)
        monto_total = self._calcular_monto_aplicable(promocion, carrito_detalle)
        
        if monto_total <= 0:
            print(f"   ❌ Monto aplicable es 0")
            return

        print(f"   💰 Monto aplicable del carrito: S/{monto_total}")

        # Verificar si es promoción combinada por monto (Caso 9)
        if promocion.es_promocion_combinada_por_monto or self._tiene_bonificaciones_por_intervalo(promocion):
            print(f"   🎯 Detectada promoción combinada por monto (Caso 9)")
            self._evaluar_promocion_combinada_monto(promocion, monto_total)
        else:
            print(f"   📋 Promoción simple por monto")
            self._evaluar_promocion_simple_monto(promocion, monto_total)

    def _tiene_bonificaciones_por_intervalo(self, promocion):
        """
        Verifica si la promoción tiene bonificaciones específicas por intervalo de monto
        """
        return BonificacionPorIntervalo.objects.filter(
            bonificacion__promocion=promocion
        ).exists()

    def _evaluar_promocion_combinada_monto(self, promocion, monto_total):
        """
        NUEVO - Evalúa promociones combinadas por monto (Caso 9)
        """
        print(f"   🔄 Evaluando promoción combinada por monto (Caso 9)")
        
        if promocion not in self.promociones_aplicadas:
            self.promociones_aplicadas.append(promocion)

        # Evaluar descuentos por rangos de monto
        descuentos_aplicados = self._aplicar_descuentos_por_monto(promocion, monto_total)
        
        # Evaluar bonificaciones específicas por intervalo
        bonificaciones_aplicadas = self._aplicar_bonificaciones_por_intervalo(promocion, monto_total)
        
        print(f"   ✅ Promoción combinada aplicada:")
        print(f"      - Descuentos: {len(descuentos_aplicados)}")
        print(f"      - Bonificaciones por intervalo: {len(bonificaciones_aplicadas)}")

    def _evaluar_promocion_simple_monto(self, promocion, monto_total):
        """
        Evalúa promociones simples por monto (Casos 2, 5, 6, 10, 11)
        """
        # Verificar descuentos por rangos de monto
        descuentos_promocion = Descuento.objects.filter(promocion=promocion).order_by('valor_minimo')
        
        for descuento in descuentos_promocion:
            if self._cumple_condicion_monto(monto_total, descuento):
                if promocion not in self.promociones_aplicadas:
                    self.promociones_aplicadas.append(promocion)
                
                # Calcular monto de descuento
                monto_descuento = monto_total * (descuento.porcentaje / 100) if descuento.porcentaje else 0
                
                self.descuentos.append({
                    'promocion': promocion,
                    'tipo': 'monto_total',
                    'porcentaje': float(descuento.porcentaje) if descuento.porcentaje else 0,
                    'monto_descuento': float(monto_descuento),
                    'monto_base': float(monto_total),
                    'escalable': promocion.escalable,
                    'veces_aplicable': self._calcular_veces_aplicables_monto(promocion, monto_total)
                })
                
                print(f"   💰 Descuento simple aplicado: {descuento.porcentaje}% sobre S/{monto_total}")

                # Aplicar bonificaciones generales si las hay
                self._aplicar_bonificaciones_promocion(promocion)
                break  # Solo aplicar el primer rango que cumpla

    def _aplicar_descuentos_por_monto(self, promocion, monto_total):
        """
        Aplica descuentos por monto para promociones combinadas
        """
        descuentos_aplicados = []
        descuentos_promocion = Descuento.objects.filter(promocion=promocion).order_by('valor_minimo')
        
        for descuento in descuentos_promocion:
            if self._cumple_condicion_monto(monto_total, descuento):
                # Calcular monto de descuento
                monto_descuento = monto_total * (descuento.porcentaje / 100) if descuento.porcentaje else 0
                
                descuento_aplicado = {
                    'promocion': promocion,
                    'tipo': 'monto_total_combinado',
                    'porcentaje': float(descuento.porcentaje) if descuento.porcentaje else 0,
                    'monto_descuento': float(monto_descuento),
                    'monto_base': float(monto_total),
                    'intervalo_min': float(descuento.valor_minimo),
                    'intervalo_max': float(descuento.valor_maximo) if descuento.valor_maximo else None,
                    'escalable': promocion.escalable,
                    'veces_aplicable': 1
                }
                
                self.descuentos.append(descuento_aplicado)
                descuentos_aplicados.append(descuento_aplicado)
                
                print(f"      💰 Descuento aplicado: {descuento.porcentaje}% sobre S/{monto_total} = S/{monto_descuento}")
                break  # Solo aplicar el primer rango que cumpla
        
        return descuentos_aplicados

    def _aplicar_bonificaciones_por_intervalo(self, promocion, monto_total):
        """
        NUEVO - Aplica bonificaciones específicas por intervalo de monto (Caso 9)
        """
        bonificaciones_aplicadas = []
        
        # Obtener todas las bonificaciones con intervalos para esta promoción
        bonificaciones_intervalo = BonificacionPorIntervalo.objects.filter(
            bonificacion__promocion=promocion
        ).select_related('bonificacion', 'bonificacion__articulo').order_by('valor_minimo')
        
        print(f"      📋 Bonificaciones por intervalo encontradas: {bonificaciones_intervalo.count()}")
        
        for bonif_intervalo in bonificaciones_intervalo:
            print(f"      🔍 Verificando intervalo S/{bonif_intervalo.valor_minimo}-{bonif_intervalo.valor_maximo or '∞'}")
            
            # Verificar si el monto está en este intervalo
            if self._monto_en_intervalo(monto_total, bonif_intervalo.valor_minimo, bonif_intervalo.valor_maximo):
                print(f"      ✅ Monto S/{monto_total} está en intervalo")
                
                # Calcular cantidad bonificada
                cantidad_bonificada = bonif_intervalo.bonificacion.cantidad
                
                # Si la promoción es escalable, calcular veces aplicables
                if promocion.escalable:
                    veces_aplicable = self._calcular_veces_aplicables_monto(promocion, monto_total)
                    cantidad_bonificada *= veces_aplicable
                else:
                    veces_aplicable = 1
                
                bonificacion_aplicada = {
                    'promocion': promocion,
                    'articulo': bonif_intervalo.bonificacion.articulo,
                    'cantidad': cantidad_bonificada,
                    'intervalo_min': float(bonif_intervalo.valor_minimo),
                    'intervalo_max': float(bonif_intervalo.valor_maximo) if bonif_intervalo.valor_maximo else None,
                    'escalable': promocion.escalable,
                    'veces_aplicable': veces_aplicable,
                    'tipo_bonificacion': 'por_intervalo_monto'
                }
                
                self.bonificaciones.append(bonificacion_aplicada)
                bonificaciones_aplicadas.append(bonificacion_aplicada)
                
                print(f"      🎁 Bonificación por intervalo agregada: {cantidad_bonificada} unidades de {bonif_intervalo.bonificacion.articulo.descripcion}")
                break  # Solo aplicar el primer intervalo que cumpla
            else:
                print(f"      ❌ Monto no está en este intervalo")
        
        return bonificaciones_aplicadas

    def _monto_en_intervalo(self, monto, valor_minimo, valor_maximo):
        """
        Verifica si un monto está dentro de un intervalo específico
        """
        if monto < valor_minimo:
            return False
        
        if valor_maximo and monto > valor_maximo:
            return False
        
        return True

    def _calcular_veces_aplicables_monto(self, promocion, monto_total):
        """
        Calcula cuántas veces es aplicable una promoción escalable por monto
        """
        if not promocion.escalable or not promocion.monto_minimo:
            return 1
        
        return int(monto_total // promocion.monto_minimo)

    def _calcular_monto_aplicable(self, promocion, carrito_detalle):
        """
        Calcula el monto del carrito que aplica para la promoción
        considerando filtros de línea y marca
        """
        monto_total = Decimal('0')
        
        for detalle in carrito_detalle:
            articulo = detalle.articulo
            
            # Si la promoción es solo para línea y marca específica
            if promocion.grupo_proveedor_id or promocion.linea_articulo_id:
                if promocion.grupo_proveedor_id and str(articulo.grupo_proveedor.grupo_proveedor_id) != str(promocion.grupo_proveedor_id):
                    continue
                if promocion.linea_articulo_id and str(articulo.linea_articulo.linea_articulo_id) != str(promocion.linea_articulo_id):
                    continue
            
            monto_total += articulo.precio * detalle.cantidad
        
        return monto_total

    def _verificar_promocion_linea_marca(self, promocion, carrito_detalle):
        """
        Verifica si el carrito contiene productos de la línea/marca especificada
        """
        if not promocion.grupo_proveedor_id and not promocion.linea_articulo_id:
            return True  # No hay filtro específico
        
        for detalle in carrito_detalle:
            articulo = detalle.articulo
            
            # Verificar marca si está especificada
            if promocion.grupo_proveedor_id:
                if str(articulo.grupo_proveedor.grupo_proveedor_id) != str(promocion.grupo_proveedor_id):
                    continue
            
            # Verificar línea si está especificada
            if promocion.linea_articulo_id:
                if str(articulo.linea_articulo.linea_articulo_id) != str(promocion.linea_articulo_id):
                    continue
            
            return True  # Encontró al menos un producto que cumple
        
        return False

    def _cumple_condicion_monto(self, monto_total, descuento):
        """
        Verifica si el monto total cumple con las condiciones del descuento
        """
        if descuento.valor_minimo and monto_total < descuento.valor_minimo:
            return False
        
        if descuento.valor_maximo and monto_total > descuento.valor_maximo:
            return False
        
        return True

    def _aplicar_beneficios_promocion(self, promocion, carrito_detalle=None):
        """
        Aplica los beneficios generales de una promoción
        """
        if promocion not in self.promociones_aplicadas:
            self.promociones_aplicadas.append(promocion)

        # Para promociones escalables por monto, calcular veces aplicables
        veces_aplicable = 1
        if promocion.escalable and promocion.tipo_condicion == 'monto' and carrito_detalle:
            monto_total = self._calcular_monto_aplicable(promocion, carrito_detalle)
            monto_minimo = promocion.monto_minimo or Decimal('0')
            if monto_minimo > 0:
                veces_aplicable = int(monto_total // monto_minimo)

        # Aplicar bonificaciones
        self._aplicar_bonificaciones_promocion(promocion, veces_aplicable)
        
        # Aplicar descuentos generales
        descuentos_generales = Descuento.objects.filter(
            promocion=promocion,
            valor_minimo__isnull=True,
            valor_maximo__isnull=True
        )
        
        for descuento in descuentos_generales:
            if descuento.porcentaje:
                self.descuentos.append({
                    'promocion': promocion,
                    'tipo': 'general',
                    'porcentaje': float(descuento.porcentaje),
                    'monto_descuento': 0,  # Se calculará al aplicar
                    'escalable': promocion.escalable,
                    'veces_aplicable': veces_aplicable
                })

    def _aplicar_bonificaciones_promocion(self, promocion, veces_aplicable=1):
        """
        Aplica las bonificaciones definidas para una promoción
        """
        bonificaciones_promocion = Bonificacion.objects.filter(promocion=promocion)
        
        for bonificacion in bonificaciones_promocion:
            # Si la promoción es escalable, multiplicar por las veces aplicables
            cantidad_final = bonificacion.cantidad * veces_aplicable
            
            self.bonificaciones.append({
                'promocion': promocion,
                'articulo': bonificacion.articulo,
                'cantidad': cantidad_final,
                'escalable': promocion.escalable,
                'veces_aplicable': veces_aplicable
            })
            print(f"   🎁 Bonificación adicional: {cantidad_final} unidades de {bonificacion.articulo.descripcion}")

    def _construir_respuesta(self, ):
        """
        Construye la respuesta final con todos los beneficios aplicables
        """
        # Calcular totales
        total_descuento = sum(desc.get('monto_descuento', 0) for desc in self.descuentos)
        total_bonificaciones = len(self.bonificaciones)
        
        respuesta = {
            'promociones_aplicadas': self.promociones_aplicadas,
            'bonificaciones': self.bonificaciones,
            'descuentos': self.descuentos,
            'errores': self.errores,
            'total_descuento': total_descuento,
            'total_bonificaciones': total_bonificaciones
        }
        
        # Debug de respuesta final
        print(f"\n📊 RESUMEN FINAL:")
        print(f"   🎉 Promociones aplicadas: {len(self.promociones_aplicadas)}")
        for promo in self.promociones_aplicadas:
            escalable_info = " (Escalable)" if promo.escalable else ""
            tipo_info = " - Caso 9" if promo.es_promocion_combinada_por_monto else ""
            print(f"      - {promo.nombre}{escalable_info}{tipo_info}")
        
        print(f"   🎁 Total bonificaciones: {total_bonificaciones}")
        for bonif in self.bonificaciones:
            tipo_info = f" [{bonif.get('tipo_bonificacion', 'general')}]" if bonif.get('tipo_bonificacion') else ""
            print(f"      - {bonif['cantidad']} x {bonif['articulo'].descripcion}{tipo_info}")
        
        print(f"   💰 Total descuentos: {len(self.descuentos)} (S/{total_descuento})")
        for desc in self.descuentos:
            print(f"      - {desc.get('porcentaje', 0)}% = S/{desc.get('monto_descuento', 0)}")
        
        if self.errores:
            print(f"   ❌ Errores: {len(self.errores)}")
            for error in self.errores:
                print(f"      - {error}")
        
        return respuesta


def evaluar_promociones(carrito_detalle, cliente=None, empresa=None, sucursal=None):
    """
    Función principal para evaluar promociones desde las vistas
    """
    print(f"\n🔥 INICIANDO EVALUACIÓN DE PROMOCIONES")
    print(f"   🛒 Productos en carrito: {len(carrito_detalle) if carrito_detalle else 0}")
    print(f"   👤 Cliente: {cliente.usuario.nombre if cliente and cliente.usuario else 'Anónimo'}")
    print(f"   🏢 Empresa: {empresa.nombre if empresa else 'No especificada'}")
    print(f"   🏪 Sucursal: {sucursal.nombre if sucursal else 'No especificada'}")
    
    motor = MotorPromociones()
    resultado = motor.evaluar_promociones(carrito_detalle, cliente, empresa, sucursal)
    
    print(f"🏁 EVALUACIÓN COMPLETADA\n")
    return resultado


# FUNCIÓN AUXILIAR PARA DEBUGGING DEL CASO 9
def debug_evaluacion_caso9(promocion, monto_total):
    """
    Función de debugging específica para el Caso 9
    """
    print("\n=== DEBUG CASO 9 ===")
    print(f"Promoción: {promocion.nombre}")
    print(f"Monto total: S/{monto_total}")
    print(f"Es promoción combinada: {promocion.es_promocion_combinada_por_monto}")
    
    # Mostrar descuentos configurados
    descuentos = Descuento.objects.filter(promocion=promocion)
    print(f"\nDescuentos configurados: {descuentos.count()}")
    for desc in descuentos:
        print(f"  - S/{desc.valor_minimo}-{desc.valor_maximo or '∞'}: {desc.porcentaje}%")
    
    # Mostrar bonificaciones por intervalo
    bonificaciones_intervalo = BonificacionPorIntervalo.objects.filter(
        bonificacion__promocion=promocion
    )
    print(f"\nBonificaciones por intervalo: {bonificaciones_intervalo.count()}")
    for bonif in bonificaciones_intervalo:
        print(f"  - S/{bonif.valor_minimo}-{bonif.valor_maximo or '∞'}: {bonif.bonificacion.cantidad} unidades {bonif.bonificacion.articulo.descripcion}")
    
    print("=== FIN DEBUG CASO 9 ===\n")