import requests
import xml.etree.ElementTree as ET
from django.utils import timezone
from datetime import timedelta
from datetime import datetime
from decimal import Decimal
from django.conf import settings

from companies.models import Company
from payments.models import Payment


CONVERGE_URL = settings.CONVERGE_XML_URL
PLAN_LABELS = {
    "basic": "Temp Only",
    "premium": "Full Access",
}


def sync_company_subscription_from_converge(account):
    company = Company.objects.get(account=account)

    # ============================================================
    # CUENTAS AUTORIZADAS SIN PAYMENT Y SIN CONVERGE
    # ============================================================
    if account_bypasses_subscription(account):
        return {
            "has_subscription": True,
            "plan": PLAN_LABELS.get(company.subscription),
            "is_active": True,
            "payment_status": "bypass",
            "amount": None,
            "next_payment_date": None,
            "client_since": company.created_at.date(),
            "recurring_id": None,
            "billing_cycle": None,
            "needs_payment_update": False,
            "message": "Subscription verification bypassed."
        }

    expiration_limit = timezone.now() - timedelta(minutes=15)

    Payment.objects.filter(
        company=company,
        status="pending",
        created_at__lt=expiration_limit
    ).update(
        status="expired"
    )

    payment = Payment.objects.filter(
        company=company,
        status="active",
        converge_recurring_id__isnull=False
    ).order_by("-created_at").first()

    if not payment:
        payment = Payment.objects.filter(
            company=company,
            status__in=["cancelled", "past_due", "failed", "declined", "pending"]
        ).order_by("-created_at").first()

    if not payment:
        return {
            "has_subscription": False,
            "plan": None,
            "is_active": False,
            "payment_status": None,
            "amount": None,
            "next_payment_date": None,
            "client_since": None,
            "billing_cycle": None,
            "needs_payment_update": False,
            "message": "No payment found."
        }

    if payment.status == "pending":
        return {
            "has_subscription": False,
            "plan": None,
            "is_active": False,
            "payment_status": "pending",
            "amount": str(payment.amount),
            "next_payment_date": None,
            "client_since": None,
            "billing_cycle": payment.billing_cycle,
            "needs_payment_update": False,
            "message": "Payment is pending confirmation."
        }

    if payment.status == "cancelled":
        return {
            "has_subscription": False,
            "plan": PLAN_LABELS.get(company.subscription),
            "is_active": bool(company.is_active),
            "payment_status": "paused",
            "amount": str(payment.amount),
            # "next_payment_date": payment.next_payment_date,
            "client_since": payment.created_at.date(),
            "billing_cycle": payment.billing_cycle,
            "needs_payment_update": False,
            "message": "Subscription cancelled."
        }

    xml = f"""
    <txn>
        <ssl_transaction_type>recurringquery</ssl_transaction_type>
        <ssl_account_id>{settings.CONVERGE_ACCOUNT_ID}</ssl_account_id>
        <ssl_user_id>{settings.CONVERGE_USER_ID}</ssl_user_id>
        <ssl_pin>{settings.CONVERGE_PIN}</ssl_pin>
        <ssl_recurring_id>{payment.converge_recurring_id}</ssl_recurring_id>
    </txn>
    """

    response = requests.post(
        CONVERGE_URL,
        data={"xmldata": xml},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30
    )

    print("CONVERGE RECURRING QUERY STATUS:", response.status_code)
    print("CONVERGE RECURRING QUERY RESPONSE:", response.text)

    data = parse_converge_xml(response.text)

    converge_error = False
    message = "Subscription synchronized with Converge."

    if response.status_code != 200:
        converge_error = True
        message = "Could not connect to Converge."

    if data.get("ssl_result") and data.get("ssl_result") != "0":
        converge_error = True
        message = (
            data.get("ssl_result_message")
            or data.get("ssl_error_message")
            or "Converge returned an error."
        )

    error_text = (
        data.get("ssl_result_message")
        or data.get("ssl_error_message")
        or ""
    ).lower()

    if any(word in error_text for word in ["declined", "failed", "expired", "invalid", "cancelled"]):
        converge_error = True
        message = error_text

    if not converge_error:
        if data.get("ssl_amount"):
            payment.amount = Decimal(data.get("ssl_amount"))

        if data.get("ssl_next_payment_date"):
            payment.next_payment_date = datetime.strptime(
                data.get("ssl_next_payment_date"),
                "%m/%d/%Y"
            ).date()

        if data.get("ssl_billing_cycle"):
            payment.billing_cycle = data.get("ssl_billing_cycle")

        payment.save()

    needs_payment_update = (
        converge_error
        or payment.status in ["past_due", "failed", "declined"]
        or not company.is_active
    )

    return {
        "has_subscription": True,
        "plan": PLAN_LABELS.get(company.subscription),
        "is_active": bool(company.is_active),
        "payment_status": payment.status,
        "amount": str(payment.amount),
        "next_payment_date": payment.next_payment_date,
        "client_since": payment.created_at.date(),
        "recurring_id": payment.converge_recurring_id,
        "billing_cycle": payment.billing_cycle,
        "needs_payment_update": needs_payment_update,
        "message": message
    }


def parse_converge_xml(raw):
    try:
        root = ET.fromstring(raw.strip())
    except ET.ParseError:
        return {}

    return {
        child.tag.strip(): child.text.strip()
        for child in root
        if child.tag and child.text
    }

    from django.utils import timezone


def company_has_valid_subscription(account):
    try:
        company = Company.objects.get(account=account)
    except Company.DoesNotExist:
        return False, None

    payment = Payment.objects.filter(
        company=company
    ).order_by("-created_at").first()

    if not payment:
        return False, None

    today = timezone.now().date()

    if payment.status == "active":
        return True, payment

    if payment.status == "cancelled":
        if payment.next_payment_date and payment.next_payment_date >= today:
            return True, payment

    return False, payment

def account_bypasses_subscription(account):
    return account.id_account in getattr(
        settings,
        "SUBSCRIPTION_BYPASS_ACCOUNT_IDS",
        []
    )