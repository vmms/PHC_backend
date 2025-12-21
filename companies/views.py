from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response 
from rest_framework.parsers import MultiPartParser, FormParser

from .models import Company
from .serializers import CompanySerializer
from collections import defaultdict
from django.shortcuts import get_object_or_404

from jobs.models import Job, SkillsHasJobs, ScheduleHasJobs
from jobs.serializers import JobSerializer
from jobApplication.models import JobApplication
from jobApplication.serializers import JobApplicationSerializer
from candidates.models import Candidate, CandidateHasSchedule
from candidates.serializers import CandidatePublicSerializer, CandidateContactSerializer

from geopy.geocoders import Nominatim
from math import radians, sin, cos, sqrt, atan2


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_companies(request):
    try:
        companies = Company.objects.all()

        if not companies.exists():
            return Response({"message": "No companies found", "results": []}, status=status.HTTP_200_OK)

        return Response({"message": "Imagen subida con éxito"}, status=status.HTTP_200_OK)

    except DatabaseError:
        return Response({"error": "Database error while fetching companies"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        # Cualquier error inesperado
        return Response({"error": "Unexpected server error", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_company(request):
    try:
        # Usar account_id en lugar de account
        company = Company.objects.get(account_id=request.user.id_account)
        serializer = CompanySerializer(company, context={'request': request})
        return Response(serializer.data, status=200)
    except Company.DoesNotExist:
        return Response(
            {'message': 'No company associated with this user'}, 
            status=404
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_company(request):
    serializer = CompanySerializer(data=request.data)
    if serializer.is_valid():
        # Asignar automáticamente el account desde el token
        serializer.save(account=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_company_logo(request):
    id_company = request.data.get('id_company')
    if not id_company:
        return Response({'error': 'id_company is required'}, status=400)

    try:
        company = Company.objects.get(id_company=id_company)
    except Company.DoesNotExist:
        return Response({'error': 'Company not found'}, status=404)

    if 'logo' not in request.FILES:
        return Response({'error': 'No logo file provided'}, status=400)

    # Guardar el logo usando .save() para sobrescribir
    company.logo.save(
        request.FILES['logo'].name,
        request.FILES['logo'],
        save=True
    )

    serializer = CompanySerializer(company, context={'request': request})
    return Response(serializer.data, status=200)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_company(request):

    try:
        company = Company.objects.get(account=request.user)
    except Company.DoesNotExist:
        return Response({'message': 'No company associated with this user'}, status=status.HTTP_404_NOT_FOUND)

    serializer = CompanySerializer(company, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def delete_company(request, pk):
    """Elimina una compañía"""
    try:
        company = Company.objects.get(pk=pk)
    except Company.DoesNotExist:
        return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)

    company.delete()
    return Response({'message': 'Company deleted successfully'}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_my_job_applications(request):
    try:
        # Obtener la company del usuario logueado
        company = Company.objects.get(account=request.user)

        # Obtener los jobs de la company
        jobs = Job.objects.filter(company=company)

        # Construir la respuesta anidada
        jobs_data = []
        for job in jobs:
            applications = JobApplication.objects.filter(id_jobs=job)
            # Construir manualmente la info del candidato
            applications_data = []
            for app in applications:
                applications_data.append({
                    "id_job_application": app.id_job_application,
                    "id_jobs": app.id_jobs.id_jobs,
                    "id_candidate": app.id_candidate.id_candidate,
                    "candidate_name": f"{app.id_candidate.first_name} {app.id_candidate.last_name}",
                    "status": app.status,
                    "created_at": app.created_at.date() if app.created_at else None,
                    "updated_at": app.updated_at.date() if app.updated_at else None,
                })

            jobs_data.append({
                "id_jobs": job.id_jobs,
                "title": job.title,
                "applications": applications_data
            })

        return Response({"jobs": jobs_data}, status=status.HTTP_200_OK)

    except Company.DoesNotExist:
        return Response(
            {"message": "No company associated with this user"},
            status=status.HTTP_404_NOT_FOUND
        )

    except Exception as e:
        return Response(
            {"error": "Unexpected error", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
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
def list_my_jobs(request):
    data = request.data or {}

    # -----------------------------------
    # 1. Obtener company desde account
    # -----------------------------------
    try:
        company = Company.objects.get(account_id=request.user.id_account)
    except Company.DoesNotExist:
        return Response(
            {"message": "User has no associated company"},
            status=status.HTTP_403_FORBIDDEN
        )

    # -----------------------------------
    # 2. Base queryset
    # -----------------------------------
    jobs = Job.objects.filter(company_id=company.id_company)

    # -----------------------------------
    # 3. Filtros simples
    # -----------------------------------
    title = data.get('title')
    location = data.get('location')
    employment_type = data.get('employment_type')
    modality = data.get('modality')
    job_type = data.get('job_type')
    qualifications = data.get('qualifications')
    radius_miles = data.get('radius_miles', 350)
    is_active_filter = data.get('is_active')

    if is_active_filter is None:
        jobs = jobs.filter(is_active=1)
    elif isinstance(is_active_filter, str):
        if is_active_filter.lower() == "active":
            jobs = jobs.filter(is_active=1)
        elif is_active_filter.lower() == "disable":
            jobs = jobs.filter(is_active=0)

    if title and isinstance(title, str) and title.lower() != 'none':
        jobs = jobs.filter(title__icontains=title)

    if employment_type and isinstance(employment_type, str) and employment_type.lower() != 'none':
        jobs = jobs.filter(employment_type__iexact=employment_type)

    if job_type and isinstance(job_type, str) and job_type.lower() != 'none':
        jobs = jobs.filter(job_type__iexact=job_type)

    if modality and isinstance(modality, str) and modality.lower() != 'none':
        jobs = jobs.filter(modality__iexact=modality)

    if qualifications and isinstance(qualifications, str) and qualifications.lower() != 'none':
        jobs = jobs.filter(qualifications__icontains=qualifications)
    
    jobs = jobs.order_by('-created_at')

    # -----------------------------------
    # 4. Filtro por ubicación (IGUAL que list_job)
    # -----------------------------------
    if location and isinstance(location, str) and location.lower() != 'none':
        try:
            from geopy.geocoders import Nominatim
            import time

            geolocator = Nominatim(user_agent="PHC_backend_list_my_jobs")
            city_loc = geolocator.geocode(location, timeout=10)
            time.sleep(2)

            if not city_loc:
                return Response(
                    {"message": "Ciudad no encontrada"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            city_lat, city_lng = city_loc.latitude, city_loc.longitude
            radius_miles = float(radius_miles)

        except Exception as e:
            return Response(
                {"message": f"Error obteniendo coordenadas: {e}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        filtered_jobs = []
        for job in jobs:
            if job.latitude is not None and job.longitude is not None:
                dist = haversine(city_lat, city_lng, job.latitude, job.longitude)
                if dist <= radius_miles:
                    filtered_jobs.append(job)

        jobs = filtered_jobs

    # -----------------------------------
    # 5. Respuesta
    # -----------------------------------
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

        # ----------------------------
        # Skills
        # ----------------------------
        skill_links = SkillsHasJobs.objects.filter(jobs=job_obj).select_related('skills')
        job_data["skills"] = [
            {
                "id_skills": link.skills.id_skills,
                "name": link.skills.name
            }
            for link in skill_links
        ]

        # ----------------------------
        # Schedule
        # ----------------------------
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

    return Response({"jobs": jobs_data}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_candidate_public(request):
    id_candidate = request.data.get('id_candidate')

    if not id_candidate:
        return Response(
            {'error': 'id_candidate is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    candidate = get_object_or_404(
        Candidate,
        id_candidate=id_candidate
    )

    # -----------------------------
    # Schedule (misma lógica)
    # -----------------------------
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

    serializer = CandidatePublicSerializer(
        candidate,
        context={'request': request}
    )

    response_data = serializer.data
    response_data["schedule"] = schedule_data

    return Response(response_data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_candidate_contact_info(request):
    id_candidate = request.data.get('id_candidate')

    if not id_candidate:
        return Response(
            {'error': 'id_candidate is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    candidate = get_object_or_404(
        Candidate,
        id_candidate=id_candidate
    )

    serializer = CandidateContactSerializer(
        candidate,
        context={'request': request}
    )

    return Response(serializer.data, status=status.HTTP_200_OK)