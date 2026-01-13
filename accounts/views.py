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
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([])
def create_account(request):
    username = request.data.get('user')

    if not username:
        return Response(
            {"detail": "User is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if Account.objects.filter(user=username).exists():
        return Response(
            {"detail": "This username is already in use."},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = AccountSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([])
def google_register(request):
    token = request.data.get('token')

    if not token:
        return Response(
            {"detail": "Google token required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validar token con Google
    r = requests.get(
        'https://www.googleapis.com/oauth2/v3/userinfo',
        headers={'Authorization': f'Bearer {token}'}
    )

    if r.status_code != 200:
        return Response(
            {"detail": "Invalid Google token"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    data = r.json()

    email = data.get('email')
    google_id = data.get('sub')

    if not email:
        return Response(
            {"detail": "Google account has no email"},
            status=status.HTTP_400_BAD_REQUEST
        )

    account = Account.objects.filter(email=email).first()

    if not account:
        # CREAR CUENTA NUEVA
        account = Account.objects.create(
            user=email,
            email=email,
            google_id=google_id,
            password=None,
            status=1,
            subscription='free'
        )
    else:
        # VINCULAR GOOGLE SI YA EXISTÍA
        if not account.google_id:
            account.google_id = google_id
            account.save()

    # GENERAR TOKENS (MISMO SISTEMA)
    refresh = RefreshToken()
    refresh.set_exp(lifetime=timedelta(days=7))
    refresh['id_account'] = account.id_account
    refresh['user'] = account.user
    refresh['subscription'] = account.subscription

    access = AccessToken()
    access.set_exp(lifetime=timedelta(hours=1))
    access['id_account'] = account.id_account
    access['user'] = account.user
    access['subscription'] = account.subscription

    return Response({
        "code": 1,
        "message": "Google login successful",
        "refresh": str(refresh),
        "access": str(access),
        "id_account": account.id_account,
        "user": account.user,
        "subscription": account.subscription
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([])
def facebook_register(request):
    token = request.data.get('token')

    if not token:
        return Response(
            {"detail": "Facebook token required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    r = requests.get(
        'https://graph.facebook.com/me',
        params={
            'fields': 'id,email,name',
            'access_token': token
        }
    )

    if r.status_code != 200:
        return Response(
            {"detail": "Invalid Facebook token"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    data = r.json()

    email = data.get('email')
    facebook_id = data.get('id')

    if not email:
        return Response(
            {"detail": "Facebook account has no email"},
            status=status.HTTP_400_BAD_REQUEST
        )

    account = Account.objects.filter(email=email).first()

    if not account:
        account = Account.objects.create(
            user=email,
            email=email,
            facebook_id=facebook_id,
            password=None,
            status=1,
            subscription='free'
        )
    else:
        if not account.facebook_id:
            account.facebook_id = facebook_id
            account.save()

    refresh = RefreshToken()
    refresh.set_exp(lifetime=timedelta(days=7))
    refresh['id_account'] = account.id_account
    refresh['user'] = account.user
    refresh['subscription'] = account.subscription

    access = AccessToken()
    access.set_exp(lifetime=timedelta(hours=1))
    access['id_account'] = account.id_account
    access['user'] = account.user
    access['subscription'] = account.subscription

    return Response({
        "code": 1,
        "message": "Facebook login successful",
        "refresh": str(refresh),
        "access": str(access),
        "id_account": account.id_account,
        "user": account.user,
        "subscription": account.subscription
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def read_account(request):
    user = request.user.user 

    try:
        account = Account.objects.get(user=user)
    except Account.DoesNotExist:
        return Response(
            {"error": "Account not found for this user"},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = AccountSerializer(account)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_account(request):
    # ID del usuario autenticado
    id_account = request.user.id_account

    try:
        account = Account.objects.get(id_account=id_account)
    except Account.DoesNotExist:
        return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)

    # Solo permitimos actualizar estos campos
    allowed_fields = {"status", "password", "subscription"}
    data = {k: v for k, v in request.data.items() if k in allowed_fields}

    if not data:
        return Response({"error": "No valid fields provided"}, status=status.HTTP_400_BAD_REQUEST)

    # Actualizar los campos directamente
    for field, value in data.items():
        setattr(account, field, value)
    account.save()

    serializer = AccountSerializer(account, data=data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deactivate_account(request):
    # Obtener la cuenta del usuario autenticado
    id_account = request.user.id_account

    try:
        account = Account.objects.get(id_account=id_account)
    except Account.DoesNotExist:
        return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)

    # Cambiar status a 0 (desactivado)
    account.status = 0
    account.save()

    return Response({"message": "Account deactivated successfully"}, status=status.HTTP_200_OK)

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

@api_view(['POST'])
@permission_classes([])
def google_login(request):
    token = request.data.get('token')

    if not token:
        return Response({"code": 0, "message": "Token requerido"}, status=400)

    # Validar token con Google
    r = requests.get(
        'https://www.googleapis.com/oauth2/v3/userinfo',
        headers={'Authorization': f'Bearer {token}'}
    )

    if r.status_code != 200:
        return Response({"code": 0, "message": "Token Google inválido"}, status=401)

    data = r.json()

    email = data.get('email')
    google_id = data.get('sub')

    if not email:
        return Response({"code": 0, "message": "Google no devolvió email"}, status=400)

    account = Account.objects.filter(email=email).first()

    if account:
        if not account.google_id:
            account.google_id = google_id
            account.save()
    else:
        account = Account.objects.create(
            user=email,
            email=email,
            google_id=google_id,
            password=None,
            status=1,
            subscription='free'
        )

    # === TU MISMO TOKEN ===
    refresh = RefreshToken()
    refresh.set_exp(lifetime=timedelta(days=7))
    refresh['id_account'] = account.id_account
    refresh['user'] = account.user
    refresh['subscription'] = account.subscription

    access = AccessToken()
    access.set_exp(lifetime=timedelta(hours=1))
    access['id_account'] = account.id_account
    access['user'] = account.user
    access['subscription'] = account.subscription

    return Response({
        "code": 1,
        "message": "Login Google OK",
        "refresh": str(refresh),
        "access": str(access),
        "id_account": account.id_account,
        "user": account.user,
        "subscription": account.subscription
    })

@api_view(['POST'])
@permission_classes([])
def facebook_login(request):
    token = request.data.get('token')

    if not token:
        return Response({"code": 0, "message": "Token requerido"}, status=400)

    r = requests.get(
        'https://graph.facebook.com/me',
        params={
            'fields': 'id,email,name',
            'access_token': token
        }
    )

    if r.status_code != 200:
        return Response({"code": 0, "message": "Token Facebook inválido"}, status=401)

    data = r.json()

    email = data.get('email')
    facebook_id = data.get('id')

    if not email:
        return Response({"code": 0, "message": "Facebook no devolvió email"}, status=400)

    account = Account.objects.filter(email=email).first()

    if account:
        if not account.facebook_id:
            account.facebook_id = facebook_id
            account.save()
    else:
        account = Account.objects.create(
            user=email,
            email=email,
            facebook_id=facebook_id,
            password=None,
            status=1,
            subscription='free'
        )

    refresh = RefreshToken()
    refresh.set_exp(lifetime=timedelta(days=7))
    refresh['id_account'] = account.id_account
    refresh['user'] = account.user
    refresh['subscription'] = account.subscription

    access = AccessToken()
    access.set_exp(lifetime=timedelta(hours=1))
    access['id_account'] = account.id_account
    access['user'] = account.user
    access['subscription'] = account.subscription

    return Response({
        "code": 1,
        "message": "Login Facebook OK",
        "refresh": str(refresh),
        "access": str(access),
        "id_account": account.id_account,
        "user": account.user,
        "subscription": account.subscription
    })