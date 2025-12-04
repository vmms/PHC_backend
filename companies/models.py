from django.db import models
from accounts.models import Account
from addresses.models import Address

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

    class Meta:
        db_table = "company"
        managed = False
        
    def __str__(self):
        return self.name