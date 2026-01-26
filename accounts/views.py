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

from companies.models import Company
from candidates.models import Candidate
from addresses.models import Address
from candidates.services import create_candidate_internal

import secrets
import string
from django.db.models import Q
from django.core.mail import send_mail


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_accounts(request):
    """Lista todos los usuarios registrados en la tabla account"""
    accounts = Account.objects.all()
    serializer = AccountSerializer(accounts, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

from django.core.mail import send_mail
from django.conf import settings

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
        account = serializer.save(email=username)  # 👈 GUARDA el objeto
        print("account: ",account.id_account)
        
        if account.subscription == "candidate":
            create_candidate_internal(
                id_account=account.id_account,
                email=account.email
            )

        elif account.subscription == "company":
            from companies.services import create_company_internal

            create_company_internal(
                id_account=account.id_account,
                email=account.email
            )
        
        elif account.subscription == "admin":
            pass 

        send_mail(
            subject="Welcome to Professional Hospitality Connections",
            message=(
                "Welcome to Professional Hospitality Connections!\n\n"
                "Your account has been successfully created.\n\n"
                "You can now log in and start exploring the platform.\n\n"
                "Best regards,\n"
                "Professional Hospitality Connections"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[account.email],
            fail_silently=False  
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
    print(request.data)
    username = request.data.get('user')
    password = request.data.get('password')
    type_account = request.data.get('type')  # 'company' | 'candidate'

    if not username or not password or not type_account:
        return Response(
            {
                "code": 0,
                "message": "Username, password, and account type are required."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        account = Account.objects.get(user=username)
    except Account.DoesNotExist:
        return Response(
            {
                "code": 0,
                "message": "User not found."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    if account.password != password:
        return Response(
            {
                "code": 0,
                "message": "Invalid password."
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    # -------------------------------
    # VALIDATE ACCOUNT TYPE
    # -------------------------------
    
    # ADMIN
    if type_account == 'admin':
        if account.subscription != 'admin':
            return Response(
                {
                    "code": 0,
                    "message": "This account is not an admin account."
                },
                status=status.HTTP_403_FORBIDDEN
            )

    # COMPANY / CANDIDATE
    else:
        is_company = Company.objects.filter(account=account).exists()
        is_candidate = Candidate.objects.filter(account=account).exists()

        if type_account == 'company' and not is_company:
            return Response(
                {
                    "code": 0,
                    "message": "This account is not a company account. Please log in as a candidate."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        if type_account == 'candidate' and not is_candidate:
            return Response(
                {
                    "code": 0,
                    "message": "This account is not a candidate account. Please log in as a company."
                },
                status=status.HTTP_403_FORBIDDEN
            )


    # -------------------------------
    # CREATE TOKENS
    # -------------------------------
    refresh = RefreshToken()
    refresh.set_exp(lifetime=timedelta(days=7))
    refresh['id_account'] = account.id_account
    refresh['user'] = account.user
    refresh['subscription'] = account.subscription
    refresh['type_account'] = type_account

    access = AccessToken()
    access.set_exp(lifetime=timedelta(hours=1))
    access['id_account'] = account.id_account
    access['user'] = account.user
    access['subscription'] = account.subscription
    access['type_account'] = type_account

    return Response(
        {
            "code": 1,
            "message": "Access granted.",
            "refresh": str(refresh),
            "access": str(access),
            "id_account": account.id_account,
            "user": account.user,
            "subscription": account.subscription,
            "type_account": type_account
        },
        status=status.HTTP_200_OK
    )

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

@api_view(['POST'])
@permission_classes([])
def recover_password(request):
    account_value = request.data.get('account')
    type_account = request.data.get('type_account')  # candidate | company

    if not account_value or not type_account:
        return Response(
            {"code": 0, "message": "account and type_account are required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Respuesta genérica (no filtrar existencia)
    generic_response = {
        "code": 1,
        "message": "A new password has been sent to the registered email."
    }

    # -----------------------
    # BUSCAR ACCOUNT
    # -----------------------
    account_obj = Account.objects.filter(
        Q(user=account_value) | Q(email=account_value)
    ).first()

    if not account_obj:
        return Response(generic_response, status=status.HTTP_200_OK)

    # -----------------------
    # OBTENER EMAIL SEGÚN TIPO
    # -----------------------
    email = None

    if type_account == 'candidate':
        candidate = Candidate.objects.filter(account_id=account_obj.id_account).first()
        if candidate and candidate.email:
            email = candidate.email

    elif type_account == 'company':
        company = Company.objects.filter(account_id=account_obj.id_account).first()
        if company and company.email_pc:
            email = company.email_pc

    else:
        return Response(
            {"code": 0, "message": "Invalid type_account"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not email:
        return Response(generic_response, status=status.HTTP_200_OK)

    # -----------------------
    # GENERAR NUEVA PASSWORD
    # -----------------------
    new_password = ''.join(
        secrets.choice(string.ascii_letters + string.digits)
        for _ in range(10)
    )

    # GUARDAR PASSWORD (TEXTO PLANO, COMO TU SISTEMA)
    account_obj.password = new_password
    account_obj.save()

    print("email:", email)

    # -----------------------
    # ENVIAR EMAIL
    # -----------------------
    send_mail(
        subject="Password recovery",
        message=(
            f"Your new password is:\n\n{new_password}\n\n"
            "Please log in and change it after accessing the platform."
        ),
        from_email="no-reply@tuapp.com",
        recipient_list=[email],
        fail_silently=True
    )

    return Response(generic_response, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_password(request):
    # ID del usuario autenticado
    id_account = request.user.id_account

    current_password = request.data.get('current_password')
    new_password = request.data.get('new_password')

    if not current_password or not new_password:
        return Response(
            {
                "code": 0,
                "message": "current_password and new_password are required"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # -----------------------
    # OBTENER ACCOUNT
    # -----------------------
    try:
        account = Account.objects.get(id_account=id_account)
    except Account.DoesNotExist:
        return Response(
            {"code": 0, "message": "Account not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    # -----------------------
    # VALIDAR PASSWORD ACTUAL
    # -----------------------
    if account.password != current_password:
        return Response(
            {"code": 0, "message": "Current password is incorrect"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # -----------------------
    # ACTUALIZAR PASSWORD
    # -----------------------
    account.password = new_password
    account.save(update_fields=['password'])

    return Response(
        {
            "code": 1,
            "message": "Password updated successfully"
        },
        status=status.HTTP_200_OK
    )

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_account(request):
    id_account = request.user.id_account

    try:
        account = Account.objects.get(id_account=id_account)
    except Account.DoesNotExist:
        return Response({"code": 0, "message": "Account not found"}, status=status.HTTP_404_NOT_FOUND)

    user_email = account.email

    # Eliminamos la cuenta (y toda la info en cascada)
    account.delete()

    # Enviamos correo de despedida
    send_mail(
        subject="We hope to see you again soon!",
        message=(
            f"Hello {user_email},\n\n"
            "Your account has been successfully deleted.\n\n"
            "We hope to see you back on our platform soon!\n\n"
            "Best regards,\n"
            "Professional Hospitality Connections"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user_email],
        fail_silently=True
    )

    return Response({"code": 1, "message": "Account and all related data deleted successfully"}, status=status.HTTP_200_OK)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def observations_admin(request):
    """
    Actualiza el campo observations_admin de un Account (solo admin).
    El id_account y el texto vienen en el body.
    """
    try:
        id_account = request.data.get('id_account')
        observations_admin = request.data.get('observations_admin')

        if not id_account:
            return Response(
                {"error": "id_account is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if observations_admin is None:
            return Response(
                {"error": "observations_admin is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        account = Account.objects.get(id_account=id_account)

        account.observations_admin = observations_admin
        account.save(update_fields=['observations_admin'])

        return Response({
            "message": "observations_admin updated successfully",
            "id_account": account.id_account,
            "observations_admin": account.observations_admin
        }, status=status.HTTP_200_OK)

    except Account.DoesNotExist:
        return Response(
            {"error": "Account not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    except Exception as e:
        return Response(
            {"error": "Unexpected server error", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )