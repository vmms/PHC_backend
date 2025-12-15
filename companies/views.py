from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response 
from rest_framework.parsers import MultiPartParser, FormParser

from .models import Company
from .serializers import CompanySerializer

from jobs.models import Job
from jobApplication.models import JobApplication
from jobApplication.serializers import JobApplicationSerializer


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
                    "created_at": app.created_at
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