# Generated by Django 4.0.3 on 2022-05-11 12:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0012_alter_collection_image2_alter_collection_image3'),
    ]

    operations = [
        migrations.AlterField(
            model_name='card',
            name='craft_cost',
            field=models.IntegerField(default=20),
        ),
    ]
