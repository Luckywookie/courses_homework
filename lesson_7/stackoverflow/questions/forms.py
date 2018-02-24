from django import forms
from .models import Profile, Question
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
    class Meta:
        model = Question
        fields = ('title', 'text', 'tags')

    def __init__(self, *args, **kwargs):
        super(QuestionCreateForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
