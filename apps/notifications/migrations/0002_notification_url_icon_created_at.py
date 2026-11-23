from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='url',
            field=models.CharField(blank=True, default='', max_length=300),
        ),
        migrations.AddField(
            model_name='notification',
            name='icon',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
        migrations.AddField(
            model_name='notification',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='notification',
            name='scheduled_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(
                choices=[
                    ('report_update', 'Report update'),
                    ('expiry_soon', 'Expiry soon'),
                    ('expiry_expired', 'Expired product'),
                    ('streak', 'Streak'),
                    ('routine_remind', 'Routine reminder'),
                    ('welcome', 'Welcome'),
                    ('general', 'General'),
                ],
                default='general',
                max_length=30,
            ),
        ),
        migrations.AlterModelOptions(
            name='notification',
            options={'ordering': ['-created_at']},
        ),
    ]
