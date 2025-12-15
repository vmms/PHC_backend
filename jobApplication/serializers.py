from rest_framework import serializers
from .models import JobApplication

class JobApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobApplication
        fields = [
            'id_job_application',
            'id_jobs',
            'id_candidate',
            'status',
            'created_at'
        ]
