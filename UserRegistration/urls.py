from django.urls import path
from .views import *

app_name = 'UserRegistration'
urlpatterns = [
    path('registration', RegisterView.as_view(), name='registration'),
    path('login', LoginView.as_view(), name='login'),
    path('logout/', logoutUser, name='logout'),
    path('', index, name='index'),
]
