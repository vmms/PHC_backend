from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser

from .models import Candidate, CandidateHasSchedule
from .serializers import CandidateSerializer, CandidateAdminSerializer
from collections import defaultdict

from jobs.models import Job, SkillsHasJobs, ScheduleHasJobs
from jobs.serializers import JobSerializer
from jobApplication.models import JobApplication
from schedulers.models import Scheduler
from companies.models import Company
from companies.serializers import CompanySerializer
from candidates.services import get_candidate_admin_stats

from django.utils.deconstruct import deconstructible
from django.conf import settings
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django.core.files.storage import default_storage

from datetime import timedelta
from django.utils import timezone

import os
import time
import json

from geopy.geocoders import Nominatim
from math import radians, sin, cos, sqrt, atan2

from candidates.services import parse_date, parse_time, hours_intersect



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_candidate(request):
    try:
        candidate = Candidate.objects.get(account_id=request.user.id_account)
    except Candidate.DoesNotExist:
        return Response({'message': 'No candidate associated with this user'}, status=404)

    temp_schedule = defaultdict(list)

    for link in CandidateHasSchedule.objects.filter(candidate=candidate).select_related('schedule'):
        sched = link.schedule
        if sched.type == "permanent":
            temp_schedule["permanent"].append({
                "day": getattr(sched, "day", None),
                "time_start": sched.time_start.strftime("%H:%M") if sched.time_start else None,
                "time_end": sched.time_finish.strftime("%H:%M") if sched.time_finish else None,
                "hired_date": sched.date_start.strftime("%Y-%m-%d") if sched.date_start else None
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

    schedule_data = []
    for sched_type, items in temp_schedule.items():
        hired_date = items[0].get("hired_date") if items else None
        schedule_data.append({
            "type": sched_type,
            "hired_date": hired_date,
            "dates" if sched_type == "multiple" else "days": items
        })

    serializer = CandidateSerializer(candidate, context={'request': request})
    response_data = serializer.data
    response_data["schedule"] = schedule_data
    #print(response_data)

    return Response(response_data, status=200)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_candidate(request):
    data = request.data.copy()
    data.pop('account', None)
    data.pop('id_candidate', None)

    schedule_payload = data.pop("schedule", [])

    # Si viene como string, parseamos
    if isinstance(schedule_payload, str):
        try:
            schedule_payload = json.loads(schedule_payload)
        except:
            schedule_payload = []

    serializer = CandidateSerializer(data=data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    candidate = serializer.save(account=request.user)

    # ============================================
    # PROCESAR SCHEDULES (igual que en jobs)
    # ============================================
    for sch in schedule_payload:

        # CASE: MULTIPLE
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
                CandidateHasSchedule.objects.get_or_create(schedule=scheduler, candidate=candidate)
            continue

        # CASE: RANGE
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
                CandidateHasSchedule.objects.get_or_create(schedule=scheduler, candidate=candidate)
            continue

        # CASE: PERMANENT
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
                CandidateHasSchedule.objects.get_or_create(schedule=scheduler, candidate=candidate)

    response_data = serializer.format_response(candidate)
    return Response(response_data, status=status.HTTP_201_CREATED)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_candidate(request):
    # print(request.data)
    try:
        candidate = Candidate.objects.get(account_id=request.user.id_account)
    except Candidate.DoesNotExist:
        return Response({'message': 'No candidate associated with this user'}, status=404)

    data = request.data.copy()

    # ===========================
    # 1. ADDRESS UPDATE
    # ===========================
    address_data = data.pop('address', None)
    if address_data:
        for field, value in address_data.items():
            setattr(candidate.address, field, value)
        candidate.address.save()

    # ===========================
    # 2. EDUCATION UPDATE
    # ===========================
    education_data = data.pop('education', None)
    if education_data:
        for field, value in education_data.items():
            setattr(candidate.education, field, value)
        candidate.education.save()

    # ===========================
    # 3. CANDIDATE FIELDS UPDATE
    # ===========================
    for field, value in data.items():
        if field not in ["schedule"]:  # schedule se procesa aparte
            setattr(candidate, field, value)

    candidate.save()

    # ===========================
    # 4. SCHEDULE UPDATE (BORRAR + CREAR)
    # ===========================
    schedule_data = request.data.get("schedule", [])

    if schedule_data:
        # 4.1 borrar relaciones actuales
        CandidateHasSchedule.objects.filter(candidate=candidate).delete()

        for sched_block in schedule_data:
            perm = sched_block.get("permanent")
            if perm:
                start_date = perm.get("start_date")
                days = perm.get("days", [])

                for day_data in days:
                    # crear scheduler usando tu modelo REAL
                    new_sched = Scheduler.objects.create(
                        type="permanent",
                        day=day_data["day"],
                        date_start=start_date,
                        date_end=None,
                        time_start=day_data["time_start"],
                        time_finish=day_data["time_end"]  # JSON usa time_end, modelo usa time_finish
                    )

                    # crear relación
                    CandidateHasSchedule.objects.create(
                        candidate=candidate,
                        schedule_id=new_sched.id_schedule
                    )

    return Response({"message": "Candidate updated successfully"}, status=200)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_candidate(request):
    """
    Elimina el candidate asociado al usuario autenticado.
    """
    try:
        candidate = Candidate.objects.get(account=request.user)
    except Candidate.DoesNotExist:
        return Response({'message': 'No candidate associated with this user'}, status=status.HTTP_404_NOT_FOUND)

    candidate.delete()
    return Response({'message': 'Candidate deleted successfully'}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_candidates(request):
    """
    Lista todos los candidates (solo admin o debugging).
    """
    try:
        candidates = Candidate.objects.all().order_by(
            '-created_at',   # más nuevos primero
            'first_name'     # luego por nombre
        )
        total = candidates.count()  # Número total de candidatos

        serializer = CandidateAdminSerializer(candidates, many=True, context={'request': request})

        return Response({
            "total": total,
            "candidates": serializer.data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "error": "Unexpected server error",
            "details": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def apply_to_job(request):

    account = request.user

    # Candidate ligado a esa cuenta
    try:
        candidate = Candidate.objects.get(account=account)
        if not candidate.is_active:
            return Response(
                {
                    "message": "You cannot apply for a job if your account is inactive."
                },
                status=status.HTTP_403_FORBIDDEN
            )
    except Candidate.DoesNotExist:
        return Response(
            {'message': 'No candidate associated with this user'},
            status=status.HTTP_404_NOT_FOUND
        )

    if not candidate.is_active:
        return Response(
            {
                "message": "Your candidate profile is inactive. You cannot apply for jobs."
            },
            status=status.HTTP_403_FORBIDDEN
        )

    # obtener id del job
    job_id = request.data.get('job_id')
    if not job_id:
        return Response(
            {"message": "job_id is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # obtener job
    try:
        job = Job.objects.get(id_jobs=job_id)
    except Job.DoesNotExist:
        return Response(
            {"message": "Job does not exist"},
            status=status.HTTP_404_NOT_FOUND
        )

    # validar si ya aplicó
    if JobApplication.objects.filter(id_candidate=candidate, id_jobs=job).exists():
        return Response(
            {"message": "You have already applied for this job"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # crear registro
    JobApplication.objects.create(
        id_candidate=candidate,
        id_jobs=job,
        status='application_submitted'
    )

    return Response(
        {"message": "Application submitted successfully"},
        status=status.HTTP_201_CREATED
    )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_photo(request):
    id_candidate = request.data.get('id_candidate')
    if not id_candidate:
        return Response({'error': 'id_candidate is required'}, status=400)

    try:
        candidate = Candidate.objects.get(id_candidate=id_candidate)
    except Candidate.DoesNotExist:
        return Response({'error': 'Candidate not found'}, status=404)

    if 'photo' not in request.FILES:
        return Response({'error': 'No photo file provided'}, status=400)

    # Guardar la foto usando .save() para que se sobrescriba
    candidate.photo.save(
        request.FILES['photo'].name, 
        request.FILES['photo'], 
        save=True
    )

    return Response(
        {"message": "Your profile photo has been updated successfully"},
        status=200
    )

def haversine(lat1, lon1, lat2, lon2):
    R = 3958.8  # millas
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi, dlambda = radians(lat2-lat1), radians(lon2-lon1)
    a = sin(dphi/2)**2 + cos(phi1)*cos(phi2)*sin(dlambda/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def list_job(request):
    data = request.data

    account = request.user

    # Candidate ligado a esa cuenta
    try:
        candidate = Candidate.objects.get(account=account)
        if not candidate.is_active:
            return Response(
                {
                    "message": "You cannot apply for a job if your account is inactive."
                },
                status=status.HTTP_403_FORBIDDEN
            )
    except Candidate.DoesNotExist:
        return Response(
            {'message': 'No candidate associated with this user'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Si el JSON está vacío o todos los filtros son None/'none', devolver vacíos
    if not data or all(
        value is None or (isinstance(value, str) and value.lower() == 'none')
        for key, value in data.items()
        if key in ['title', 'location', 'employment_type', 'modality', 'job_type', 'qualifications', 'salary', 'radius_miles']
    ):
        return Response({"jobs": []}, status=status.HTTP_200_OK)

    title = data.get('title')
    location = data.get('location')
    employment_type = data.get('employment_type')
    modality = data.get('modality')
    job_type = data.get('job_type')
    qualifications = data.get('qualifications')
    salary_max = data.get('salary')
    radius_miles = data.get('radius_miles', 350)  # valor por defecto 350 millas
    try:
        radius_miles = float(radius_miles)
    except (ValueError, TypeError):
        return Response({"message": "radius miles must be a number"}, status=status.HTTP_400_BAD_REQUEST)

    jobs = Job.objects.filter(is_active=1)

    # ---------------------
    # Filtros de string
    # ---------------------
    if title and isinstance(title, str) and title.lower() != 'none':
        jobs = jobs.filter(title__icontains=title)
    if employment_type and isinstance(employment_type, str) and employment_type.lower() != 'none':
        jobs = jobs.filter(employment_type__iexact=employment_type)
    if job_type and isinstance(employment_type, str) and job_type.lower() != 'none':
        jobs = jobs.filter(employment_type__iexact=job_type)
    if modality and isinstance(modality, str) and modality.lower() != 'none':
        jobs = jobs.filter(modality__iexact=modality)
    if qualifications and isinstance(qualifications, str) and qualifications.lower() != 'none':
        jobs = jobs.filter(qualifications__icontains=qualifications)
    if salary_max is not None:
        try:
            salary_max = float(salary_max)
            jobs = jobs.extra(where=["CAST(salary AS DECIMAL) <= %s"], params=[salary_max])
        except ValueError:
            return Response({"message": "salary must be a number"}, status=status.HTTP_400_BAD_REQUEST)

    # ---------------------
    # Filtrar por distancia usando lat/lng
    # ---------------------
    filtered_jobs = []
    if location and isinstance(location, str) and location.lower() != 'none':
        # buscar coordenadas de la ciudad de referencia
        try:
            from geopy.geocoders import Nominatim
            import time
            geolocator = Nominatim(user_agent="PHC_backend_list_job")
            city_loc = geolocator.geocode(location, timeout=10)
            time.sleep(2)
            if not city_loc:
                return Response({"message": "City not found"}, status=status.HTTP_400_BAD_REQUEST)
            city_lat, city_lng = city_loc.latitude, city_loc.longitude
        except Exception as e:
            return Response({"message": f"Error obtaining city coordinates: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        # recorrer jobs y calcular distancia
        for job in jobs:
            if job.latitude is not None and job.longitude is not None:
                dist = haversine(city_lat, city_lng, job.latitude, job.longitude)
                if dist <= radius_miles:
                    filtered_jobs.append(job)

        jobs = filtered_jobs

    serializer = JobSerializer(jobs, many=True)
    jobs_data = serializer.data

    for job_data in jobs_data:
        job_id = job_data.get("id_jobs")

        try:
            job_obj = Job.objects.get(id_jobs=job_id)
        except Job.DoesNotExist:
            job_data["skills"] = []
            job_data["schedule"] = []
            continue

        # ------------------------------------------------------
        # Skills
        # ------------------------------------------------------
        skill_links = SkillsHasJobs.objects.filter(jobs=job_obj).select_related('skills')
        job_data["skills"] = [
            {
                "id_skills": link.skills.id_skills,
                "name": link.skills.name
            }
            for link in skill_links
        ]

        # ------------------------------------------------------
        # Schedule
        # ------------------------------------------------------
        temp_schedule = defaultdict(list)

        for link in ScheduleHasJobs.objects.filter(jobs=job_obj).select_related('schedule'):
            sched = link.schedule

            if sched.type == "permanent":
                temp_schedule["permanent"].append({
                    "day": getattr(sched, "day", None),
                    "time_start": sched.time_start.strftime("%H:%M") if sched.time_start else None,
                    "time_end": sched.time_finish.strftime("%H:%M") if sched.time_finish else None
                })

            elif sched.type == "range":
                temp_schedule["range"].append({
                    "date_start": sched.date_start.strftime("%Y-%m-%d") if sched.date_start else None,
                    "date_end": sched.date_end.strftime("%Y-%m-%d") if sched.date_end else None,
                    "time_start": sched.time_start.strftime("%H:%M") if sched.time_start else None,
                    "time_end": sched.time_finish.strftime("%H:%M") if sched.time_finish else None
                })

            elif sched.type == "multiple":
                temp_schedule["multiple"].append({
                    "date": sched.date_start.strftime("%Y-%m-%d") if sched.date_start else None,
                    "time_start": sched.time_start.strftime("%H:%M") if sched.time_start else None,
                    "time_end": sched.time_finish.strftime("%H:%M") if sched.time_finish else None
                })

        schedule_data = []
        for sched_type, items in temp_schedule.items():
            schedule_data.append({
                "type": sched_type,
                "dates" if sched_type == "multiple" else "days": items
            })

        job_data["schedule"] = schedule_data

        # ------------------------------------------------------
        # Company (lo que ya tenías)
        # ------------------------------------------------------
        company_id = job_data.get("company")
        if company_id:
            try:
                company = Company.objects.get(id_company=company_id)
                job_data["company"] = CompanySerializer(
                    company,
                    context={'request': request}
                ).data
            except Company.DoesNotExist:
                job_data["company"] = None

    return Response({"jobs": jobs_data}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_last_jobs(request):
    desired_position = request.data.get('desired_position', None)

    jobs = Job.objects.filter(is_active=1)

    if desired_position and desired_position.lower() != 'none':
        jobs = jobs.filter(title__icontains=desired_position)

    jobs = jobs.order_by('-created_at')[:5]

    serializer = JobSerializer(jobs, many=True)
    return Response({"jobs": serializer.data}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_company(request):
    company_id = request.data.get('company_id')
    
    if not company_id:
        return Response({"message": "company_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        company = Company.objects.get(id_company=company_id)
    except Company.DoesNotExist:
        return Response({"message": "Company not found"}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = CompanySerializer(company)
    return Response({"company": serializer.data}, status=status.HTTP_200_OK)

def format_date(date):
    if not date:
        return None
    return date.strftime("%m-%d-%Y")

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def my_applications(request):
    id_candidate = request.data.get("id_candidate")
    title = request.data.get("title")
    company = request.data.get("company")

    account = request.user

    # Candidate ligado a esa cuenta
    try:
        candidate = Candidate.objects.get(account=account)
        if not candidate.is_active:
            return Response(
                {
                    "message": "You cannot apply for a job if your account is inactive."
                },
                status=status.HTTP_403_FORBIDDEN
            )
    except Candidate.DoesNotExist:
        return Response(
            {'message': 'No candidate associated with this user'},
            status=status.HTTP_404_NOT_FOUND
        )

    if not id_candidate:
        return Response({"message": "id_candidate is required"}, status=400)

    applications = JobApplication.objects.filter(
        id_candidate=id_candidate
    ).select_related('id_jobs__company')

    if title:
        applications = applications.filter(id_jobs__title__icontains=title)
    if company:
        applications = applications.filter(id_jobs__company__name__icontains=company)

    applications = applications.order_by("-created_at")

    STATUS_LABELS = {
        "application_submitted": "application submitted",
        "application_viewed": "application viewed",
    }

    result = []

    for app in applications:
        job = app.id_jobs
        company_obj = job.company

        job_data = JobSerializer(job).data
        job_data["company"] = CompanySerializer(
            company_obj, context={"request": request}
        ).data

        result.append({
            "id_job_application": app.id_job_application,
            "status": STATUS_LABELS.get(app.status, app.status),
            "created_at": format_date(app.created_at),
            "updated_at": format_date(app.updated_at),
            "job": job_data
        })

    return Response({"applications": result}, status=200)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def load_cvu(request):
    id_candidate = request.data.get('id_candidate')
    if not id_candidate:
        return Response(
            {'error': 'id_candidate is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        candidate = Candidate.objects.get(id_candidate=id_candidate)
    except Candidate.DoesNotExist:
        return Response(
            {'error': 'Candidate not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    if 'cvu' not in request.FILES:
        return Response(
            {'error': 'No CVU file provided'},
            status=status.HTTP_400_BAD_REQUEST
        )

    cvu_file = request.FILES['cvu']

    # -----------------------------
    # Validar PDF
    # -----------------------------
    if cvu_file.content_type != 'application/pdf':
        return Response(
            {'error': 'Only PDF files are allowed'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not cvu_file.name.lower().endswith('.pdf'):
        return Response(
            {'error': 'File extension must be .pdf'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # -----------------------------
    # BORRAR CVU EXISTENTE (si hay)
    # -----------------------------
    if candidate.cvu:
        if default_storage.exists(candidate.cvu.name):
            default_storage.delete(candidate.cvu.name)

        # Limpia el campo en memoria
        candidate.cvu = None

    # -----------------------------
    # Guardar nuevo CVU
    # -----------------------------
    candidate.cvu.save(
        cvu_file.name,
        cvu_file,
        save=True
    )

    return Response(
        {"message": "Your resum file has been updated"},
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_cvu(request):
    id_candidate = request.data.get('id_candidate')

    if not id_candidate:
        return Response({'error': 'id_candidate is required'}, status=400)

    candidate = get_object_or_404(Candidate, id_candidate=id_candidate)

    if not candidate.cvu:
        return Response({'error': 'CVU not found'}, status=404)

    file_path = candidate.cvu.path

    if not os.path.exists(file_path):
        return Response({'error': 'File does not exist'}, status=404)

    user_account = request.user

    if user_account.subscription == 'ADMIN':
        # Los admins solo descargan, no cuentan
        pass
    elif user_account.subscription in ['company']:
        try:
            company = Company.objects.get(account_id=user_account.id_account)
            company.cvu_downloads += 1
            company.save(update_fields=['cvu_downloads'])
        except Company.DoesNotExist:
            return Response(
                {"error": "Company not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    else:
        # Otros usuarios no deben incrementar nada
        pass

    download_name = f'{candidate.first_name}_{candidate.last_name}.pdf'

    response = FileResponse(
        open(file_path, 'rb'),
        content_type='application/pdf'
    )

    return response

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def toggle_candidate_active(request):
    """
    Toggle del campo is_active del candidato.
    El id_candidate viene en el body (JSON).
    """
    try:
        id_candidate = request.data.get('id_candidate')

        if not id_candidate:
            return Response(
                {"error": "id_candidate is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        candidate = Candidate.objects.get(id_candidate=id_candidate)

        candidate.is_active = not candidate.is_active
        candidate.save(update_fields=['is_active'])

        return Response({
            "message": "Candidate is_active updated successfully",
            "id_candidate": candidate.id_candidate,
            "is_active": candidate.is_active
        }, status=status.HTTP_200_OK)

    except Candidate.DoesNotExist:
        return Response(
            {"error": "Candidate not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    except Exception as e:
        return Response(
            {"error": "Unexpected server error", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

from django.db.models import Count, Q

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def search_candidate_admin(request):
    # print(request.data)

    try:
        data = request.data or {}

        # -------------------------------
        # INPUTS
        # -------------------------------
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        desired_position = data.get('desired_position')
        job_type = data.get('job_type')
        employment_type = data.get('employment_type')
        modality = data.get('modality')
        salary = data.get('salary')
        is_active = data.get('is_active')

        last_position = data.get('last_position')
        adult = data.get('adult')
        work_permission = data.get('work_permission')
        years_experience = data.get('years_experience')
        servsafe = data.get('servsafe')

        schedule_input = data.get('schedule')
        order_by = data.get('order_by')

        candidates = Candidate.objects.all()

        # -------------------------------
        # FILTERS
        # -------------------------------
        if first_name:
            candidates = candidates.filter(first_name__icontains=first_name)

        if last_name:
            candidates = candidates.filter(last_name__icontains=last_name)

        if desired_position:
            candidates = candidates.filter(desired_position__icontains=desired_position)

        if last_position:
            candidates = candidates.filter(last_position__icontains=last_position)

        if job_type:
            candidates = candidates.filter(job_type=job_type)

        if employment_type:
            candidates = candidates.filter(employment_type=employment_type)

        if modality:
            candidates = candidates.filter(modality=modality)

        if is_active:
            candidates = candidates.filter(is_active=is_active)

        if salary:
            candidates = candidates.filter(salary__lte=salary)

        if years_experience:
            candidates = candidates.filter(years_experience__gte=years_experience)

        if adult is not None:
            candidates = candidates.filter(adult=adult)

        if work_permission is not None:
            candidates = candidates.filter(work_permission=work_permission)

        if servsafe is not None:
            candidates = candidates.filter(servsafe=servsafe)

        # -------------------------------
        # APPLICATIONS COUNT
        # -------------------------------
        if order_by in ['applications_count', '-applications_count']:
            candidates = candidates.annotate(
                applications_count=Count('jobapplication')
            )

        # -------------------------------
        # ORDER BY
        # -------------------------------
        if order_by:
            candidates = candidates.order_by(order_by)
        else:
            candidates = candidates.order_by('-created_at')

        # -------------------------------
        # SERIALIZE
        # -------------------------------
        serializer = CandidateAdminSerializer(
            candidates,
            many=True,
            context={'request': request}
        )
        candidates_data = serializer.data

        # =====================================================
        # NORMALIZAR schedules → schedule (MISMA ESTRUCTURA)
        # =====================================================
        from collections import defaultdict

        for cand in candidates_data:
            temp_schedule = defaultdict(list)

            for sched in cand.get("schedules", []):
                if sched.get("type") == "permanent":
                    temp_schedule["permanent"].append({
                        "day": sched.get("day"),
                        "time_start": sched.get("time_start"),
                        "time_end": sched.get("time_finish"),
                        "hired_date": sched.get("date_start"),
                    })

                elif sched.get("type") == "range":
                    temp_schedule["range"].append({
                        "date_start": sched.get("date_start"),
                        "date_end": sched.get("date_end"),
                        "time_start": sched.get("time_start"),
                        "time_end": sched.get("time_finish"),
                    })

                elif sched.get("type") == "multiple":
                    temp_schedule["multiple"].append({
                        "date": sched.get("date_start"),
                        "time_start": sched.get("time_start"),
                        "time_end": sched.get("time_finish"),
                    })

            schedule_data = []
            for sched_type, items in temp_schedule.items():
                hired_date = items[0].get("hired_date") if items else None
                schedule_data.append({
                    "type": sched_type,
                    "hired_date": hired_date,
                    "dates" if sched_type == "multiple" else "days": items
                })

            cand["schedule"] = schedule_data

        # =====================================================
        # FILTRO POR SCHEDULE (MISMA LÓGICA)
        # =====================================================
        filtered_candidates = []
        ranges = []
        multiples = []

        if schedule_input:
            if isinstance(schedule_input, list):
                schedule_str = schedule_input[0]
            else:
                schedule_str = schedule_input

            try:
                schedule_data = json.loads(schedule_str)
                ranges = schedule_data.get("range", [])
                # print("ranges",ranges)
                multiples = schedule_data.get("multiple", [])
                # print("multiples",multiples)
            except (ValueError, TypeError, json.JSONDecodeError):
                ranges = []
                multiples = []

            for cand in candidates_data:
                match = False

                # -------- RANGE --------
                if ranges:
                    r = ranges[0]
                    r_date_start = parse_date(r.get("date_start"))
                    r_date_end = parse_date(r.get("date_end"))
                    r_hour_start = parse_time(r.get("hour_start"))
                    r_hour_end = parse_time(r.get("hour_end"))

                    for sched in cand.get("schedule", []):
                        hired_date = parse_date(sched.get("hired_date"))
                        if not hired_date:
                            continue

                        if not (
                            hired_date < r_date_start or
                            (r_date_start <= hired_date <= r_date_end)
                        ):
                            continue

                        days = sched.get("days", sched.get("dates", []))
                        for d in days:
                            day_start = parse_time(d.get("time_start"))
                            day_end = parse_time(d.get("time_end"))
                            if hours_intersect(r_hour_start, r_hour_end, day_start, day_end):
                                match = True
                                break
                        if match:
                            break

                    if match:
                        filtered_candidates.append(cand)

                # -------- MULTIPLE --------
                elif multiples:
                    permanent_days = []

                    for sched in cand.get("schedule", []):
                        if sched.get("type") == "permanent":
                            permanent_days = sched.get("days", [])
                            break

                    if not permanent_days:
                        continue

                    match_found = False

                    for m_item in multiples:
                        m_date = parse_date(m_item.get("date_start"))
                        if not m_date:
                            continue

                        m_weekday = WEEKDAY_MAP[m_date.weekday()]
                        m_hour_start = parse_time(m_item.get("hour_start"))
                        m_hour_end = parse_time(m_item.get("hour_end"))

                        for d in permanent_days:
                            d_hired_date = parse_date(d.get("hired_date"))
                            if d_hired_date and m_date < d_hired_date:
                                continue

                            if d.get("day") != m_weekday:
                                continue

                            day_start = parse_time(d.get("time_start"))
                            day_end = parse_time(d.get("time_end"))

                            if hours_intersect(m_hour_start, m_hour_end, day_start, day_end):
                                match_found = True
                                break

                        if match_found:
                            break

                    if match_found:
                        filtered_candidates.append(cand)

        else:
            filtered_candidates = candidates_data

        return Response(
            {
                "total": len(filtered_candidates),
                "candidates": filtered_candidates
            },
            status=status.HTTP_200_OK
        )

    except Exception as e:
        return Response(
            {
                "error": "Unexpected server error",
                "details": str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def candidate_admin_stats(request):
    try:
        data = get_candidate_admin_stats()
        return Response(data, status=200)

    except Exception as e:
        return Response(
            {
                "error": "Unable to retrieve candidate admin stats",
                "details": str(e)
            },
            status=500
        )
