from datetime import date
from decimal import Decimal
from django.utils import timezone
from django.db.models import Q
from .models import Bonificacion, Descuento, Promocion, EstadoEntidades, PromocionProducto, VerificacionProducto

class MotorPromociones:
    """
    Motor de promociones que evalúa qué promociones aplican a un carrito
    y calcula los beneficios correspondientes
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

            # Obtener promociones activas
            promociones_activas = self._obtener_promociones_activas(empresa, sucursal, cliente)
            
            if not promociones_activas:
                return self._construir_respuesta()

            # Evaluar cada promoción
            for promocion in promociones_activas:
                try:
                    self._evaluar_promocion_individual(promocion, carrito_detalle)
                except Exception as e:
                    self.errores.append(f"Error evaluando promoción {promocion.nombre}: {str(e)}")

            return self._construir_respuesta()

        except Exception as e:
            self.errores.append(f"Error general en motor de promociones: {str(e)}")
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

        return Promocion.objects.filter(filtros).select_related(
            'empresa', 'sucursal', 'canal_cliente', 'tipo_beneficio'
        ).prefetch_related(
            'productos', 'bonificaciones', 'descuentos', 'verificaciones'
        )

    def _evaluar_promocion_individual(self, promocion, carrito_detalle):
        """
        Evalúa una promoción específica contra el carrito
        """
        # Verificar si hay productos específicos requeridos
        if not self._verificar_productos_condicion(promocion, carrito_detalle):
            return

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
                return False

        return True

    def _evaluar_condicion_cantidad(self, promocion, carrito_detalle):
        """
        Evalúa promociones basadas en cantidad de productos
        """
        productos_promocion = PromocionProducto.objects.filter(promocion=promocion)
        
        for producto_promo in productos_promocion:
            # Buscar el producto en el carrito
            detalle_producto = None
            for detalle in carrito_detalle:
                if detalle.articulo.articulo_id == producto_promo.articulo.articulo_id:
                    detalle_producto = detalle
                    break
            
            if not detalle_producto:
                continue

            cantidad_carrito = detalle_producto.cantidad
            
            # Verificar si cumple con las condiciones de cantidad
            if self._cumple_condicion_cantidad(cantidad_carrito, producto_promo):
                self._aplicar_beneficios_por_cantidad(promocion, producto_promo, cantidad_carrito)

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

        # Si el tipo de selección es porcentaje, aplicar descuento
        if producto_promo.tipo_seleccion == 'porcentaje' and producto_promo.valor:
            self.descuentos.append({
                'promocion': promocion,
                'tipo': 'porcentaje_producto',
                'porcentaje': float(producto_promo.valor),
                'articulo': producto_promo.articulo,
                'monto_descuento': 0  # Se calculará al aplicar
            })

        # Si el tipo de selección es producto, aplicar bonificación
        elif producto_promo.tipo_seleccion == 'producto' and producto_promo.valor:
            # Calcular cuántas veces aplica la promoción
            veces_aplicable = cantidad_carrito // (producto_promo.cantidad_min or 1)
            cantidad_bonificada = int(producto_promo.valor) * veces_aplicable
            
            if cantidad_bonificada > 0:
                self.bonificaciones.append({
                    'promocion': promocion,
                    'articulo': producto_promo.articulo,
                    'cantidad': cantidad_bonificada
                })

        # Aplicar bonificaciones adicionales de la promoción
        self._aplicar_bonificaciones_promocion(promocion)

    def _evaluar_condicion_monto(self, promocion, carrito_detalle):
        """
        Evalúa promociones basadas en monto de compra
        """
        # Calcular monto total del carrito (considerando filtros de línea/marca si aplica)
        monto_total = self._calcular_monto_aplicable(promocion, carrito_detalle)
        
        if monto_total <= 0:
            return

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
                    'monto_base': float(monto_total)
                })

                # Aplicar bonificaciones si las hay
                self._aplicar_bonificaciones_promocion(promocion)
                break  # Solo aplicar el primer rango que cumpla

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

        # Aplicar bonificaciones
        self._aplicar_bonificaciones_promocion(promocion)
        
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
                    'monto_descuento': 0  # Se calculará al aplicar
                })

    def _aplicar_bonificaciones_promocion(self, promocion):
        """
        Aplica las bonificaciones definidas para una promoción
        """
        bonificaciones_promocion = Bonificacion.objects.filter(promocion=promocion)
        
        for bonificacion in bonificaciones_promocion:
            self.bonificaciones.append({
                'promocion': promocion,
                'articulo': bonificacion.articulo,
                'cantidad': bonificacion.cantidad
            })

    def _construir_respuesta(self):
        """
        Construye la respuesta final con todos los beneficios aplicables
        """
        return {
            'promociones_aplicadas': self.promociones_aplicadas,
            'bonificaciones': self.bonificaciones,
            'descuentos': self.descuentos,
            'errores': self.errores,
            'total_descuento': sum(desc.get('monto_descuento', 0) for desc in self.descuentos),
            'total_bonificaciones': len(self.bonificaciones)
        }


def evaluar_promociones(carrito_detalle, cliente=None, empresa=None, sucursal=None):
    """
    Función principal para evaluar promociones desde las vistas
    """
    motor = MotorPromociones()
    return motor.evaluar_promociones(carrito_detalle, cliente, empresa, sucursal)