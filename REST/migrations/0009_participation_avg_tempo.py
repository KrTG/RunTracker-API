# Generated by Django 2.0.3 on 2018-04-20 18:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('REST', '0008_auto_20180420_1534'),
    ]

    operations = [
        migrations.AddField(
            model_name='participation',
            name='avg_tempo',
            field=models.DurationField(blank=True, default=None, null=True),
        ),
    ]
