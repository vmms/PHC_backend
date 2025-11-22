from django.db import models

class Scheduler(models.Model):
    id_schedule = models.AutoField(primary_key=True)
    day = models.CharField(max_length=20, null=True, blank=True)
    time_start = models.TimeField(null=True, blank=True)
    time_finish = models.TimeField(null=True, blank=True)

    class Meta:
        db_table = 'schedule'
        managed = False

    def __str__(self):
        return f"{self.day} {self.start_time}-{self.end_time}"
