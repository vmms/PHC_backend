from django.urls import path
from . import views


urlpatterns = [
    path('list/', views.list_jobs, name='list_jobs'),
    path('get/', views.get_job, name='get_job'),
    path('create/', views.create_job, name='create_job'),
    path('update/', views.update_job, name='update_job'),
    path('delete/', views.delete_job, name='delete_job'),
    path('activate/', views.activate_job, name='activate_job'),
]