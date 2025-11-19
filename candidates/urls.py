from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_candidates, name='list_candidates'),  # opcional
    path('get/', views.get_candidate, name='get_candidate'),
    path('create/', views.create_candidate, name='create_candidate'),
    path('update/', views.update_candidate, name='update_candidate'),
    path('delete/', views.delete_candidate, name='delete_candidate'),
]
