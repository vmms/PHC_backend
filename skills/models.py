from django.db import models

class Skill(models.Model):
    id_skills = models.AutoField(primary_key=True)
    name = models.CharField(max_length=45)

    class Meta:
        db_table = 'skills'
        managed = False

    def __str__(self):
        return self.name
