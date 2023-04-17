from django.db import models
from django.contrib.auth.models import Group, User, AbstractUser
from django.conf import settings
from django.utils import timezone


class GroupForLead(models.Model):
    link = models.CharField(blank=False, null=False)
    name = models.CharField(blank=False, null=False, unique=True)
    date_start = models.DateField(blank=True, null=True, default=timezone.now)
    photo = models.ImageField(upload_to='group', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'GroupForLead'

    def __str__(self):
        return f'{self.name}'


class Account(AbstractUser):
    choice_gender =(
        (0, 'Женщина'),
        (1, 'Мужчина')
    )

    birthday_date = models.DateField(blank=True, null=True)
    photo = models.ImageField(upload_to='user', blank=True, null=True)
    gender = models.IntegerField(blank=True, null=True, choices=choice_gender, default=2)

    groups_leader = models.ManyToManyField(GroupForLead, through='SmmGroupLead', related_name='groups', blank=True)

    class Meta:
        managed = True
        db_table = 'Account'

    def __str__(self):
        return f'{self.pk} {self.last_name} {self.first_name}'


class SmmGroupLead(models.Model):
    smm = models.ForeignKey(Account, models.CASCADE, db_column='smm')
    group = models.ForeignKey(GroupForLead, models.CASCADE, db_column='group')

    class Meta:
        managed = True
        db_table = 'Smm_group_lead'
        unique_together = (('smm', 'group'),)


class Chats(models.Model):
    id_sender = models.ForeignKey(Account, models.DO_NOTHING, db_column='sender_id', related_name='sender_id')
    id_recipient = models.ForeignKey(Account, models.DO_NOTHING, db_column='recipient_id', related_name='recipient_id')
    name = models.CharField(blank=True, null=True)


class Sms(models.Model):
    id_sender = models.ForeignKey(Account, models.DO_NOTHING, db_column='sender', related_name='sender')
    id_recipient = models.ForeignKey(Account, models.DO_NOTHING, db_column='recipient', related_name='recipient')
    text = models.CharField(blank=True, null=True)
    date = models.DateTimeField(blank=False, null=False, default=timezone.now)

    class Meta:
        managed = True
        db_table = 'Sms'

    def __str__(self):
        return f'{self.id_sender} {self.id_recipient}'


class Task(models.Model):
    executor = models.ForeignKey(Account, models.DO_NOTHING, db_column='executor', related_name='executor')
    сustomer = models.ForeignKey(Account, models.DO_NOTHING, db_column='сustomer', related_name='сustomer')
    title = models.CharField(blank=False, null=False)
    text = models.CharField(blank=False, null=False)
    date_start = models.DateField(blank=True, null=True)
    date_end = models.DateField(blank=True, null=True)
    completed = models.BooleanField(default=False)

    class Meta:
        managed = True
        db_table = 'Task'


class Post(models.Model):
    group = models.ForeignKey(GroupForLead, models.CASCADE, db_column='group')
    owner = models.ForeignKey(Account, models.CASCADE, db_column='owner')
    text = models.CharField(blank=False, null=False)
    photo = models.ImageField(upload_to='post', blank=True, null=True)
    date = models.DateTimeField()

    date_of_completion = models.DateTimeField()

    class Meta:
        managed = True
        db_table = 'Post'

    def __str__(self):
        return f'{self.pk} {self.group.name} {self.date}'

