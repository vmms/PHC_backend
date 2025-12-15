from rest_framework import routers
from .views import JobApplicationViewSet

router = routers.DefaultRouter()
router.register(r'applications', JobApplicationViewSet)

urlpatterns = router.urls
