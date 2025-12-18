from django.db import models
from companies.models import Company
from candidates.models import Candidate
from skills.models import Skill
from schedulers.models import Scheduler


# -----------------------------------------------------------
# TABLA PRINCIPAL: jobs (coincide con tu SQL)
# -----------------------------------------------------------
class Job(models.Model):
    id_jobs = models.AutoField(primary_key=True)

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        db_column='company_id'
    )

    job_type = models.CharField(max_length=60, null=True, blank=True)
    title = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    salary = models.CharField(max_length=75)
    experience = models.CharField(max_length=250)

    employment_type = models.CharField(max_length=45)
    modality = models.CharField(max_length=45)

    benefits = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField()

    # Nuevos según JSON
    qualifications = models.TextField(null=True, blank=True)
    oportunity = models.CharField(max_length=400, null=True, blank=True)
    other = models.CharField(max_length=400, null=True, blank=True)

    # Control
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    auto_close = models.BooleanField(default=False)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)


    class Meta:
        db_table = 'jobs'
        managed = False

    def __str__(self):
        return f"{self.title} ({self.company_id})"


# -----------------------------------------------------------
# TABLA: skills_has_jobs (tabla puente)
# SQL: (skills_id INT, jobs_id INT) PK (skills_id, jobs_id)
# -----------------------------------------------------------
class SkillsHasJobs(models.Model):
    skills = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        db_column='skills_id',
        primary_key=True,
    )
    jobs = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        db_column='jobs_id'
    )

    class Meta:
        db_table = 'skills_has_jobs'
        managed = False
        unique_together = (('skills', 'jobs'),)
        default_related_name = '+'


# -----------------------------------------------------------
# TABLA: schedule (si tu schedulers.models usa otro db_table, ajusta)
# (en SQL: id_schedule, day, time_start, time_finish)
# -----------------------------------------------------------
# Nota: el modelo Scheduler lo tienes en schedulers.models.
# Aquí no lo redefino; usamos ese modelo para la FK en schedule_has_jobs.


# -----------------------------------------------------------
# TABLA: schedule_has_jobs (tabla puente)
# SQL: (schedule_id INT, jobs_id INT) PK (schedule_id, jobs_id)
# -----------------------------------------------------------
class ScheduleHasJobs(models.Model):
    schedule = models.ForeignKey(
        Scheduler,
        on_delete=models.CASCADE,
        db_column='schedule_id',
        primary_key=True,
    )
    jobs = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        db_column='jobs_id'
    )

    class Meta:
        db_table = 'schedule_has_jobs'
        managed = False
        unique_together = (('schedule', 'jobs'),)
        default_related_name = '+'


# -----------------------------------------------------------
# TABLA: candidate_has_schedule (tabla puente candidate <-> schedule)
# SQL: (candidate_id INT, schedule_id INT) PK (candidate_id, schedule_id)
# -----------------------------------------------------------
class CandidateHasSchedule(models.Model):
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        db_column='candidate_id',
        related_name='candidate_has_schedule'
    )
    schedule = models.ForeignKey(
        Scheduler,
        on_delete=models.CASCADE,
        db_column='schedule_id',
        related_name='candidate_has_schedule'
    )

    class Meta:
        db_table = 'candidate_has_schedule'
        managed = False
        unique_together = (('candidate', 'schedule'),)


# -----------------------------------------------------------
# TABLA: application (candidato aplica a job) -> existe en tu SQL
# -----------------------------------------------------------
class Application(models.Model):
    id_application = models.AutoField(primary_key=True)
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        db_column='candidate_id',
        related_name='applications'
    )
    jobs = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        db_column='jobs_id',
        related_name='applications'
    )
    status = models.CharField(
        max_length=10,
        choices=(('applied', 'applied'), ('reviewed', 'reviewed'), ('rejected', 'rejected'), ('hired', 'hired')),
        default='applied'
    )
    created_at = models.DateTimeField()

    class Meta:
        db_table = 'application'
        managed = False

    def __str__(self):
        return f"App {self.id_application}: cand {self.candidate_id} -> job {self.jobs_id}"
