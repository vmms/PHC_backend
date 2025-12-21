from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.list_companies, name='list_companies'),
    path('getcompany/', views.get_company, name='get_company'),
    path('create/', views.create_company, name='create_company'),
    path('update/', views.update_company, name='update_company'),
    path('delete/<int:pk>/', views.delete_company, name='delete_company'),
    path('upload_image/', views.upload_company_logo, name='upload_company_logo'),
    path('my_applications/', views.list_my_job_applications, name='list_my_job_applications'),
    path('list_my_jobs/', views.list_my_jobs, name='list_my_jobs'),
    path('get_candidate_public/', views.get_candidate_public, name='get_candidate_public'),
    path('get_candidate_contact_info/', views.get_candidate_contact_info, name='get_candidate_contact_info'),
]
