import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from accounts.models import Account
from rest_framework_simplejwt.settings import api_settings


class AccountJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]

        # 🔥 OBTENER LA MISMA LLAVE QUE USA SIMPLEJWT
        signing_key = api_settings.SIGNING_KEY

        try:
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=[api_settings.ALGORITHM]
            )
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token expirado')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Token inválido')

        id_account = payload.get('id_account')
        if not id_account:
            raise AuthenticationFailed('Token inválido: sin id_account')

        try:
            account = Account.objects.get(id_account=id_account)
        except Account.DoesNotExist:
            raise AuthenticationFailed('Cuenta no encontrada')

        return (account, None)
