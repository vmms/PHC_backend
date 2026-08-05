import json

from django.db import transaction
from rest_framework.exceptions import ValidationError

from candidates.models import Candidate, CandidateHasSchedule
from candidates.serializers import CandidateSerializer
from schedulers.models import Scheduler
from accounts.models import Account
from addresses.models import Address
from education.models import Education

from datetime import timedelta
from django.utils import timezone
from django.db.models import Count
from jobApplication.models import JobApplication

from datetime import datetime

def create_candidate_internal(*, id_account, email):

    try:
        account = Account.objects.get(id_account=id_account)
    except Account.DoesNotExist:
        raise ValidationError("Account not found")

    with transaction.atomic():

        # =============================
        # 1️⃣ CREAR ADDRESS VACÍO
        # =============================
        address = Address.objects.create()

        # =============================
        # 2️⃣ CREAR EDUCATION VACÍO
        # =============================
        education = Education.objects.create()

        # =============================
        # 3️⃣ CREAR CANDIDATE
        # =============================
        candidate = Candidate.objects.create(
            account=account,

            first_name="",
            last_name="",

            # AHORA SE GUARDA EL TELÉFONO
            # phone_number=phone_number,

            emergency_contact_name="",
            emergency_contact_phone="",

            address=address,
            education=education,

            email=email,
            salary="",
            servsafe=None,

            adult=None,
            work_permission=None,
            status="active",
        )

    return candidate


def get_candidate_admin_stats():
    now = timezone.now()
    start_week = now - timedelta(days=7)
    start_month = now.replace(day=1)

    # -----------------------
    # TOTALES
    # -----------------------
    total_candidates = Candidate.objects.count()

    new_this_week = Candidate.objects.filter(
        created_at__gte=start_week
    ).count()

    new_this_month = Candidate.objects.filter(
        created_at__gte=start_month
    ).count()

    # -----------------------
    # JOB TYPE
    # -----------------------
    permanent_candidates = Candidate.objects.filter(
        job_type__iexact='permanent'
    ).count()

    temporary_candidates = Candidate.objects.filter(
        job_type__iexact='temporary'
    ).count()

    # -----------------------
    # JOB APPLICATIONS
    # -----------------------
    candidates_with_apps = Candidate.objects.annotate(
        job_applications_count=Count('jobapplication')
    )

    top_3_most = candidates_with_apps.order_by(
        '-job_applications_count',
        'first_name'
    )[:3]

    top_3_least = candidates_with_apps.order_by(
        'job_applications_count',
        'first_name'
    )[:3]

    top_desired_positions = (
        Candidate.objects
        .values('desired_position')
        .annotate(position_count=Count('desired_position'))
        .exclude(desired_position__isnull=True)
        .exclude(desired_position__exact='')
        .order_by('-position_count')[:3]
    )

    def serialize_candidate(c):
        return {
            "id_candidate": c.id_candidate,
            "first_name": c.first_name,
            "last_name": c.last_name,
            "job_applications_count": c.job_applications_count
        }

    return {
        "totals": {
            "total": total_candidates,
            "new_this_week": new_this_week,
            "new_this_month": new_this_month,
        },
        "job_type": {
            "permanent": permanent_candidates,
            "temporary": temporary_candidates
        },
        "top_3_most_applications": [
            serialize_candidate(c) for c in top_3_most
        ],
        "top_3_least_applications": [
            serialize_candidate(c) for c in top_3_least
        ],
        "top_3_desired_positions": [
            {
                "desired_position": p["desired_position"],
                "count": p["position_count"]
            }
            for p in top_desired_positions
        ]
    }

def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str[:10], "%Y-%m-%d").date()
    except ValueError:
        return None

def parse_time(time_str):
    if not time_str:
        return None
    try:
        return datetime.strptime(time_str, "%H:%M:%S").time()
    except ValueError:
        # por si viene solo HH:MM
        return datetime.strptime(time_str, "%H:%M").time()

def hours_intersect(start1, end1, start2, end2):
    """Verifica si dos rangos de horas se intersectan"""
    return max(start1, start2) < min(end1, end2)