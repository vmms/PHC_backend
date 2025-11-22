from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Scheduler
from .serializers import SchedulerSerializer

class SchedulerViewSet(viewsets.ModelViewSet):
    queryset = Scheduler.objects.all()
    serializer_class = SchedulerSerializer
    permission_classes = [IsAuthenticated]