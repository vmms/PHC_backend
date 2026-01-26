from django.db import models
from accounts.models import Account
from addresses.models import Address
from education.models import Education

from schedulers.models import Scheduler

from django.utils.deconstruct import deconstructible
from django.conf import settings
import os

@deconstructible
class PhotoProfilePath:
    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        filename = f'photo_user_{instance.id_candidate}.{ext}'
        full_path = os.path.join('photos_profiles', filename)
        
        # Borrar archivo existente antes de guardar
        absolute_path = os.path.join(settings.MEDIA_ROOT, full_path)
        if os.path.exists(absolute_path):
            os.remove(absolute_path)
        
        return full_path

@deconstructible
class CVUPath:
    def __call__(self, instance, filename):
        filename = f'candidate_{instance.id_candidate}.pdf'
        full_path = os.path.join('cvu_files', filename)

        # Borrar CVU existente antes de guardar
        absolute_path = os.path.join(settings.MEDIA_ROOT, full_path)
        if os.path.exists(absolute_path):
            os.remove(absolute_path)

        return full_path

class Candidate(models.Model):
    id_candidate = models.AutoField(primary_key=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=45)
    last_name = models.CharField(max_length=45)
    phone_number = models.CharField(max_length=20)
    emergency_contact_name = models.CharField(max_length=100)
    emergency_contact_phone = models.CharField(max_length=20)
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    education = models.ForeignKey(Education, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=[('active','active'),('inactive','inactive')], default='active')
    radius = models.IntegerField(null=True, blank=True)
    adult = models.BooleanField(default=True)
    work_permission = models.BooleanField(default=True)
    web_link = models.CharField(max_length=100, null=True, blank=True)
    about = models.TextField(null=True, blank=True)
    photo = models.ImageField(upload_to=PhotoProfilePath(), null=True, blank=True)
    cvu = models.FileField(upload_to=CVUPath(), null=True, blank=True)
    desired_position = models.CharField(max_length=100, null=True, blank=True)
    years_experience = models.IntegerField(null=True, blank=True)
    last_position = models.CharField(max_length=100, null=True, blank=True)
    last_company = models.CharField(max_length=100, null=True, blank=True)
    email = models.CharField(max_length=100, null=True, blank=True)
    job_type = models.CharField(max_length=45, null=True, blank=True)
    employment_type = models.CharField(max_length=45, null=True, blank=True)
    modality = models.CharField(max_length=45, null=True, blank=True)
    salary = models.CharField(max_length=75)
    servsafe = models.CharField(max_length=25, default='na')
    is_active = models.BooleanField(default=False)

    profile_views = models.PositiveIntegerField(default=0)
    cvu_downloads = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "candidate"
        managed = False

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class CandidateHasSchedule(models.Model):
    candidate = models.ForeignKey(
        'Candidate',
        on_delete=models.CASCADE,
        db_column='candidate_id',
        primary_key=True,
    )
    schedule = models.ForeignKey(
        Scheduler,
        on_delete=models.CASCADE,
        db_column='schedule_id'
    )

    class Meta:
        db_table = 'candidate_has_schedule'
        managed = False
        unique_together = (('candidate', 'schedule'),)
