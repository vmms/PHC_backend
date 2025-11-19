from django.db import models
from accounts.models import Account
from addresses.models import Address
from education.models import Education

class Candidate(models.Model):
    id_candidate = models.AutoField(primary_key=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=45)
    last_name = models.CharField(max_length=45)
    phone_number = models.CharField(max_length=20)
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    education = models.ForeignKey(Education, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=[('active','active'),('inactive','inactive')], default='active')
    radius = models.IntegerField(null=True, blank=True)
    adult = models.BooleanField(default=True)
    work_permission = models.BooleanField(default=True)
    web_link = models.CharField(max_length=100, null=True, blank=True)
    about = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "candidate"
        managed = False

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
