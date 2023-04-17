from django.urls import path
from .views import *

app_name = 'MainOffice'
urlpatterns = [
    path('', index, name='base'),
    path('chat/', Chats.as_view(), name='chat'),
    path('chat/<str:room_name>/', Chats.as_view(), name='chat1'),
    path('profile/<int:pk>', Profile.as_view(), name='profile'),
    path('calendar/', calendar, name='calendar'),

    path('posts/', Posts.as_view(), name='posts'),
    path('posts/get-image/<int:pk>/', get_image, name='get_image'),

    path('tasks/', tasks, name='tasks'),
    path('statistics/', statistics, name='statistics'),
    # path('chat/<int:pk>', name='chat'),
    # path('profile/<int:pk>', profile, name=profile),
]
