from django.db import transaction
from rest_framework.exceptions import ValidationError

from accounts.models import Account
from companies.models import Company
from addresses.models import Address
from jobs.models import Job

from datetime import timedelta
from django.utils import timezone
from django.db.models import Count


def create_company_internal(*, id_account, email):
    try:
        account = Account.objects.get(id_account=id_account)
    except Account.DoesNotExist:
        raise ValidationError("Account not found")

    with transaction.atomic():

        # =============================
        # 1️⃣ CREAR ADDRESS
        # =============================
        address = Address.objects.create()

        # =============================
        # 2️⃣ CREAR COMPANY
        # =============================
        company = Company.objects.create(
            account=account,
            address=address,

            name="",
            primary_contact="",
            type_business="",
            title_pc="",
            phone_number_pc="",
            email_pc=email,

            description="",
            link="",
        )

    return company

def get_company_admin_stats():
    now = timezone.now()
    start_week = now - timedelta(days=7)
    start_month = now.replace(day=1)

    # -----------------------
    # TOTALES
    # -----------------------
    total_companies = Company.objects.count()

    new_this_week = Company.objects.filter(
        created_at__gte=start_week
    ).count()

    new_this_month = Company.objects.filter(
        created_at__gte=start_month
    ).count()

    # -----------------------
    # SUBSCRIPTION
    # -----------------------
    basic_companies = Company.objects.filter(subscription='basic').count()
    premium_companies = Company.objects.filter(subscription='premium').count()

    # -----------------------
    # JOBS PER COMPANY (solo top/least, sin totales)
    # -----------------------
    companies_with_jobs = Company.objects.annotate(
        jobs_count=Count('job')
    )

    top_3_most_jobs = companies_with_jobs.order_by(
        '-jobs_count',
        'name'
    )[:3]

    top_3_least_jobs = companies_with_jobs.order_by(
        'jobs_count',
        'name'
    )[:3]

    def serialize_company(c):
        return {
            "id_company": c.id_company,
            "name": c.name,
            "jobs_count": c.jobs_count
        }

    return {
        "totals": {
            "total": total_companies,
            "new_this_week": new_this_week,
            "new_this_month": new_this_month,
        },
        "subscription": {
            "basic": basic_companies,
            "premium": premium_companies,
        },
        "top_3_most_jobs": [
            serialize_company(c) for c in top_3_most_jobs
        ],
        "top_3_least_jobs": [
            serialize_company(c) for c in top_3_least_jobs
        ]
    }
