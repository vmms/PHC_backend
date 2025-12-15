from django.db import models

class JobApplication(models.Model):
    id_job_application = models.AutoField(primary_key=True)

    id_jobs = models.ForeignKey(
        'jobs.Job',
        on_delete=models.CASCADE,
        db_column='id_jobs'
    )

    id_candidate = models.ForeignKey(
        'candidates.Candidate',
        on_delete=models.CASCADE,
        db_column='id_candidate'
    )

    status = models.CharField(
        max_length=20,
        default='applied',
        choices=[
            ('applied', 'Applied'),
            ('review', 'Review'),
            ('rejected', 'Rejected'),
            ('accepted', 'Accepted'),
        ]
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'job_applications'
        managed = False
        unique_together = ('id_jobs', 'id_candidate')