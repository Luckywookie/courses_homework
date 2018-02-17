# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import get_object_or_404, render
from .models import Question
# Create your views here.


def main(request):
    return render(request, 'questions/main.html')


def detail(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    return render(request, 'questions/details.html', {'question': question})
