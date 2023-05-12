from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from MainOffice.models import Account


class CustomCreateUser(UserCreationForm):
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': "form-control form-control-lg", 'placeholder': "Пароль"}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': "form-control form-control-lg", 'placeholder': "Повторите пароль"}))

    class Meta:
        model = Account
        fields = ('username', 'password1', 'password2', 'first_name', 'last_name')
        widgets = {
            'username': forms.TextInput(attrs={'class': "form-control form-control-lg", 'type': "text", 'placeholder': "Логин"}),
            'first_name': forms.TextInput(attrs={'class': "form-control form-control-lg", 'type': "text", 'placeholder': "Имя"}),
            'last_name': forms.TextInput(attrs={'class': "form-control form-control-lg", 'type': "text", 'placeholder': "Фамилия"}),
        }


class CustomUserAuthenticateForm(AuthenticationForm):
    username = forms.CharField(label='Login', widget=forms.TextInput(attrs={'class': "form-control form-control-lg",
                                                                            'placeholder': "Введите логин",}))
    password = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'class': "form-control form-control-lg",
                                                                                   'placeholder': "Введите пароль"}))
