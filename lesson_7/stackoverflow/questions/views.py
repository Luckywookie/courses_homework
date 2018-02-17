# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import get_object_or_404, get_list_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from .models import Question
# Create your views here.
# from django.contrib.auth.mixins import LoginRequiredMixin
# class MyView(LoginRequiredMixin, View):
#     login_url = '/login/'
#     redirect_field_name = 'redirect_to'


class Logout(LogoutView):
    next_page = '/'


def view_login(request):
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        # Redirect to a success page.
    else:
        # Return an 'invalid login' error message.
        pass

def home(request):
    return render(request, 'questions/main.html', {'questions': []})


def main(request):
    questions = get_list_or_404(Question)
    return render(request, 'questions/main.html', {'questions': questions})


def detail(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    # user = get_list_or_404()
    return render(request, 'questions/details.html', {'question': question})
