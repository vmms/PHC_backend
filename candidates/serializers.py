from rest_framework import serializers
from .models import Candidate
from addresses.models import Address
from education.models import Education
from addresses.serializers import AddressSerializer
from education.serializers import EducationSerializer

class CandidateSerializer(serializers.ModelSerializer):
    address = AddressSerializer()
    education = EducationSerializer()
    account = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Candidate
        fields = [
            'id_candidate', 'account', 'first_name', 'last_name', 'phone_number',
            'address', 'education', 'status', 'radius', 'adult', 'work_permission',
            'web_link', 'about'
        ]

    def create(self, validated_data):
        address_data = validated_data.pop('address')
        education_data = validated_data.pop('education')
        address = Address.objects.create(**address_data)
        education = Education.objects.create(**education_data)
        candidate = Candidate.objects.create(address=address, education=education, **validated_data)
        return candidate

    def update(self, instance, validated_data):
        address_data = validated_data.pop('address', None)
        education_data = validated_data.pop('education', None)

        if address_data:
            for key, value in address_data.items():
                setattr(instance.address, key, value)
            instance.address.save()

        if education_data:
            for key, value in education_data.items():
                setattr(instance.education, key, value)
            instance.education.save()

        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance
    
    def format_response(self, instance=None):
        """
        Devuelve un diccionario con los campos que quieres exponer en la respuesta.
        Si no se pasa instance, toma self.instance (lo que usualmente se guarda después de save()).
        """
        if instance is None:
            instance = self.instance

        if not instance:
            return {}

        return {
            "message": "Candidate creado correctamente",
            "candidate": {
                "id_candidate": instance.id_candidate,
                "first_name": instance.first_name,
                "last_name": instance.last_name,
                "status": instance.status,
            }
        }

