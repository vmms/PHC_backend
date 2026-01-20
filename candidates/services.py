import json

from django.db import transaction
from rest_framework.exceptions import ValidationError

from candidates.models import Candidate, CandidateHasSchedule
from candidates.serializers import CandidateSerializer
from schedulers.models import Scheduler
from accounts.models import Account
from addresses.models import Address
from education.models import Education

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
            phone_number="",
            emergency_contact_name="",
            emergency_contact_phone="",

            address=address,
            education=education,

            email=email,
            salary="",        # ⚠️ este campo NO es null en tu modelo
            servsafe="na",

            adult=True,
            work_permission=True,
            status="active",
        )

    return candidate