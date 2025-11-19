from django.db import models

class Education(models.Model):
    id_education = models.AutoField(primary_key=True)
    country = models.CharField(max_length=45)
    education = models.CharField(max_length=100)
    graduation_year = models.CharField(max_length=10)
    institute = models.CharField(max_length=100)

    class Meta:
        db_table = 'education'
        managed = False

    def __str__(self):
        return f"{self.education} - {self.institute}"
