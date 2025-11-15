from django.db import models

class Address(models.Model):
    id_address = models.AutoField(primary_key=True)
    street = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=45, null=True, blank=True)
    zip_code = models.CharField(max_length=10, null=True, blank=True)
    country = models.CharField(max_length=45, null=True, blank=True)

    class Meta:
        db_table = 'address'
        managed = False

    def __str__(self):
        return f"{self.street}, {self.state} ({self.zip_code})"
