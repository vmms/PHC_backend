from rest_framework import serializers
from .models import Company
from addresses.models import Address
from addresses.serializers import AddressSerializer

class CompanySerializer(serializers.ModelSerializer):
    address = AddressSerializer()
    account = serializers.PrimaryKeyRelatedField(read_only=True)  # no enviado por cliente

    class Meta:
        model = Company
        fields = [
            'id_company', 'name', 'account', 'address', 'type_business',
            'primary_contact', 'title_pc', 'phone_number_pc', 'email_pc',
            'secondary_contact', 'title_sc', 'phone_number_sc', 'email_sc',
            'description', 'link', 'logo'
        ]

    def create(self, validated_data):
        address_data = validated_data.pop('address')
        address = Address.objects.create(**address_data)
        company = Company.objects.create(address=address, **validated_data)
        return company


    def update(self, instance, validated_data):
        address_data = validated_data.pop('address')

        # Update address
        for key, value in address_data.items():
            setattr(instance.address, key, value)
        instance.address.save()

        # Update company
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()

        return instance

    def get_logo_url(self, obj):
        request = self.context.get('request')
        if obj.logo and hasattr(obj.logo, 'url'):
            # Construye la URL absoluta usando el request
            return request.build_absolute_uri(obj.logo.url)
        return None
