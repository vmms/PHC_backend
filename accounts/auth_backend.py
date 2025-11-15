import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from accounts.models import Account


class AccountJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
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

        # Importante: debe tener el método is_authenticated (ya lo agregaste en Account)
        return (account, None)
