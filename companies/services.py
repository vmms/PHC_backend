from django.db import transaction
from rest_framework.exceptions import ValidationError

from accounts.models import Account
from companies.models import Company
from addresses.models import Address

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
