import uuid
from django.db import models
from django.utils import timezone
from post_project_promociones.choices import EstadoEntidades
from django.contrib.auth.models import AbstractUser 

class Rol(models.Model):
    rol_id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)
    estado = models.IntegerField(choices=EstadoEntidades.choices, default=EstadoEntidades.ACTIVO)

    class Meta:
        db_table = 'roles'

    def __str__(self):
        return self.nombre


class Empresa(models.Model):
    empresa_id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)

    class Meta:
        db_table = 'empresas'

    def __str__(self):
        return self.nombre


class Sucursal(models.Model):
    sucursal_id = models.AutoField(primary_key=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.RESTRICT, related_name='sucursales')
    nombre = models.CharField(max_length=255)

    class Meta:
        db_table = 'sucursales'

    def __str__(self):
        return self.nombre


class CanalCliente(models.Model):
    canal_cliente_id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)

    class Meta:
        db_table = 'canales_cliente'

    def __str__(self):
        return self.nombre


class Usuario(AbstractUser):
    nombre = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    rol = models.ForeignKey(
        'Rol',
        on_delete=models.RESTRICT,
        related_name='usuarios',
        null=True,    
        blank=True    
    )
    empresa = models.ForeignKey('Empresa', on_delete=models.RESTRICT, null=True, blank=True)
    sucursal = models.ForeignKey('Sucursal', on_delete=models.RESTRICT, null=True, blank=True)
    estado = models.IntegerField(choices=EstadoEntidades.choices, default=EstadoEntidades.ACTIVO)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'nombre']

    class Meta:
        db_table = 'usuarios'

    def __str__(self):
        return self.nombre


class Cliente(models.Model):
    cliente_id = models.AutoField(primary_key=True)
    canal_cliente = models.ForeignKey(CanalCliente, on_delete=models.RESTRICT, related_name='clientes')
    usuario = models.ForeignKey(
        'Usuario',
        on_delete=models.CASCADE,
        related_name='clientes',
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'clientes'

    def __str__(self):
        return self.usuario.nombre if self.usuario else "Cliente sin usuario"


class GrupoProveedor(models.Model):
    grupo_proveedor_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(Empresa, on_delete=models.RESTRICT, related_name='grupos_proveedor')
    codigo = models.CharField(max_length=10)
    nombre = models.CharField(max_length=100)
    estado = models.IntegerField(choices=EstadoEntidades.choices, default=EstadoEntidades.ACTIVO)

    class Meta:
        db_table = 'grupos_proveedor'

    def __str__(self):
        return self.nombre


class LineaArticulo(models.Model):
    linea_articulo_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(Empresa, on_delete=models.RESTRICT, related_name='lineas_articulo')
    grupo_proveedor = models.ForeignKey(GrupoProveedor, on_delete=models.RESTRICT, related_name='lineas_articulo')
    nombre = models.CharField(max_length=100)
    estado = models.IntegerField(choices=EstadoEntidades.choices, default=EstadoEntidades.ACTIVO)

    class Meta:
        db_table = 'lineas_articulos'

    def __str__(self):
        return self.nombre


class SublineaArticulo(models.Model):
    sublinea_articulo_id = models.AutoField(primary_key=True)
    linea_articulo = models.ForeignKey(LineaArticulo, on_delete=models.RESTRICT, related_name='sublineas_articulo')
    nombre = models.CharField(max_length=100)

    class Meta:
        db_table = 'sublineas_articulos'

    def __str__(self):
        return self.nombre
  

class Articulo(models.Model):
    articulo_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(Empresa, on_delete=models.RESTRICT, related_name='articulos')
    sucursal = models.ForeignKey(Sucursal, on_delete=models.RESTRICT, related_name='articulos', null=True, blank=True)
    codigo = models.CharField(max_length=50)
    codigo_barras = models.CharField(max_length=50, blank=True, null=True)
    codigo_ean = models.CharField(max_length=50, blank=True, null=True)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    grupo_proveedor = models.ForeignKey(GrupoProveedor, on_delete=models.RESTRICT, related_name='articulos')
    linea_articulo = models.ForeignKey(LineaArticulo, on_delete=models.RESTRICT, related_name='articulos')
    unidad_medida = models.CharField(max_length=50, blank=True, null=True)
    unidad_compra = models.CharField(max_length=50, blank=True, null=True)
    unidad_reparto = models.CharField(max_length=50, blank=True, null=True)
    unidad_bonificacion = models.CharField(max_length=50, blank=True, null=True)
    factor_reparto = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    factor_compra = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    factor_bonificacion = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    tipo_afectacion = models.CharField(max_length=50, blank=True, null=True)
    peso = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    tipo_producto = models.CharField(max_length=50, blank=True, null=True)
    afecto_retencion = models.BooleanField(default=False)
    afecto_detraccion = models.BooleanField(default=False)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.IntegerField(choices=EstadoEntidades.choices, default=EstadoEntidades.ACTIVO)

    class Meta:
        db_table = 'articulos'

    def __str__(self):
        return self.descripcion or ''


class StockSucursal(models.Model):
    stock_sucursal_id = models.AutoField(primary_key=True)
    sucursal = models.ForeignKey(Sucursal, on_delete=models.RESTRICT, related_name='stocks')
    articulo = models.ForeignKey(Articulo, on_delete=models.RESTRICT, related_name='stocks')
    stock_actual = models.IntegerField()

    class Meta:
        db_table = 'stock_sucursal'
        unique_together = ('sucursal', 'articulo')

    def __str__(self):
        return f'Stock {self.stock_actual} de {self.articulo} en {self.sucursal}'


# ===== NUEVA ESTRUCTURA DE PROMOCIONES =====

class Promocion(models.Model):
    promocion_id = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=255)
    empresa = models.ForeignKey(Empresa, on_delete=models.RESTRICT, related_name='promociones')
    sucursal = models.ForeignKey(Sucursal, on_delete=models.RESTRICT, related_name='promociones')
    canal_cliente = models.ForeignKey(CanalCliente, on_delete=models.RESTRICT, related_name='promociones')
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    grupo_proveedor_id = models.UUIDField(null=True, blank=True)
    linea_articulo_id = models.UUIDField(null=True, blank=True)
    monto_minimo = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cantidad_minima = models.IntegerField(null=True, blank=True)
    escalable = models.BooleanField(default=False)
    estado = models.IntegerField(choices=EstadoEntidades.choices, default=EstadoEntidades.ACTIVO)

    class Meta:
        db_table = 'promociones'

    def __str__(self):
        escalable_text = " (Escalable)" if self.escalable else ""
        return f"{self.descripcion}{escalable_text}"


class VerificacionProducto(models.Model):
    verificacion_id = models.AutoField(primary_key=True)
    articulo = models.ForeignKey('Articulo', on_delete=models.CASCADE, related_name='verificaciones')
    promocion = models.ForeignKey('Promocion', on_delete=models.CASCADE, related_name='verificaciones')

    def __str__(self):
        return f"Verificación {self.verificacion_id} - Artículo {self.articulo.descripcion} - Promoción {self.promocion.descripcion}"

    class Meta:
        db_table = 'verificacion_productos'


class Rango(models.Model):
    TIPO_CONDICION_CHOICES = [
        ('monto', 'Intervalos de Precios'),
        ('cantidad', 'Intervalos de Cantidad'),
    ]

    rango_id = models.AutoField(primary_key=True)
    tipo_rango = models.CharField(max_length=10, choices=TIPO_CONDICION_CHOICES)
    minimo = models.IntegerField()
    maximo = models.IntegerField(null=True, blank=True)
    descuento = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    promocion = models.ForeignKey(Promocion, on_delete=models.CASCADE, related_name='rangos')

    class Meta:
        db_table = 'rangos'
        ordering = ['minimo']

    def __str__(self):
        tipo_texto = "cantidad" if self.tipo_rango == "cantidad" else "monto"
        if self.maximo:
            return f"Rango {tipo_texto}: {self.minimo} - {self.maximo}"
        return f"Rango {tipo_texto}: {self.minimo}+"


class ProductoBonificadoRango(models.Model):
    pro_boni_id = models.AutoField(primary_key=True)
    articulo = models.ForeignKey(Articulo, on_delete=models.CASCADE, related_name='bonificaciones_rango')
    cantidad = models.IntegerField()
    rango = models.ForeignKey(Rango, on_delete=models.CASCADE, related_name='productos_bonificados')

    class Meta:
        db_table = 'producto_bonificado_rangos'

    def __str__(self):
        return f"{self.cantidad} unidades de {self.articulo.descripcion} (Rango: {self.rango.rango_id})"


class Beneficio(models.Model):
    TIPO_BENEFICIO_CHOICES = [
        ('bonificacion', 'Solo Bonificación'),
        ('descuento', 'Solo Descuento'), 
        ('ambos', 'Bonificación + Descuento'),
    ]

    beneficio_id = models.AutoField(primary_key=True)
    tipo_beneficio = models.CharField(max_length=20, choices=TIPO_BENEFICIO_CHOICES)
    descuento = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    promocion = models.ForeignKey(Promocion, on_delete=models.CASCADE, related_name='beneficios')

    class Meta:
        db_table = 'beneficio'

    def __str__(self):
        desc_text = f" ({self.descuento}%)" if self.descuento else ""
        return f"{self.get_tipo_beneficio_display()}{desc_text}"


class ProductosBeneficios(models.Model):
    pro_bene_id = models.AutoField(primary_key=True)
    articulo = models.ForeignKey(Articulo, on_delete=models.CASCADE, related_name='beneficios')
    cantidad = models.IntegerField()
    beneficio = models.ForeignKey(Beneficio, on_delete=models.CASCADE, related_name='productos')

    class Meta:
        db_table = 'productos_beneficios'

    def __str__(self):
        return f"{self.cantidad} unidades de {self.articulo.descripcion}"



class BonificacionAplicada(models.Model):
    bonificacion_aplicada_id = models.AutoField(primary_key=True)
    pedido = models.ForeignKey('Pedido', on_delete=models.RESTRICT, related_name='bonificaciones_aplicadas')
    promocion = models.ForeignKey(Promocion, on_delete=models.RESTRICT, related_name='bonificaciones_aplicadas')
    articulo = models.ForeignKey(Articulo, on_delete=models.RESTRICT, related_name='bonificaciones_aplicadas')
    cantidad = models.IntegerField()

    class Meta:
        db_table = 'bonificaciones_aplicadas'


class DescuentoAplicado(models.Model):
    descuento_aplicado_id = models.AutoField(primary_key=True)
    pedido = models.ForeignKey('Pedido', on_delete=models.RESTRICT, related_name='descuentos_aplicados')
    promocion = models.ForeignKey(Promocion, on_delete=models.RESTRICT, related_name='descuentos_aplicados')
    porcentaje_descuento = models.DecimalField(max_digits=5, decimal_places=2)
    monto_descuento = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'descuentos_aplicados'


class Carrito(models.Model):
    carrito_id = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.RESTRICT, related_name='carritos')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'carritos'


class DetalleCarrito(models.Model):
    detalle_carrito_id = models.AutoField(primary_key=True)
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name='detalle_carritos')
    articulo = models.ForeignKey(Articulo, on_delete=models.RESTRICT, related_name='detalle_carritos')
    cantidad = models.IntegerField()

    class Meta:
        db_table = 'detalle_carritos'


class Pedido(models.Model):
    pedido_id = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.RESTRICT, related_name='pedidos')
    sucursal = models.ForeignKey(Sucursal, on_delete=models.RESTRICT, related_name='pedidos')
    usuario = models.ForeignKey(Usuario, on_delete=models.RESTRICT, related_name='pedidos')
    fecha = models.DateField()
    total = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.IntegerField(choices=EstadoEntidades.choices, default=EstadoEntidades.ACTIVO)

    class Meta:
        db_table = 'pedidos'


class DetallePedido(models.Model):
    detalle_pedido_id = models.AutoField(primary_key=True)
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalle_pedidos')
    articulo = models.ForeignKey(Articulo, on_delete=models.RESTRICT, related_name='detalle_pedidos')
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'detalle_pedidos'