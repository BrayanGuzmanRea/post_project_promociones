from django.utils import timezone
from django.db.models import Q
from .models import Promocion, EstadoEntidades

def evaluar_promociones(articulos_carrito, canal_cliente):
    hoy = timezone.now().date()
    resultados = []

    promociones = Promocion.objects.filter(
        estado=EstadoEntidades.ACTIVO,
        fecha_inicio__lte=hoy,
        fecha_fin__gte=hoy,
    )

    if canal_cliente:
        promociones = promociones.filter(Q(canal_cliente__isnull=True) | Q(canal_cliente=canal_cliente))

    print("🎯 Total promociones candidatas:", promociones.count())

    for promo in promociones:
        print("⏳ Evaluando promoción:", promo.nombre)

        total_cantidad = 0
        total_monto = 0

        productos_promo_codigos = list(promo.productos.values_list('articulo__codigo', flat=True))
        sucursal_promo = promo.sucursal
        empresa_promo = promo.empresa

        for item in articulos_carrito:
            articulo = item['articulo']
            cantidad = item['cantidad']

            # Validar empresa/sucursal del artículo vs promoción
            if articulo.empresa != empresa_promo:
                continue
            if sucursal_promo and articulo.sucursal != sucursal_promo:
                continue

            if articulo.codigo in productos_promo_codigos:
                total_cantidad += cantidad
                total_monto += articulo.precio * cantidad

        print(" - Total cantidad:", total_cantidad)

        cumple = False
        veces = 0
        if promo.tipo_condicion == 'cantidad' and promo.cantidad_minima:
            veces = total_cantidad // promo.cantidad_minima
            cumple = veces >= 1
        elif promo.tipo_condicion == 'monto' and promo.monto_minimo:
            cumple = total_monto >= promo.monto_minimo
            veces = 1 if cumple else 0

        print("✔️ Cumple:", cumple, " | Veces:", veces)

        if not cumple:
            continue

        bonificaciones = []
        descuentos = []

        for bonif in promo.bonificaciones.all():
            bonificaciones.append((bonif.articulo, bonif.cantidad * veces))

        for desc in promo.descuentos.all():
            descuentos.append(desc.porcentaje)

        resultados.append({
            'promocion': promo,
            'bonificaciones': bonificaciones,
            'descuentos': descuentos
        })

    return resultados
