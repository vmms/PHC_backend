from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from jobs.models import Job
from jobApplication.models import JobApplication

def get_jobs_admin_stats():
    now = timezone.now()
    start_week = now - timedelta(days=7)
    start_month = now.replace(day=1)

    # -----------------------
    # TOTALES
    # -----------------------
    total_jobs = Job.objects.count()
    new_this_week = Job.objects.filter(created_at__gte=start_week).count()
    new_this_month = Job.objects.filter(created_at__gte=start_month).count()

    # -----------------------
    # EMPLOYMENT TYPE
    # -----------------------
    full_time_jobs = Job.objects.filter(employment_type__iexact='full_time').count()
    part_time_jobs = Job.objects.filter(employment_type__iexact='part_time').count()

    # -----------------------
    # POPULARITY / APPLICATIONS
    # -----------------------
    jobs_with_applications = Job.objects.annotate(
        total_applications=Count('jobapplication')
    )

    top_3_most_apps = jobs_with_applications.order_by('-total_applications', 'title')[:3]
    top_3_least_apps = jobs_with_applications.order_by('total_applications', 'title')[:3]

    def serialize_job(j):
        return {
            "id_jobs": j.id_jobs,
            "title": j.title,
            "total_applications": getattr(j, 'total_applications', 0)
        }

    return {
        "totals": {
            "total_jobs": total_jobs,
            "new_this_week": new_this_week,
            "new_this_month": new_this_month
        },
        "employment_type": {
            "full_time": full_time_jobs,
            "part_time": part_time_jobs
        },
        "applications": {
            "top_3_most_applications": [serialize_job(j) for j in top_3_most_apps],
            "top_3_least_applications": [serialize_job(j) for j in top_3_least_apps]
        }
    }