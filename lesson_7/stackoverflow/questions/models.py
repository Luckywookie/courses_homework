# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save


# Create your models here.
class Profile(AbstractUser):
    avatar = models.ImageField(upload_to='questions/static/images/avatars', blank=True, null=True)

    class Meta:
        app_label = 'questions'


class Tag(models.Model):
    word = models.CharField(max_length=35)

    def __str__(self):
        return self.word


class Question(models.Model):
    title = models.CharField(max_length=240)
    text = models.TextField(max_length=900)
    author = models.ForeignKey(Profile)
    pub_date = models.DateTimeField('date published')
    tags = models.ManyToManyField(Tag)

    # def __str__(self):
    #     return self.title, self.author, self.pub_date


class Answer(models.Model):
    text = models.TextField(max_length=900)
    author = models.ForeignKey(Profile)
    date = models.DateTimeField('date created')
    is_right = models.BooleanField(default=False)
    question = models.ForeignKey(Question)
