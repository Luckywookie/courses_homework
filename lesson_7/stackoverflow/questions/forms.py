from django import forms
from .models import Profile, Question, Answer
from django.contrib.auth.forms import ReadOnlyPasswordHashField, UserCreationForm


class UserForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('username', 'password')


class UserCreateForm(UserCreationForm):
    class Meta:
        model = Profile
        fields = ('username', 'email', 'password1', 'password2', 'avatar')

    def __init__(self, *args, **kwargs):
        super(UserCreateForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


class QuestionCreateForm(forms.ModelForm):
    new_tags = forms.CharField(label='new_tags')

    class Meta:
        model = Question
        fields = ('title', 'text')

    def __init__(self, *args, **kwargs):
        super(QuestionCreateForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


class AnswerCreateForm(forms.ModelForm):

    class Meta:
        model = Answer
        fields = ('text',)

    def __init__(self, *args, **kwargs):
        super(AnswerCreateForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
