# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

# Register your models here.
from .models import Profile, Question, Answer, Tag


class DataQuestion(admin.ModelAdmin):
    list_display = ('pub_date', 'title', 'author')


class DataAnswer(admin.ModelAdmin):
    list_display = ('date', 'author', 'question')


admin.site.register(Profile)
admin.site.register(Question, DataQuestion)
admin.site.register(Answer, DataAnswer)
admin.site.register(Tag)