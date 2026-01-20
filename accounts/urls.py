from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from . import views

urlpatterns = [
    path('create/', views.create_account, name='create_account'),
    path('google_register/', views.google_register, name='google_register'),
    path('facebook_register/', views.facebook_register, name='facebook_register'),
    path('read/', views.read_account, name='read_account'),
    path('update/', views.update_account, name='update_account'),
    path('deactivate/', views.deactivate_account, name='deactivate_account'),
    path('list/', views.list_accounts, name='list_accounts'),  
    path('token/', views.token_login, name='token_login'),
    path('google_login/', views.google_login, name='google_login'),
    path('facebook_login/', views.facebook_login, name='facebook_login'),
    path('recover_password/', views.recover_password, name='recover_password'),
    path('update_password/', views.update_password, name='update_password'),
    path('delete/', views.delete_account, name='delete_account'),
]