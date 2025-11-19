from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Candidate
from .serializers import CandidateSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_candidate(request):
    """
    Devuelve el candidate asociado al usuario autenticado.
    Si no existe, devuelve un mensaje indicando que no hay candidate asociado.
    """
    try:
        candidate = Candidate.objects.get(account=request.user)
        serializer = CandidateSerializer(candidate)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Candidate.DoesNotExist:
        return Response({'message': 'No candidate associated with this user'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_candidate(request):
    """
    Crea un candidate asociado al usuario autenticado.
    """
    serializer = CandidateSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(account=request.user)
        response_data = serializer.format_response(serializer.instance)
        return Response(response_data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_404_NOT_FOUND)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_candidate(request):
    """
    Actualiza el candidate asociado al usuario autenticado.
    """
    try:
        candidate = Candidate.objects.get(account=request.user)
    except Candidate.DoesNotExist:
        return Response({'message': 'No candidate associated with this user'}, status=status.HTTP_404_NOT_FOUND)

    serializer = CandidateSerializer(candidate, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
    candidates = Candidate.objects.all()
    serializer = CandidateSerializer(candidates, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
