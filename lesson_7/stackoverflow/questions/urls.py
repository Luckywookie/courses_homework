from django.conf.urls import url
from . import views

# app_name = 'questions'

urlpatterns = [
    url(r'^$', views.main),
    url(r'(?P<question_id>\d+)$', views.detail),
    url(r'add_question$', views.add_question),
    url(r'(?P<question_id>\d+)/add_answer$', views.add_answer),
]