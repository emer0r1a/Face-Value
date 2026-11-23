from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product_library', '0002_product_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='opened_on',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='pao_months',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
    ]
