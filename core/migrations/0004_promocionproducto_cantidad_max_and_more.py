# Generated by Django 5.2.1 on 2025-05-22 14:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_alter_descuento_options_descuento_valor_maximo_and_more'),
    ]

    operations = [
        # migrations.AddField(
        #     model_name='promocionproducto',
        #     name='cantidad_max',
        #     field=models.PositiveIntegerField(blank=True, null=True),
        # ),
        # migrations.AddField(
        #     model_name='promocionproducto',
        #     name='cantidad_min',
        #     field=models.PositiveIntegerField(blank=True, null=True),
        # ),
        # migrations.AddField(
        #     model_name='promocionproducto',
        #     name='tipo_seleccion',
        #     field=models.CharField(blank=True, max_length=20, null=True),
        # ),
        # migrations.AddField(
        #     model_name='promocionproducto',
        #     name='valor',
        #     field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        # ),
        migrations.AlterField(
            model_name='promocion',
            name='tipo_condicion',
            field=models.CharField(choices=[('monto', 'Intervalos de Precios'), ('cantidad', 'Intervalos de Cantidad')], max_length=10),
        ),
    ]
