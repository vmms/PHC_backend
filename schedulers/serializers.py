from rest_framework import serializers
from .models import Scheduler

class SchedulerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scheduler
        fields = [
            'id_schedule',
            'type',
            'day',
            'date_start',
            'date_end',
            'time_start',
            'time_finish'
        ]