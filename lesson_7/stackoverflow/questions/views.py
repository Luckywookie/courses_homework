# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from datetime import datetime
from django.shortcuts import get_object_or_404, get_list_or_404, render, redirect, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from .models import Question, Answer
from .forms import UserForm, UserCreateForm, QuestionCreateForm
from django.contrib.messages import error


class Logout(LogoutView):
    next_page = '/'


def view_login(request):
    form = UserForm(request.POST)
    username = form.data['username']
    password = form.data['password']
    next = form.data['next']
    user = authenticate(request, username=username, password=password)
    if user is not None:
        print(user)
        login(request, user)
        return HttpResponseRedirect(next)
    else:
        error(request, 'Ошибка авторизации')
        return HttpResponseRedirect(next)


def home(request):
    form = UserForm()
    return render(request, 'main.html', {'questions': [], 'form': form})


def main(request):
    questions = Question.objects.all()
    for question in questions:
        answers = Answer.objects.filter(question=question).all()
        question.ans = len(answers)
    form = UserForm()
    return render(request, 'main.html', {'questions': questions, 'form': form})


def detail(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    answers = Answer.objects.filter(question=question).all()
    return render(request, 'questions/details.html', {'question': question, 'answers': answers})


def registration(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            user.save()
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=user.username, password=raw_password)
            login(request, user)
            return redirect('/')
    else:
        form = UserCreateForm()
    return render(request, 'registration.html', {'form': form})


@login_required
def add_question(request):
    if request.method == 'POST':
        form = QuestionCreateForm(request.POST)
        if form.is_valid():
            new_question = form.save(commit=False)
            new_question.pub_date = datetime.now()
            new_question.author = request.user
            new_question.save()
    else:
        form = QuestionCreateForm()
    return render(request, 'questions/add_question.html', {'form': form})
