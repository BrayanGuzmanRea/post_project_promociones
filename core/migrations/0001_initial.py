import django.contrib.auth.models
import django.contrib.auth.validators
import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Articulo',
            fields=[
                ('articulo_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('codigo', models.CharField(max_length=50)),
                ('codigo_barras', models.CharField(blank=True, max_length=50, null=True)),
                ('codigo_ean', models.CharField(blank=True, max_length=50, null=True)),
                ('descripcion', models.CharField(blank=True, max_length=255, null=True)),
                ('unidad_medida', models.CharField(blank=True, max_length=50, null=True)),
                ('unidad_compra', models.CharField(blank=True, max_length=50, null=True)),
                ('unidad_reparto', models.CharField(blank=True, max_length=50, null=True)),
                ('unidad_bonificacion', models.CharField(blank=True, max_length=50, null=True)),
                ('factor_reparto', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('factor_compra', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('factor_bonificacion', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('tipo_afectacion', models.CharField(blank=True, max_length=50, null=True)),
                ('peso', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('tipo_producto', models.CharField(blank=True, max_length=50, null=True)),
                ('afecto_retencion', models.BooleanField(default=False)),
                ('afecto_detraccion', models.BooleanField(default=False)),
                ('precio', models.DecimalField(decimal_places=2, max_digits=10)),
                ('estado', models.IntegerField(choices=[(1, 'Activo'), (9, 'De baja')], default=1)),
            ],
            options={
                'db_table': 'articulos',
            },
        ),
        migrations.CreateModel(
            name='CanalCliente',
            fields=[
                ('canal_cliente_id', models.AutoField(primary_key=True, serialize=False)),
                ('nombre', models.CharField(max_length=100)),
            ],
            options={
                'db_table': 'canales_cliente',
            },
        ),
        migrations.CreateModel(
            name='Empresa',
            fields=[
                ('empresa_id', models.AutoField(primary_key=True, serialize=False)),
                ('nombre', models.CharField(max_length=255)),
            ],
            options={
                'db_table': 'empresas',
            },
        ),
        migrations.CreateModel(
            name='Rol',
            fields=[
                ('rol_id', models.AutoField(primary_key=True, serialize=False)),
                ('nombre', models.CharField(max_length=50, unique=True)),
                ('estado', models.IntegerField(choices=[(1, 'Activo'), (9, 'De baja')], default=1)),
            ],
            options={
                'db_table': 'roles',
            },
        ),
        migrations.CreateModel(
            name='TipoBeneficio',
            fields=[
                ('tipo_beneficio_id', models.AutoField(primary_key=True, serialize=False)),
                ('nombre', models.CharField(max_length=50, unique=True)),
            ],
            options={
                'db_table': 'tipos_beneficio',
            },
        ),
        migrations.CreateModel(
            name='Usuario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('nombre', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('estado', models.IntegerField(choices=[(1, 'Activo'), (9, 'De baja')], default=1)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
                ('empresa', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, to='core.empresa')),
                ('rol', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='usuarios', to='core.rol')),
            ],
            options={
                'db_table': 'usuarios',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Carrito',
            fields=[
                ('carrito_id', models.AutoField(primary_key=True, serialize=False)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='carritos', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'carritos',
            },
        ),
        migrations.CreateModel(
            name='Cliente',
            fields=[
                ('cliente_id', models.AutoField(primary_key=True, serialize=False)),
                ('canal_cliente', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='clientes', to='core.canalcliente')),
                ('usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='clientes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'clientes',
            },
        ),
        migrations.CreateModel(
            name='DetalleCarrito',
            fields=[
                ('detalle_carrito_id', models.AutoField(primary_key=True, serialize=False)),
                ('cantidad', models.IntegerField()),
                ('articulo', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='detalle_carritos', to='core.articulo')),
                ('carrito', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='detalle_carritos', to='core.carrito')),
            ],
            options={
                'db_table': 'detalle_carritos',
            },
        ),
        migrations.AddField(
            model_name='articulo',
            name='empresa',
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='articulos', to='core.empresa'),
        ),
        migrations.CreateModel(
            name='GrupoProveedor',
            fields=[
                ('grupo_proveedor_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('codigo', models.CharField(max_length=10)),
                ('nombre', models.CharField(max_length=100)),
                ('estado', models.IntegerField(choices=[(1, 'Activo'), (9, 'De baja')], default=1)),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='grupos_proveedor', to='core.empresa')),
            ],
            options={
                'db_table': 'grupos_proveedor',
            },
        ),
        migrations.AddField(
            model_name='articulo',
            name='grupo_proveedor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='articulos', to='core.grupoproveedor'),
        ),
        migrations.CreateModel(
            name='LineaArticulo',
            fields=[
                ('linea_articulo_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('nombre', models.CharField(max_length=100)),
                ('estado', models.IntegerField(choices=[(1, 'Activo'), (9, 'De baja')], default=1)),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='lineas_articulo', to='core.empresa')),
                ('grupo_proveedor', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='lineas_articulo', to='core.grupoproveedor')),
            ],
            options={
                'db_table': 'lineas_articulos',
            },
        ),
        migrations.AddField(
            model_name='articulo',
            name='linea_articulo',
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='articulos', to='core.lineaarticulo'),
        ),
        migrations.CreateModel(
            name='Pedido',
            fields=[
                ('pedido_id', models.AutoField(primary_key=True, serialize=False)),
                ('fecha', models.DateField()),
                ('total', models.DecimalField(decimal_places=2, max_digits=10)),
                ('estado', models.IntegerField(choices=[(1, 'Activo'), (9, 'De baja')], default=1)),
                ('cliente', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='pedidos', to='core.cliente')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='pedidos', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'pedidos',
            },
        ),
        migrations.CreateModel(
            name='DetallePedido',
            fields=[
                ('detalle_pedido_id', models.AutoField(primary_key=True, serialize=False)),
                ('cantidad', models.IntegerField()),
                ('precio_unitario', models.DecimalField(decimal_places=2, max_digits=10)),
                ('articulo', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='detalle_pedidos', to='core.articulo')),
                ('pedido', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='detalle_pedidos', to='core.pedido')),
            ],
            options={
                'db_table': 'detalle_pedidos',
            },
        ),
        migrations.CreateModel(
            name='Promocion',
            fields=[
                ('promocion_id', models.AutoField(primary_key=True, serialize=False)),
                ('nombre', models.CharField(max_length=255)),
                ('fecha_inicio', models.DateField()),
                ('fecha_fin', models.DateField()),
                ('tipo_condicion', models.CharField(choices=[('monto', 'Monto'), ('cantidad', 'Cantidad')], max_length=10)),
                ('monto_minimo', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('cantidad_minima', models.IntegerField(blank=True, null=True)),
                ('estado', models.IntegerField(choices=[(1, 'Activo'), (9, 'De baja')], default=1)),
                ('canal_cliente', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='promociones', to='core.canalcliente')),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='promociones', to='core.empresa')),
            ],
            options={
                'db_table': 'promociones',
            },
        ),
        migrations.CreateModel(
            name='DescuentoAplicado',
            fields=[
                ('descuento_aplicado_id', models.AutoField(primary_key=True, serialize=False)),
                ('porcentaje_descuento', models.DecimalField(decimal_places=2, max_digits=5)),
                ('monto_descuento', models.DecimalField(decimal_places=2, max_digits=10)),
                ('pedido', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='descuentos_aplicados', to='core.pedido')),
                ('promocion', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='descuentos_aplicados', to='core.promocion')),
            ],
            options={
                'db_table': 'descuentos_aplicados',
            },
        ),
        migrations.CreateModel(
            name='Descuento',
            fields=[
                ('descuento_id', models.AutoField(primary_key=True, serialize=False)),
                ('porcentaje', models.DecimalField(decimal_places=2, max_digits=5)),
                ('promocion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='descuentos', to='core.promocion')),
            ],
            options={
                'db_table': 'descuentos',
            },
        ),
        migrations.CreateModel(
            name='BonificacionAplicada',
            fields=[
                ('bonificacion_aplicada_id', models.AutoField(primary_key=True, serialize=False)),
                ('cantidad', models.IntegerField()),
                ('articulo', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='bonificaciones_aplicadas', to='core.articulo')),
                ('pedido', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='bonificaciones_aplicadas', to='core.pedido')),
                ('promocion', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='bonificaciones_aplicadas', to='core.promocion')),
            ],
            options={
                'db_table': 'bonificaciones_aplicadas',
            },
        ),
        migrations.CreateModel(
            name='Bonificacion',
            fields=[
                ('bonificacion_id', models.AutoField(primary_key=True, serialize=False)),
                ('cantidad', models.IntegerField()),
                ('articulo', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='bonificaciones', to='core.articulo')),
                ('promocion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bonificaciones', to='core.promocion')),
            ],
            options={
                'db_table': 'bonificaciones',
            },
        ),
        migrations.CreateModel(
            name='SublineaArticulo',
            fields=[
                ('sublinea_articulo_id', models.AutoField(primary_key=True, serialize=False)),
                ('nombre', models.CharField(max_length=100)),
                ('linea_articulo', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='sublineas_articulo', to='core.lineaarticulo')),
            ],
            options={
                'db_table': 'sublineas_articulos',
            },
        ),
        migrations.CreateModel(
            name='Sucursal',
            fields=[
                ('sucursal_id', models.AutoField(primary_key=True, serialize=False)),
                ('nombre', models.CharField(max_length=255)),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='sucursales', to='core.empresa')),
            ],
            options={
                'db_table': 'sucursales',
            },
        ),
        migrations.AddField(
            model_name='promocion',
            name='sucursal',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='promociones', to='core.sucursal'),
        ),
        migrations.AddField(
            model_name='pedido',
            name='sucursal',
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='pedidos', to='core.sucursal'),
        ),
        migrations.AddField(
            model_name='articulo',
            name='sucursal',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='articulos', to='core.sucursal'),
        ),
        migrations.AddField(
            model_name='usuario',
            name='sucursal',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, to='core.sucursal'),
        ),
        migrations.AddField(
            model_name='articulo',
            name='sucursal',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='articulos', to='core.sucursal'),
        ),
        migrations.AddField(
            model_name='articulo',
            name='sucursal',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='articulos', to='core.sucursal'),
        ),
        migrations.AddField(
            model_name='usuario',
            name='sucursal',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, to='core.sucursal'),
        ),
        migrations.AddField(

            model_name='promocion',
            name='tipo_beneficio',
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='promociones', to='core.tipobeneficio'),
        ),
        migrations.CreateModel(
            name='PromocionLinea',
            fields=[
                ('promocion_linea_id', models.AutoField(primary_key=True, serialize=False)),
                ('linea_articulo', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='promocion_lineas', to='core.lineaarticulo')),
                ('promocion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lineas', to='core.promocion')),
            ],
            options={
                'db_table': 'promocion_lineas',
                'unique_together': {('promocion', 'linea_articulo')},
            },
        ),
        migrations.CreateModel(
            name='PromocionProducto',
            fields=[
                ('promocion_producto_id', models.AutoField(primary_key=True, serialize=False)),
                ('articulo', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='promocion_productos', to='core.articulo')),
                ('promocion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='productos', to='core.promocion')),
            ],
            options={
                'db_table': 'promocion_productos',
                'unique_together': {('promocion', 'articulo')},
            },
        ),
        migrations.CreateModel(
            name='StockSucursal',
            fields=[
                ('stock_sucursal_id', models.AutoField(primary_key=True, serialize=False)),
                ('stock_actual', models.IntegerField()),
                ('articulo', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='stocks', to='core.articulo')),
                ('sucursal', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='stocks', to='core.sucursal')),
            ],
            options={
                'db_table': 'stock_sucursal',
                'unique_together': {('sucursal', 'articulo')},
            },
        ),
    ]
