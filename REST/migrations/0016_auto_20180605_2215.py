# Generated by Django 2.0.3 on 2018-06-05 22:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('REST', '0015_auto_20180516_1457'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='avatar',
            field=models.TextField(blank=True, default=''),
        ),
    ]
