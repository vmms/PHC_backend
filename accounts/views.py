from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Account
from .serializers import AccountSerializer, TokenLoginRequestSerializer, TokenLoginResponseSerializer, ErrorResponseSerializer
from django.contrib.auth.models import AnonymousUser
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from datetime import timedelta


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_accounts(request):
    """Lista todos los usuarios registrados en la tabla account"""
    accounts = Account.objects.all()
    serializer = AccountSerializer(accounts, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def create_account(request):
    serializer = AccountSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def read_account(request):
    """Permite leer uno o todos los registros"""
    id_account = request.data.get("id_account")

    if id_account:
        try:
            account = Account.objects.get(id_account=id_account)
            serializer = AccountSerializer(account)
            return Response(serializer.data)
        except Account.DoesNotExist:
            return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)
    else:
        accounts = Account.objects.all()
        serializer = AccountSerializer(accounts, many=True)
        return Response(serializer.data)


@api_view(['POST'])
def update_account(request):
    id_account = request.data.get("id_account")
    if not id_account:
        return Response({"error": "Missing id_account"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        account = Account.objects.get(id_account=id_account)
    except Account.DoesNotExist:
        return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = AccountSerializer(account, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def delete_account(request):
    id_account = request.data.get("id_account")
    if not id_account:
        return Response({"error": "Missing id_account"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        account = Account.objects.get(id_account=id_account)
    except Account.DoesNotExist:
        return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)

    account.delete()
    return Response({"message": "Account deleted successfully"}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([])
def token_login(request):
    username = request.data.get('user')
    password = request.data.get('password')

    if not username or not password:
        return Response({"code": 0, "message": "Se requiere usuario y contraseña"}, status=400)

    try:
        account = Account.objects.get(user=username)
    except Account.DoesNotExist:
        return Response({"code": 0, "message": "Usuario no encontrado"}, status=404)

    if account.password != password:
        return Response({"code": 0, "message": "Contraseña incorrecta"}, status=401)

    # --- CREAR TOKENS MANUALMENTE ---
    # Refresh token con expiración (por ejemplo 7 días)
    refresh = RefreshToken()
    refresh.set_exp(lifetime=timedelta(days=7))
    refresh['id_account'] = account.id_account
    refresh['user'] = account.user
    refresh['subscription'] = account.subscription

    # Access token con expiración (por ejemplo 1 hora)
    access = AccessToken()
    access.set_exp(lifetime=timedelta(hours=1))
    access['id_account'] = account.id_account
    access['user'] = account.user
    access['subscription'] = account.subscription

    # Debug: imprime payload para revisar
    print("Access token payload:", access.payload)
    print("Refresh token payload:", refresh.payload)

    return Response({
        "code": 1,
        "message": "Acceso permitido",
        "refresh": str(refresh),
        "access": str(access),
        "id_account": account.id_account,
        "user": account.user,
        "subscription": account.subscription
    }, status=status.HTTP_200_OK)
