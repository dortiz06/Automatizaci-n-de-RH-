# Generated manually for adding dias_vacaciones_acumulados field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('empleados', '0004_merge_20251014_1546'),
    ]

    operations = [
        migrations.AddField(
            model_name='perfil',
            name='dias_vacaciones_acumulados',
            field=models.PositiveIntegerField(default=0, verbose_name='Días de Vacaciones Acumulados del Año Anterior'),
        ),
    ]
