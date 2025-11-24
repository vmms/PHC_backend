from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.list_companies, name='list_companies'),
    path('getcompany/', views.get_company, name='get_company'),
    path('create/', views.create_company, name='create_company'),
    path('update/', views.update_company, name='update_company'),
    path('delete/<int:pk>/', views.delete_company, name='delete_company'),
]
