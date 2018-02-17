# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


# Create your models here.
class User(models.Model):
    email = models.EmailField(max_length=35)
    login = models.CharField(max_length=35)
    password = models.CharField(max_length=35)
    avatar = models.ImageField()
    register_date = models.DateTimeField('date registered')

    def __str__(self):
        return self.login


class Tag(models.Model):
    word = models.CharField(max_length=35)

    def __str__(self):
        return self.word


class Question(models.Model):
    title = models.CharField(max_length=240)
    text = models.TextField(max_length=680)
    author = models.ForeignKey(User)
    pub_date = models.DateTimeField('date published')
    tags = models.ManyToManyField(Tag)

    # def __str__(self):
    #     return self.title, self.author, self.pub_date


class Answer(models.Model):
    text = models.TextField(max_length=680)
    author = models.ForeignKey(User)
    date = models.DateTimeField('date created')
    is_wright = models.BooleanField(default=False)
    question = models.ForeignKey(Question)
