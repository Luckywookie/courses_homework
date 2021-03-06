from django.conf.urls import url
from . import views

# app_name = 'questions'

urlpatterns = [
    url(r'^$', views.main),
    url(r'(?P<question_id>\d+)$', views.detail),
    url(r'add_question$', views.add_question),
    url(r'(?P<question_id>\d+)/add_answer$', views.add_answer),
    url(r'(?P<question_id>\d+)/vote/(?P<param>(up|down))', views.vote_question),
    url(r'^vote_answer/(?P<question_id>\d+)/(?P<answer_id>\d+)/(?P<param>(up|down))$', views.vote_answer),
]