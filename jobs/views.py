from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Job, SkillsHasJobs, ScheduleHasJobs, Application
from .serializers import JobSerializer
from companies.models import Company
from candidates.models import Candidate
from django.db import transaction
from collections import defaultdict
from jobs.services import get_jobs_admin_stats


from skills.models import Skill
from schedulers.models import Scheduler
from geopy.geocoders import Nominatim

import time

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
    qs = Job.objects.filter(is_active=True).order_by('-id_jobs')
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
    # Diccionario temporal para agrupar schedules por tipo
    temp_schedule = defaultdict(list)

    for link in ScheduleHasJobs.objects.filter(jobs=job).select_related('schedule'):
        sched = link.schedule
        if sched.type == "permanent":
            temp_schedule["permanent"].append({
                "day": getattr(sched, "day", None),
                "time_start": sched.time_start.strftime("%H:%M") if sched.time_start else None,
                "time_end": sched.time_finish.strftime("%H:%M") if sched.time_finish else None
            })
        elif sched.type == "range":
            temp_schedule["range"].append({
                "date_start": getattr(sched, "date_start", None).strftime("%Y-%m-%d") if getattr(sched, "date_start", None) else None,
                "date_end": getattr(sched, "date_end", None).strftime("%Y-%m-%d") if getattr(sched, "date_end", None) else None,
                "time_start": sched.time_start.strftime("%H:%M") if sched.time_start else None,
                "time_end": sched.time_finish.strftime("%H:%M") if sched.time_finish else None
            })
        elif sched.type == "multiple":
            temp_schedule["multiple"].append({
                "date": getattr(sched, "date_start", None).strftime("%Y-%m-%d") if getattr(sched, "date_start", None) else None,
                "time_start": sched.time_start.strftime("%H:%M") if sched.time_start else None,
                "time_end": sched.time_finish.strftime("%H:%M") if sched.time_finish else None
            })

    # Construir la lista final
    schedule_data = []
    for sched_type, items in temp_schedule.items():
        schedule_data.append({
            "type": sched_type,
            "dates" if sched_type == "multiple" else "days": items
        })


    # ------------------------------------------------------
    # Armar el JSON final
    # ------------------------------------------------------
    response_data = {
        "title": job.title,
        "location": job.location,
        "job_type": job.job_type,
        "employment_type": job.employment_type,
        "modality": job.modality,
        "experience": job.experience,

        "description": job.description,
        "qualifications": job.qualifications,

        "salary": job.salary,
        "benefits": job.benefits,
        "oportunity": job.oportunity,
        "other": job.other,

        "is_active": job.is_active,
        "auto_close": job.auto_close,

        # estos NO se tocan
        "skills": skills_list,
        "schedule": schedule_data,
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

    # ===========================================
    #   NUEVA LÓGICA PARA SKILLS (strings)
    # ===========================================
    skill_names = []
    if "skills" in data:
        for item in data["skills"]:
            if "skill" in item and item["skill"]:
                skill_names.append(item["skill"].strip())
    data["skills"] = []

    # ===========================================
    #   NORMALIZAR SCHEDULES
    # ===========================================
    schedule_payload = data.pop("schedule", [])

    serializer = JobSerializer(data=data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    job = serializer.save(company=company)

    # ===========================================
    #   GENERAR LATITUD Y LONGITUD
    # ===========================================
    try:
        geolocator = Nominatim(user_agent="PHC_backend_job_creation")
        loc = geolocator.geocode(job.location, timeout=10)
        time.sleep(2)  # para evitar bloqueos de Nominatim
        if loc:
            job.latitude = loc.latitude
            job.longitude = loc.longitude
            job.save(update_fields=["latitude", "longitude"])
        else:
            job.latitude = None
            job.longitude = None
            job.save(update_fields=["latitude", "longitude"])
    except Exception as e:
        # en caso de error, dejamos lat/lng como None
        job.latitude = None
        job.longitude = None
        job.save(update_fields=["latitude", "longitude"])
        print(f"Error geocoding job {job.title}: {e}")

    # ===========================================
    #   PROCESAR SKILLS (buscar o crear)
    # ===========================================
    pk_name = job._meta.pk.name
    job_pk_value = getattr(job, pk_name)

    for name in skill_names:
        skill_obj, created = Skill.objects.get_or_create(name=name)
        SkillsHasJobs.objects.get_or_create(
            skills_id=skill_obj.id_skills,
            jobs_id=job_pk_value
        )

    # ===========================================
    #   CREAR SCHEDULES Y RELACIONARLOS
    # ===========================================
    for sch in schedule_payload:

        # ---------------------------
        # CASE: MULTIPLE
        # ---------------------------
        if "multiple" in sch and sch["multiple"]:
            for item in sch["multiple"]:
                scheduler = Scheduler.objects.create(
                    type="multiple",
                    day=None,
                    date_start=item.get("date_start"),
                    date_end=None,
                    time_start=item.get("time_start"),
                    time_finish=item.get("time_end")
                )
                ScheduleHasJobs.objects.get_or_create(schedule=scheduler, jobs=job)
            continue

        # ---------------------------
        # CASE: RANGE
        # ---------------------------
        elif "range" in sch and sch["range"]:
            for item in sch["range"]:
                scheduler = Scheduler.objects.create(
                    type="range",
                    day=None,
                    date_start=item.get("date_start"),
                    date_end=item.get("date_end"),
                    time_start=item.get("time_start"),
                    time_finish=item.get("time_end")
                )
                ScheduleHasJobs.objects.get_or_create(schedule=scheduler, jobs=job)
            continue

        # ---------------------------
        # CASE: PERMANENT
        # ---------------------------
        elif "permanent" in sch and sch["permanent"]:
            perm = sch["permanent"]
            start_date = perm.get("start_date")
            for day_item in perm.get("days", []):
                scheduler = Scheduler.objects.create(
                    type="permanent",
                    day=day_item.get("day"),
                    date_start=start_date,
                    date_end=None,
                    time_start=day_item.get("time_start"),
                    time_finish=day_item.get("time_end")
                )
                ScheduleHasJobs.objects.get_or_create(schedule=scheduler, jobs=job)

    response_data = serializer.format_response(job)
    return Response(response_data, status=status.HTTP_201_CREATED)


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
        return Response(
            {'message': 'id_jobs is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        job = Job.objects.get(id_jobs=job_id)
    except Job.DoesNotExist:
        return Response(
            {'message': 'Job not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    company = _company_for_user(request.user)
    if not company or job.company_id != company.id_company:
        return Response(
            {'message': 'Not owner of the job'},
            status=status.HTTP_403_FORBIDDEN
        )

    job.is_active = False
    job.save(update_fields=['is_active'])

    return Response(
        {'message': 'Job deactivated successfully'},
        status=status.HTTP_200_OK
    )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def activate_job(request):
    job_id = request.data.get('id_jobs')
    if not job_id:
        return Response(
            {'message': 'id_jobs is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        job = Job.objects.get(id_jobs=job_id)
    except Job.DoesNotExist:
        return Response(
            {'message': 'Job not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    company = _company_for_user(request.user)
    if not company or job.company_id != company.id_company:
        return Response(
            {'message': 'Not owner of the job'},
            status=status.HTTP_403_FORBIDDEN
        )

    job.is_active = True
    job.save(update_fields=['is_active'])

    return Response(
        {'message': 'Job activated successfully'},
        status=status.HTTP_200_OK
    )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_jobs_stats(request):
    """
    Retorna estadísticas de jobs para admin
    """
    try:
        stats = get_jobs_admin_stats()
        return Response(stats, status=200)
    except Exception as e:
        return Response(
            {"error": "Unexpected server error", "details": str(e)},
            status=500
        )
