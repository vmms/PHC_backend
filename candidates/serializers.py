from rest_framework import serializers
from .models import Candidate, CandidateHasSchedule
from addresses.models import Address
from education.models import Education
from addresses.serializers import AddressSerializer
from addresses.serializers import AddressPublicSerializer
from education.serializers import EducationSerializer, EducationPublicSerializer


class CandidateSerializer(serializers.ModelSerializer):
    address = AddressSerializer()
    education = EducationSerializer()
    account = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = Candidate
        fields = [
            'id_candidate', 'account', 'first_name', 'last_name', 'phone_number',
            'address', 'education', 'status', 'radius', 'adult', 'work_permission',
            'web_link', 'about', 'photo', 'desired_position', 'years_experience', 
            'last_position', 'last_company','email', 'job_type', 'employment_type', 
            'modality','salary', 'cvu'
        ]

    def create(self, validated_data):
        schedules = validated_data.pop('schedules', [])
        address_data = validated_data.pop('address', None)
        education_data = validated_data.pop('education', None)

        if address_data:
            address_instance = Address.objects.create(**address_data)
            validated_data['address'] = address_instance

        if education_data:
            education_instance = Education.objects.create(**education_data)
            validated_data['education'] = education_instance

        candidate = Candidate.objects.create(**validated_data)

        for schedule_id in schedules:
            CandidateHasSchedule.objects.create(schedule_id=schedule_id, candidate=candidate)

        return candidate


    def update(self, instance, validated_data):
        schedules = validated_data.pop('schedules', None)

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

        if schedules is not None:
            CandidateHasSchedule.objects.filter(candidate=instance).delete()
            for schedule_id in schedules:
                CandidateHasSchedule.objects.create(
                    schedule_id=schedule_id,
                    candidate=instance
                )

        return instance

    def format_response(self, instance=None):
        """
        Devuelve un diccionario con los campos que quieres exponer en la respuesta.
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

    def get_photo_url(self, obj):
        request = self.context.get('request')    
        if obj.photo and hasattr(obj.photo, 'url'):
            if request:
                return request.build_absolute_uri(obj.photo.url)
            # Si no hay request, regresa solo la URL relativa
            return obj.photo.url
        return None

class CandidatePublicSerializer(serializers.ModelSerializer):
    address = AddressPublicSerializer(read_only=True)
    education = EducationPublicSerializer(read_only=True)

    class Meta:
        model = Candidate
        fields = [
            'id_candidate',
            'first_name',
            'last_name',
            'desired_position',
            'years_experience',
            'last_position',
            'last_company',
            'job_type',
            'employment_type',
            'modality',
            'salary',
            'photo',
            'about',
            'address',
            'education'
        ]

class CandidateContactSerializer(serializers.ModelSerializer):
    address = AddressPublicSerializer(read_only=True)

    class Meta:
        model = Candidate
        fields = [
            'id_candidate',
            'first_name',
            'last_name',

            # ---- contacto ----
            'email',
            'phone_number',
            'address',
        ]