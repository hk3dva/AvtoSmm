# Generated by Django 4.2 on 2023-04-16 23:41

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MainOffice', '0002_post'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='date_of_completion',
            field=models.DateTimeField(default=datetime.datetime(2023, 4, 17, 2, 41, 17, 571562)),
            preserve_default=False,
        ),
    ]
