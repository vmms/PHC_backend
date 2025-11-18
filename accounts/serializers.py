from rest_framework import serializers
from .models import Account
from django.contrib.auth.hashers import check_password

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'

class AccountLoginSerializer(serializers.Serializer):
    user = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = data.get('user')
        password = data.get('password')

        try:
            account = Account.objects.get(user=user)
        except Account.DoesNotExist:
            raise serializers.ValidationError("Usuario no encontrado.")

        # Si tus contraseñas están en texto plano:
        if account.password != password:
            raise serializers.ValidationError("Contraseña incorrecta.")

        # Si estuvieran cifradas con hash:
        # if not check_password(password, account.password):
        #     raise serializers.ValidationError("Contraseña incorrecta.")

        data['account'] = account
        return data

class TokenLoginRequestSerializer(serializers.Serializer):
    user = serializers.CharField()
    password = serializers.CharField()

    class Meta:
        ref_name = "TokenLoginRequest"


class TokenLoginResponseSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    refresh = serializers.CharField()
    access = serializers.CharField()
    id_account = serializers.IntegerField()
    user = serializers.CharField()
    subscription = serializers.CharField()

    class Meta:
        ref_name = "TokenLoginResponse"

class ErrorResponseSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()

    class Meta:
        ref_name = "ErrorResponse"


