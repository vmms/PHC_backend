from django.db import models

class Scheduler(models.Model):
    id_schedule = models.AutoField(primary_key=True)
    
    type = models.CharField(max_length=10, default='multiple')  # 'multiple', 'range', 'permanent'
    day = models.CharField(max_length=3, null=True, blank=True) # para 'permanent' o 'multiple'
    
    date_start = models.DateField(null=True, blank=True)         # para 'range' o 'permanent'
    date_end = models.DateField(null=True, blank=True)           # para 'range'

    time_start = models.TimeField()
    time_finish = models.TimeField()

    class Meta:
        db_table = 'schedule'
        managed = False

    def __str__(self):
        return f"{self.type} {self.day or ''}: {self.time_start}-{self.time_finish}"