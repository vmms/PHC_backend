from rest_framework import serializers
from .models import Job, SkillsHasJobs, ScheduleHasJobs
from skills.models import Skill
from schedulers.models import Scheduler
from companies.models import Company

class JobSerializer(serializers.ModelSerializer):
    skills = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    schedules = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Job
        fields = [
            'id_jobs',
            'company',
            'job_type',
            'title',
            'location',
            'salary',
            'experience',
            'employment_type',
            'modality',
            'benefits',
            'description',
            'qualifications',
            'oportunity',
            'other',
            'is_active',
            'created_at',
            'updated_at',
            'auto_close',
            'skills',
            'schedules'
        ]
        extra_kwargs = {
            'company': {'read_only': True}
        }

    def create(self, validated_data):
        skills = validated_data.pop('skills', [])
        schedules = validated_data.pop('schedules', [])

        job = Job.objects.create(**validated_data)

        # Insertar habilidades
        for skill_id in skills:
            SkillsHasJobs.objects.create(skills_id=skill_id, jobs=job)

        # Insertar horarios
        for schedule_id in schedules:
            ScheduleHasJobs.objects.create(schedule_id=schedule_id, jobs=job)

        return job

    def update(self, instance, validated_data):
        skills = validated_data.pop('skills', None)
        schedules = validated_data.pop('schedules', None)

        # Campos normales
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Skills
        if skills is not None:
            SkillsHasJobs.objects.filter(jobs=instance).delete()
            for skill_id in skills:
                SkillsHasJobs.objects.create(skills_id=skill_id, jobs=instance)

        # Schedules
        if schedules is not None:
            ScheduleHasJobs.objects.filter(jobs=instance).delete()
            for schedule_id in schedules:
                ScheduleHasJobs.objects.create(schedule_id=schedule_id, jobs=instance)

        return instance
    
    def format_response(self, instance=None):
        if instance is None:
            instance = self.instance

        if not instance:
            return {}

        return {
            "message": "Creaste una nueva oferta de empleo nueva",
            "job": {
                "id_job": instance.id_jobs,
                "title": instance.title,
            }
        }

