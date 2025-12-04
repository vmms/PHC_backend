from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_message, name='create_message'),
    path('chats/', views.list_chats, name='list_chats'),
    path('chat_detail/', views.chat_detail, name='chat_detail'),
    path('list_chats/', views.list_chats, name='list_chats'),
    path('mark-read/', views.mark_read, name='mark_read'),
]
