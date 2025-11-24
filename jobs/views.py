from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Job, SkillsHasJobs, ScheduleHasJobs, Application
from .serializers import JobSerializer
from companies.models import Company
from candidates.models import Candidate
from django.db import transaction


from skills.models import Skill
from schedulers.models import Scheduler


def _company_for_user(user):
    try:
        return Company.objects.get(account=user)
    except Company.DoesNotExist:
        return None


def _company_allowed(user):
    # same rules you mentioned earlier: subscription != 'candidate' and status == 1
    if getattr(user, 'subscription', None) == 'candidate':
        return False, 'Users with subscription "candidate" cannot perform this action'
    if getattr(user, 'status', None) != 1:
        return False, 'Account status not active'
    return True, None


# ---------------------------
# LISTAR JOBS (GET) - público para cuentas autenticadas
# ---------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_jobs(request):
    qs = Job.objects.filter(is_active=True).order_by('-day_start')
    serializer = JobSerializer(qs, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


# ---------------------------
# OBTENER JOB (POST con body { "id_jobs": X })
# ---------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_job(request):
    job_id = request.data.get('id_jobs')
    if not job_id:
        return Response({'message': 'id_jobs is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        job = Job.objects.get(id_jobs=job_id)
    except Job.DoesNotExist:
        return Response({'message': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)

    # ------------------------------------------------------
    # Obtener skills asociados a través de la tabla intermedia
    # ------------------------------------------------------
    skill_links = SkillsHasJobs.objects.filter(jobs=job).select_related('skills')
    skills_list = [
        {"id_skills": link.skills.id_skills, "name": link.skills.name}
        for link in skill_links
    ]

    # ------------------------------------------------------
    # Obtener schedule asociados a través de la tabla intermedia
    # ------------------------------------------------------
    schedule_links = ScheduleHasJobs.objects.filter(jobs=job).select_related('schedule')
    schedule_list = [
        {
            "day": link.schedule.day,
            "time_start": link.schedule.time_start.strftime("%H:%M") if link.schedule.time_start else None,
            "time_finish": link.schedule.time_finish.strftime("%H:%M") if link.schedule.time_finish else None
        }
        for link in schedule_links
    ]

    # ------------------------------------------------------
    # Armar el JSON final
    # ------------------------------------------------------
    response_data = {
        "type": job.type,
        "title": job.title,
        "location": job.location,
        "salary": job.salary,
        "experience": job.experience,
        "schedule_type": job.schedule_type,
        "employment_type": job.employment_type,
        "modality": job.modality,
        "benefits": job.benefits,
        "requirements": job.requirements,
        "day_start": job.day_start.strftime("%Y-%m-%d") if job.day_start else None,
        "description": job.description,
        "is_active": job.is_active,
        "max_applications": job.max_applications,
        "auto_close": job.auto_close,
        "work_mode": job.work_mode,
        "contract_type": job.contract_type,
        "skills": skills_list,
        "schedule": schedule_list
    }

    return Response(response_data, status=status.HTTP_200_OK)

# ---------------------------
# CREAR JOB (POST) - usa company del token, no company en body
# ---------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_job(request):
    company = _company_for_user(request.user)
    if not company:
        return Response({'message': 'No company associated with this user'}, status=status.HTTP_404_NOT_FOUND)

    allowed, reason = _company_allowed(request.user)
    if not allowed:
        return Response({'message': reason}, status=status.HTTP_403_FORBIDDEN)

    data = request.data.copy()
    data.pop('company', None)
    data.pop('company_id', None)

    # Normalizar skills (IDs existentes)
    skill_ids = []
    if "skills" in data:
        for item in data["skills"]:
            if "id_skills" in item:
                skill_ids.append(item["id_skills"])
    data["skills"] = skill_ids

    # Normalizar schedule (crear nuevos)
    schedule_payload = data.pop("schedule", [])

    serializer = JobSerializer(data=data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_404_NOT_FOUND)

    job = serializer.save(company=company)

    # ----------------------------------------------------
    #   INSERTAR SKILLS (skills ya existen)
    # ----------------------------------------------------
    for sid in skill_ids:
        try:
            skill_obj = Skill.objects.get(id_skills=sid)
        except Skill.DoesNotExist:
            return Response({"message": f"Skill ID {sid} does not exist"},status=status.HTTP_404_NOT_FOUND)

        SkillsHasJobs.objects.get_or_create(
            skills=skill_obj,
            jobs=job
        )


    # ----------------------------------------------------
    #   CREAR SCHEDULES Y LIGARLOS
    # ----------------------------------------------------
    for sch in schedule_payload:
        # Crear el scheduler
        scheduler = Scheduler.objects.create(
            day=sch.get("day"),
            time_start=sch.get("time_start"),
            time_finish=sch.get("time_finish")
        )

        # Ligarlo a job
        ScheduleHasJobs.objects.get_or_create(
            schedule=scheduler,
            jobs=job
        )
    response_data = serializer.format_response(job)
    return Response(response_data, status=status.HTTP_201_CREATED)
    # return Response(JobSerializer(job).data, status=status.HTTP_201_CREATED)

# ---------------------------
# ACTUALIZAR JOB (POST) - usa company del token para validar propiedad
# request.body debe contener "id_jobs" + campos a actualizar
# ---------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_job(request):
    job_id = request.data.get('id_jobs')
    if not job_id:
        return Response({'message': 'id_jobs is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        job = Job.objects.get(id_jobs=job_id)
    except Job.DoesNotExist:
        return Response({'message': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)

    company = _company_for_user(request.user)
    if not company or job.company_id != company.id_company:
        return Response({'message': 'Not owner of the job'}, status=status.HTTP_403_FORBIDDEN)

    data = request.data.copy()
    # never allow changing the company via payload
    data.pop('company', None)
    data.pop('company_id', None)

    serializer = JobSerializer(job, data=data, partial=True)
    if serializer.is_valid():
        job = serializer.save()
        return Response(JobSerializer(job).data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ---------------------------
# BORRAR JOB (POST) - usa company del token para validar propiedad
# request.body debe contener "id_jobs"
# ---------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_job(request):
    job_id = request.data.get('id_jobs')
    if not job_id:
        return Response({'message': 'id_jobs is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        job = Job.objects.get(id_jobs=job_id)
    except Job.DoesNotExist:
        return Response({'message': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)

    company = _company_for_user(request.user)
    if not company or job.company_id != company.id_company:
        return Response({'message': 'Not owner of the job'}, status=status.HTTP_403_FORBIDDEN)

    job.delete()
    return Response({'message': 'Job deleted successfully'}, status=status.HTTP_200_OK)
