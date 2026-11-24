from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product_library', '0003_product_opened_on_pao_months'),
    ]

    operations = [
        migrations.CreateModel(
            name='StoredFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('data', models.BinaryField()),
                ('content_type', models.CharField(default='application/octet-stream', max_length=100)),
                ('size', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
