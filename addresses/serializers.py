from rest_framework import serializers
from .models import Address

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            'id_address', 
            'street', 
            'state', 
            'city', 
            'zip_code', 
            'country',
            'latitude',
            'longitude',
            'geocoded_at',
        ]

        read_only_fields = [
            'latitude',
            'longitude',
            'geocoded_at',
        ]


class AddressPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            'city',
            'state',
            'country'
        ]