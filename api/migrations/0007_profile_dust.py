# Generated by Django 4.0.3 on 2022-04-14 18:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_alter_cardentry_acquired_alter_collection_created'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='dust',
            field=models.IntegerField(default=0),
        ),
    ]
