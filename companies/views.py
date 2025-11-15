from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Company
from .serializers import CompanySerializer

@api_view(['GET'])
def list_companies(request):
    """Lista todas las compañías registradas"""
    companies = Company.objects.all()
    serializer = CompanySerializer(companies, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_company(request):
    """
    Devuelve la compañía asociada al usuario autenticado.
    Si no existe, devuelve un mensaje indicando que no hay compañía asociada.
    """
    try:
        company = Company.objects.get(account=request.user)
        serializer = CompanySerializer(company)
        return Response(serializer.data)
    except Company.DoesNotExist:
        return Response({'message': 'No company associated with this user'}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_company(request):
    serializer = CompanySerializer(data=request.data)
    if serializer.is_valid():
        # Asignar automáticamente el account desde el token
        serializer.save(account=request.user)
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_company(request):
    """
    Actualiza la compañía asociada al usuario autenticado.
    Si no existe, devuelve un mensaje de error.
    """
    try:
        company = Company.objects.get(account=request.user)
    except Company.DoesNotExist:
        return Response({'message': 'No company associated with this user'}, status=404)

    serializer = CompanySerializer(company, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=400)


@api_view(['DELETE'])
def delete_company(request, pk):
    """Elimina una compañía"""
    try:
        company = Company.objects.get(pk=pk)
    except Company.DoesNotExist:
        return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)

    company.delete()
    return Response({'message': 'Company deleted successfully'}, status=status.HTTP_200_OK)
