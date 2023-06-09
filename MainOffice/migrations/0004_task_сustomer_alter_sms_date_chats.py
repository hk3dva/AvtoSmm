# Generated by Django 4.2 on 2023-04-17 00:55

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('MainOffice', '0003_post_date_of_completion'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='сustomer',
            field=models.ForeignKey(db_column='сustomer', default=1, on_delete=django.db.models.deletion.DO_NOTHING, related_name='сustomer', to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='sms',
            name='date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.CreateModel(
            name='Chats',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, null=True)),
                ('id_recipient', models.ForeignKey(db_column='recipient_id', on_delete=django.db.models.deletion.DO_NOTHING, related_name='recipient_id', to=settings.AUTH_USER_MODEL)),
                ('id_sender', models.ForeignKey(db_column='sender_id', on_delete=django.db.models.deletion.DO_NOTHING, related_name='sender_id', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
