# Generated by Django 3.2.5 on 2021-11-12 10:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rp', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='species',
            name='charge',
            field=models.SmallIntegerField(default=0, null=True),
        ),
    ]
