# Generated by Django 5.2.1 on 2025-05-24 07:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_verificacionproducto'),
    ]

    operations = [
        migrations.AlterField(
            model_name='promocion',
            name='tipo_beneficio',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='promociones', to='core.tipobeneficio'),
        ),
    ]
