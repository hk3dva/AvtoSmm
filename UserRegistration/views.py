from django.shortcuts import render, redirect
from django.views import View
from .forms import CustomCreateUser, CustomUserAuthenticateForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Group, User

def index(request):
    return render(request, 'UserRegistration/index.html')


def logoutUser(request):
    logout(request)
    return redirect('/')


class RegisterView(View):
    template_name = 'UserRegistration/Registration.html'
    form_class = CustomCreateUser

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            t = form.save()
            Group.objects.get(name='Smm').user_set.add(t)

            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password1'])
            login(request, user)
            return redirect('MainOffice:base')
        return render(request, self.template_name, {'form': form})


class LoginView(View):
    template_name = 'UserRegistration/login.html'
    form_class = CustomUserAuthenticateForm

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('MainOffice:base')

        loginForm = self.form_class()
        return render(request, self.template_name, {'form': loginForm})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect('/')

        loginForm = self.form_class(request=request, data=request.POST)
        if loginForm.is_valid():
            uname = loginForm.cleaned_data['username']
            upass = loginForm.cleaned_data['password']
            user = authenticate(username=uname, password=upass)
            if user is not None:
                login(request, user)
                return redirect('/Office')

        context = {
            'form': loginForm,
        }
        return render(request, 'MainOffice/profile.html', context)
