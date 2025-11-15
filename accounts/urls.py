from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from . import views

urlpatterns = [
    path('create/', views.create_account, name='create_account'),
    path('read/', views.read_account, name='read_account'),
    path('update/', views.update_account, name='update_account'),
    path('delete/', views.delete_account, name='delete_account'),
    path('list/', views.list_accounts, name='list_accounts'),
    # path('login/', views.login_account, name='login_account'),  
    path('token/', views.token_login, name='token_login'),
    # path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # path('login/', AccountLoginView.as_view(), name='account-login'),

]