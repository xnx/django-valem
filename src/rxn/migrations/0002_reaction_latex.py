# Generated by Django 3.0 on 2022-03-14 16:33

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("rxn", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="reaction",
            name="latex",
            field=models.CharField(default="TODO", editable=False, max_length=1024),
            preserve_default=False,
        ),
    ]
