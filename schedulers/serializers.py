from rest_framework import serializers
from .models import Scheduler

class SchedulerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scheduler
        fields = ['id_scheduler', 'day', 'start_time', 'end_time']
