from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response 
from rest_framework.parsers import MultiPartParser, FormParser

from .models import Company
from .serializers import CompanySerializer, CompanyAdminSerializer
from collections import defaultdict
from django.shortcuts import get_object_or_404
from django.db.models import Q, Exists, OuterRef

from jobs.models import Job, SkillsHasJobs, ScheduleHasJobs
from jobs.serializers import JobSerializer
from jobApplication.models import JobApplication
from jobApplication.serializers import JobApplicationSerializer
from candidates.models import Candidate, CandidateHasSchedule
from candidates.serializers import CandidatePublicSerializer, CandidateContactSerializer
from companies.services import get_company_admin_stats

from geopy.geocoders import Nominatim
from math import radians, sin, cos, sqrt, atan2
from datetime import datetime, time
from django.utils import timezone
import json

WEEKDAY_MAP = {
    0: "mon",
    1: "tue",
    2: "wed",
    3: "thu",
    4: "fri",
    5: "sat",
    6: "sun",
}

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_companies(request):
    try:
        companies = Company.objects.all()

        total = companies.count()  # Número total de companies

        serializer = CompanyAdminSerializer(companies, many=True, context={'request': request})

        return Response({
            "total": total,
            "companies": serializer.data
        }, status=status.HTTP_200_OK)

    except DatabaseError:
        return Response({"error": "Database error while fetching companies"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        return Response({"error": "Unexpected server error", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_company(request):
    try:
        # Usar account_id en lugar de account
        company = Company.objects.get(account_id=request.user.id_account)
        serializer = CompanyAdminSerializer(company, context={'request': request})
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

def format_date(date):
    if not date:
        return None
    return date.strftime("%m-%d-%Y")

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_my_job_applications(request):
    try:
        company = Company.objects.get(account=request.user)
        
        # 🔹 Filtros recibidos (pueden venir o no)
        title = request.data.get("title")
        first_name = request.data.get("first_name")
        last_name = request.data.get("last_name")

        # 🔹 Jobs de la company
        jobs = Job.objects.filter(company=company)

        # 🔹 Filtro por título del job
        if title:
            jobs = jobs.filter(title__icontains=title)

        jobs_data = []

        for job in jobs:
            applications = JobApplication.objects.filter(id_jobs=job)

            # 🔹 Filtros por candidato
            if first_name:
                applications = applications.filter(
                    id_candidate__first_name__icontains=first_name
                )

            if last_name:
                applications = applications.filter(
                    id_candidate__last_name__icontains=last_name
                )

            applications_data = []
            for app in applications:
                applications_data.append({
                    "id_job_application": app.id_job_application,
                    "id_jobs": app.id_jobs.id_jobs,
                    "id_candidate": app.id_candidate.id_candidate,
                    "candidate_name": f"{app.id_candidate.first_name} {app.id_candidate.last_name}",
                    "status": app.status,
                    "created_at": format_date(app.created_at),
                    "updated_at": format_date(app.updated_at),
                })

            # 🔹 Opcional: no regresar jobs sin aplicaciones
            if applications_data:
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

def mark_application_as_viewed(id_job_application):
    if not id_job_application:
        return

    JobApplication.objects.filter(
        id_job_application=id_job_application
    ).update(
        status="application_viewed",
        updated_at=timezone.now()
    )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_candidate_public(request):
    print(request.data)
    id_candidate = request.data.get('id_candidate')
    id_job_application = request.data.get("id_job_application")
    

    if not id_candidate:
        return Response(
            {'error': 'id_candidate is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    candidate = get_object_or_404(
        Candidate,
        id_candidate=id_candidate
    )

    if id_job_application:
        mark_application_as_viewed(id_job_application)

    # -------- Schedule (tu lógica intacta) --------
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
    id_candidate = request.data.get("id_candidate")
    id_job_application = request.data.get("id_job_application")

    if not id_candidate:
        return Response({"error": "id_candidate is required"}, status=400)

    if id_job_application:
        mark_application_as_viewed(id_job_application)

    candidate = get_object_or_404(
        Candidate,
        id_candidate=id_candidate
    )

    try:
        company = Company.objects.get(account_id=request.user.id_account)
        company.profile_views += 1
        company.save(update_fields=['profile_views'])
    except Company.DoesNotExist:
        return Response({"error": "Compañía no encontrada"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": "Error del servidor", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    is_admin = request.user.subscription == 'ADMIN'

    if not is_admin:
        candidate.profile_views += 1
        candidate.save(update_fields=['profile_views'])

    serializer = CandidateContactSerializer(
        candidate,
        context={"request": request}
    )

    return Response(serializer.data, status=status.HTTP_200_OK) 

def parse_date(d):
    if not d:
        return None
    return datetime.strptime(d, "%Y-%m-%d").date()

def parse_time(t):
    if not t:
        return None
    return datetime.strptime(t, "%H:%M").time()

def hours_intersect(start1, end1, start2, end2):
    """Verifica si dos rangos de horas se intersectan"""
    return max(start1, start2) < min(end1, end2)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def search_candidates(request):
    # print("request.data:")
    # print(request.data)
    data = request.data or {}

    # -----------------------------------
    # 1. Validar company desde account
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
    candidates = Candidate.objects.filter(is_active=1).select_related('address')

    # -----------------------------------
    # 3. Filtros simples
    # -----------------------------------
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    desired_position = data.get('desired_position')
    job_type = data.get('job_type')
    employment_type = data.get('employment_type')
    modality = data.get('modality')
    salary_max = data.get('salary')

    last_position = data.get('last_position')
    adult = data.get('adult')
    work_permission = data.get('work_permission')
    years_experience = data.get('years_experience')
    servsafe = data.get('servsafe')


    location = data.get('location')        # ciudad de referencia
    radius_miles = data.get('radius_miles', 350)

    if first_name and isinstance(first_name, str) and first_name.lower() != 'none':
        candidates = candidates.filter(first_name__icontains=first_name)

    if last_name and isinstance(last_name, str) and last_name.lower() != 'none':
        candidates = candidates.filter(last_name__icontains=last_name)

    if desired_position and isinstance(desired_position, str) and desired_position.lower() != 'none':
        candidates = candidates.filter(desired_position__icontains=desired_position)

    if job_type and isinstance(job_type, str) and job_type.lower() != 'none':
        candidates = candidates.filter(job_type__iexact=job_type)

    if employment_type and isinstance(employment_type, str) and employment_type.lower() != 'none':
        candidates = candidates.filter(employment_type__iexact=employment_type)

    if modality and isinstance(modality, str) and modality.lower() != 'none':
        candidates = candidates.filter(modality__iexact=modality)

    if salary_max is not None:
        try:
            salary_max = float(salary_max)
            candidates = candidates.extra(
                where=["CAST(salary AS DECIMAL) <= %s"],
                params=[salary_max]
            )
        except ValueError:
            return Response(
                {"message": "salary must be a number"},
                status=status.HTTP_400_BAD_REQUEST
            )
    if last_position and isinstance(last_position, str) and last_position.lower() != 'none':
        candidates = candidates.filter(last_position__iexact=last_position)

    if adult and isinstance(adult, str) and adult.lower() != 'none':
        if adult.lower() == 'yes':
            adult_value = 1
        elif adult.lower() == 'no':
            adult_value = 0
        else:
            adult_value = None  # por si mandan algo raro

        if adult_value is not None:
            candidates = candidates.filter(adult=adult_value)

    if work_permission and isinstance(work_permission, str) and work_permission.lower() != 'none':
        if work_permission.lower() == 'yes':
            wp_value = 1
        elif work_permission.lower() == 'no':
            wp_value = 0
        else:
            wp_value = None

        if wp_value is not None:
            candidates = candidates.filter(work_permission=wp_value)
    
    if years_experience not in (None, "", "none"):
        try:
            years_experience = int(years_experience)
            candidates = candidates.filter(years_experience__gte=years_experience)
        except (TypeError, ValueError):
            return Response(
                {"message": "years_experience must be a number"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    if servsafe and isinstance(servsafe, str) and servsafe.lower() != 'none':
        candidates = candidates.filter(servsafe__iexact=servsafe)
    

    # -----------------------------------
    # 4. Filtro por distancia (CON CACHE)
    # -----------------------------------
    if location and isinstance(location, str) and location.lower() != 'none':
        try:
            geolocator = Nominatim(user_agent="PHC_backend_search_candidates")
            ref_loc = geolocator.geocode(location, timeout=10)

            if not ref_loc:
                return Response(
                    {"message": "Reference city not found"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            ref_lat, ref_lng = ref_loc.latitude, ref_loc.longitude
            radius_miles = float(radius_miles)

        except Exception as e:
            return Response(
                {"message": f"Error obtaining coordinates: {e}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        geo_cache = {}       
        request_count = 0
        filtered_candidates = []

        for candidate in candidates:
            addr = candidate.address
            if not addr or not addr.city:
                continue

            addr_key = f"{addr.city}|{addr.state}|{addr.country}"

            # -------------------------
            # Cache hit
            # -------------------------
            if addr_key in geo_cache:
                cand_lat, cand_lng = geo_cache[addr_key]

            # -------------------------
            # Cache miss
            # -------------------------
            else:
                try:
                    if request_count > 0:
                        time.sleep(1.2)  # delay controlado

                    query = f"{addr.city}, {addr.state or ''}, {addr.country or ''}"
                    loc = geolocator.geocode(query, timeout=10)
                    request_count += 1

                    if not loc:
                        continue

                    cand_lat, cand_lng = loc.latitude, loc.longitude
                    geo_cache[addr_key] = (cand_lat, cand_lng)

                except Exception:
                    continue

            dist = haversine(ref_lat, ref_lng, cand_lat, cand_lng)

            if dist <= radius_miles:
                filtered_candidates.append(candidate)

        candidates = filtered_candidates

    # -----------------------------------
    # 5. Serializar + Schedule
    # -----------------------------------
    serializer = CandidatePublicSerializer(
        candidates,
        many=True,
        context={'request': request}
    )

    candidates_data = serializer.data

    # -----------------------------------
    # 6. Filtrado por schedule DESPUÉS de serializar
    # -----------------------------------

    for cand_data in candidates_data:
        cand_id = cand_data.get("id_candidate")

        try:
            cand_obj = Candidate.objects.get(id_candidate=cand_id)
        except Candidate.DoesNotExist:
            cand_data["schedule"] = []
            continue

        temp_schedule = defaultdict(list)

        for link in CandidateHasSchedule.objects.filter(candidate=cand_obj).select_related('schedule'):
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

        # Al final, agregamos hired_date en schedule_data
        schedule_data = []
        for sched_type, items in temp_schedule.items():
            hired_date = items[0].get("hired_date") if items else None
            schedule_data.append({
                "type": sched_type,
                "hired_date": hired_date,
                "dates" if sched_type == "multiple" else "days": items
            })

        cand_data["schedule"] = schedule_data
    
    # print(candidates_data)
    schedule_str = data.get('schedule')
    schedule_data = {}
    ranges = []
    multiples = []

    filtered_candidates = []

    if schedule_str:  # viene algo del frontend
        #print("filtra por hora")
        try:
            # print("parsear el JSON del string")
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

            # --- FILTRO POR RANGE ---
            if ranges:
                r = ranges[0]  # siempre solo hay uno
                r_date_start = parse_date(r.get("date_start"))
                r_date_end = parse_date(r.get("date_end"))
                r_hour_start = parse_time(r.get("hour_start"))
                r_hour_end = parse_time(r.get("hour_end"))

                for sched in cand.get("schedule", []):
                    hired_date = parse_date(sched.get("hired_date"))
                    if not hired_date:
                        continue

                    # Paso 1: hired_date dentro del rango
                    if not (
                        hired_date < r_date_start or
                        (r_date_start <= hired_date <= r_date_end)
                    ):
                        continue

                    # Paso 2: verificar horas de cada day dentro del schedule
                    days = sched.get("days", sched.get("dates", []))
                    for d in days:
                        day_start = parse_time(d.get("time_start"))
                        day_end = parse_time(d.get("time_end"))
                        if hours_intersect(r_hour_start, r_hour_end, day_start, day_end):
                            match = True
                            break
                    if match:
                        break

                # 🔹 Guardar candidato si hubo match en RANGE
                if match:
                    filtered_candidates.append(cand)

            # --- FILTRO POR MULTIPLE ---
            elif multiples:
                # 🔹 Siempre tomar los días del schedule permanente
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
                        # hired_date
                        d_hired_date = parse_date(d.get("hired_date"))
                        if d_hired_date and m_date < d_hired_date:
                            continue

                        # día de la semana
                        if d.get("day") != m_weekday:
                            continue

                        # cruce horario
                        day_start = parse_time(d.get("time_start"))
                        day_end = parse_time(d.get("time_end"))

                        if hours_intersect(m_hour_start, m_hour_end, day_start, day_end):
                            match_found = True
                            break

                    if match_found:
                        break

                # 🔹 Guardar candidato si hubo match en MULTIPLE
                if match_found:
                    filtered_candidates.append(cand)

    else:
        #print("no filtrar por hora")
        filtered_candidates = candidates_data

    #print(filtered_candidates)
    return Response({"candidates": filtered_candidates}, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def company_admin_stats(request):
    try:
        data = get_company_admin_stats()
        return Response(data, status=200)

    except Exception as e:
        return Response(
            {
                "error": "Unable to retrieve company admin stats",
                "details": str(e)
            },
            status=500
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_search_companies(request):
    data = request.data

    companies = Company.objects.select_related(
        'address',
        'account'
    )

    # -----------------------
    # FILTROS (opcionales)
    # -----------------------
    name = data.get('name')
    city = data.get('city')
    subscription = data.get('subscription')
    type_business = data.get('type_business')
    is_active = data.get('is_active')
    order_by = data.get('order_by')

    if name:
        companies = companies.filter(name__icontains=name)

    if city:
        companies = companies.filter(address__city__icontains=city)

    if subscription:
        companies = companies.filter(account__subscription=subscription)

    if type_business:
        companies = companies.filter(type_business=type_business)

    if is_active is not None:
        companies = companies.filter(is_active=is_active)

    # -----------------------
    # ORDEN
    # -----------------------
    if order_by:
        companies = companies.order_by(order_by)
    else:
        companies = companies.order_by('-created_at')

    # -----------------------
    # RESPONSE
    # -----------------------
    serializer = CompanyAdminSerializer(companies, many=True)

    return Response({
        "total": companies.count(),
        "companies": serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def company_admin_detail(request):
    id_company = request.data.get('id_company')

    if not id_company:
        return Response(
            {"error": "id_company is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        company = Company.objects.select_related(
            'account',
            'address'
        ).get(id_company=id_company)

    except Company.DoesNotExist:
        return Response(
            {"error": "Company not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = CompanyAdminSerializer(
        company,
        context={"request": request}
    )

    return Response(serializer.data, status=status.HTTP_200_OK)

