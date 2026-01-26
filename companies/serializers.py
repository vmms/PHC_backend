from rest_framework import serializers
from .models import Company
from addresses.models import Address
from addresses.serializers import AddressSerializer
from accounts.serializers import AccountAdminSerializer
from jobs.models import Job

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


class CompanyAdminSerializer(serializers.ModelSerializer):
    address = AddressSerializer(read_only=True)
    account = AccountAdminSerializer(read_only=True)
    total_jobs = serializers.SerializerMethodField()
    active_jobs = serializers.SerializerMethodField()
    preferred_contact = serializers.SerializerMethodField()
    
    created_at = serializers.DateTimeField(format="%m/%d/%Y", read_only=True)
    updated_at = serializers.DateTimeField(format="%m/%d/%Y", read_only=True)

    class Meta:
        model = Company
        fields = [
            'id_company',
            'name',
            'account',              # incluye observations_admin
            'address',
            'type_business',

            'primary_contact',
            'title_pc',
            'phone_number_pc',
            'email_pc',

            'secondary_contact',
            'title_sc',
            'phone_number_sc',
            'email_sc',

            'description',
            'link',
            'logo',

            'total_jobs',
            'active_jobs',

            'created_at',
            'updated_at',
            'profile_views',
            'cvu_downloads',
            'preferred_contact',
            'subscription',
            'is_active',
        ]
    
    def get_total_jobs(self, obj):
        return Job.objects.filter(company_id=obj.id_company).count()

    def get_active_jobs(self, obj):
        return Job.objects.filter(company_id=obj.id_company, is_active=True).count()
    
    def get_preferred_contact(self, obj):
        # Comparar cuál es mayor
        if obj.first_contact_applications >= obj.first_contact_search:
            return "Applications"
        else:
            return "Search"