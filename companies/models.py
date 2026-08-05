from django.db import models
from accounts.models import Account
from addresses.models import Address 

from django.utils.deconstruct import deconstructible
from django.conf import settings
import os

# @deconstructible
# class CompanyLogoPath:
#     def __call__(self, instance, filename):
#         # Obtener extensión del archivo original
#         ext = filename.split('.')[-1]
#         # Nombre fijo por empresa
#         filename = f'logo_company_{instance.id_company}.{ext}'
#         full_path = os.path.join('company_logos', filename)

#         # Borrar archivo existente si ya existe
#         absolute_path = os.path.join(settings.MEDIA_ROOT, full_path)
#         if os.path.exists(absolute_path):
#             os.remove(absolute_path)

#         return full_path

@deconstructible
class CompanyLogoPath:
    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        filename = f'logo_company_{instance.id_company}.{ext}'
        return os.path.join('media/companies/logos', filename)

class Company(models.Model):
    id_company = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    primary_contact = models.CharField(max_length=45)
    type_business = models.CharField(max_length=100)
    title_pc = models.CharField(max_length=45)
    phone_number_pc = models.CharField(max_length=20)
    email_pc = models.EmailField(max_length=100)
    secondary_contact = models.CharField(max_length=45, null=True, blank=True)
    title_sc = models.CharField(max_length=45, null=True, blank=True)
    phone_number_sc = models.CharField(max_length=20, null=True, blank=True)
    email_sc = models.EmailField(max_length=100, null=True, blank=True)
    description = models.CharField(max_length=500)
    link = models.CharField(max_length=100)
    logo = models.ImageField(upload_to=CompanyLogoPath(), null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cvu_downloads = models.IntegerField(default=0)
    profile_views = models.IntegerField(default=0)
    first_contact_applications = models.IntegerField(default=0)
    first_contact_search = models.IntegerField(default=0)
    subscription = models.CharField(max_length=50, null=True, blank=True)
    is_active = models.BooleanField(default=False)

    class Meta:
        db_table = "company"
        managed = False
        
    def __str__(self):
        return self.name