from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_candidates, name='list_candidates'),  # opcional
    path('get/', views.get_candidate, name='get_candidate'),
    path('create/', views.create_candidate, name='create_candidate'),
    path('update/', views.update_candidate, name='update_candidate'),
    path('delete/', views.delete_candidate, name='delete_candidate'),
    path('apply/', views.apply_to_job, name='apply_to_job'),
    path('upload_photo/', views.upload_photo, name='upload_photo'),
    path('list_job/', views.list_job, name='list_job'),
    path('list_last_jobs/', views.list_last_jobs, name='list_last_jobs'),
    path('get_company/', views.get_company, name='get_company'),
    path('my_applications/', views.my_applications, name='my_applications'),
    path('load_cvu/', views.load_cvu, name='load_cvu'),
    path('download_cvu/', views.download_cvu, name='download_cvu'),
]
