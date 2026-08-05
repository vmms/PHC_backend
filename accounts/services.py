import json

from django.db import transaction
from rest_framework.exceptions import ValidationError

from candidates.models import Candidate, CandidateHasSchedule
from candidates.serializers import CandidateSerializer
from schedulers.models import Scheduler

def create_candidate_internal(*, id_account, email):
    try:
        account = Account.objects.get(id_account=id_account)
    except Account.DoesNotExist:
        raise ValidationError("Account not found")

    # =============================
    # DATA GENÉRICA (MINIMA)
    # =============================
    data = {
        "first_name": "",
        "last_name": "",
        "phone_number": "",
        "email": email,
        "schedule": []
    }

    schedule_payload = data.pop("schedule", [])

    # =============================
    # MISMA LÓGICA DE create_candidate
    # =============================
    with transaction.atomic():

        print("create_candidate_internal NUEVA VERSION")
        print("adult:", None)
        print("work_permission:", None)
        print("servsafe:", None)

        candidate = Candidate.objects.create(
            account=account,
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            phone_number=data.get("phone_number"),
            emergency_contact_name=None,
            emergency_contact_phone=None,
            address_id=None,
            education_id=None,
            desired_position=None,
            years_experience=None,
            last_position=None,
            last_company=None,
            email=data.get("email"),
            job_type=None,
            employment_type=None,
            modality=None,
            salary=None,
            radius=None,
            adult=None,
            work_permission=None,
            web_link=None,
            about=None,
            photo=None,
            cvu=None,
            servsafe=None,
            status="active"
        )

        # ============================================
        # SCHEDULES (MISMO BLOQUE, solo que vacío)
        # ============================================
        for sch in schedule_payload:

            if "multiple" in sch and sch["multiple"]:
                for item in sch["multiple"]:
                    scheduler = Scheduler.objects.create(
                        type="multiple",
                        day=None,
                        date_start=item.get("date_start"),
                        date_end=None,
                        time_start=item.get("time_start"),
                        time_finish=item.get("time_end")
                    )
                    CandidateHasSchedule.objects.create(
                        schedule=scheduler,
                        candidate=candidate
                    )

            elif "range" in sch and sch["range"]:
                for item in sch["range"]:
                    scheduler = Scheduler.objects.create(
                        type="range",
                        day=None,
                        date_start=item.get("date_start"),
                        date_end=item.get("date_end"),
                        time_start=item.get("time_start"),
                        time_finish=item.get("time_end")
                    )
                    CandidateHasSchedule.objects.create(
                        schedule=scheduler,
                        candidate=candidate
                    )

            elif "permanent" in sch and sch["permanent"]:
                perm = sch["permanent"]
                start_date = perm.get("start_date")
                for day_item in perm.get("days", []):
                    scheduler = Scheduler.objects.create(
                        type="permanent",
                        day=day_item.get("day"),
                        date_start=start_date,
                        date_end=None,
                        time_start=day_item.get("time_start"),
                        time_finish=day_item.get("time_end")
                    )
                    CandidateHasSchedule.objects.create(
                        schedule=scheduler,
                        candidate=candidate
                    )

    return candidate