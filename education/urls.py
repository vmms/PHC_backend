from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EducationViewSet

router = DefaultRouter()
router.register(r'educations', EducationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
