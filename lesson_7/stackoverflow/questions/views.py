# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import get_object_or_404, get_list_or_404, render, redirect, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from .models import Question, Answer
from .forms import UserForm
from django.contrib.messages import error


class Logout(LogoutView):
    next_page = '/'


def view_login(request):
    form = UserForm(request.POST)
    login = form.data['login']
    password = form.data['password']
    next = form.data['next']
    user = authenticate(request, username=login, password=password)
    if user is not None:
        login(request, user)
        return HttpResponseRedirect(next)
    else:
        error(request, 'Ошибка авторизации')
        return HttpResponseRedirect(next)


def home(request):
    form = UserForm()
    return render(request, 'questions/main.html', {'questions': [], 'form': form})


def main(request):
    questions = Question.objects.all()
    for question in questions:
        answers = Answer.objects.filter(question=question).all()
        question.ans = len(answers)
    form = UserForm()
    return render(request, 'questions/main.html', {'questions': questions, 'form': form})


def detail(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    answers = Answer.objects.filter(question=question).all()
    return render(request, 'questions/details.html', {'question': question, 'answers': answers})
