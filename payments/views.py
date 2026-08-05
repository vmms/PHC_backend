import requests
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.conf import settings
from django.shortcuts import redirect
from django.utils import timezone
import uuid

from decimal import Decimal, ROUND_HALF_UP
from dateutil.relativedelta import relativedelta

from companies.models import Company
from payments.models import Payment

PLAN_LABELS = {
    "basic": "Temp Only",
    "premium": "Full Access"
}

def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

    if x_forwarded_for:
        # Si hay varias IPs, la primera es la del cliente original
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")

    return ip

def get_public_outbound_ip():
    try:
        r = requests.get(
            "https://www.convergepay.com/hosted-payments/myip",
            timeout=10
        )
        return r.text.strip()
    except Exception as e:
        return f"Error obteniendo IP pública: {str(e)}"

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def Process_payment(request):

    plan = request.data.get("subscription")
    print('plan:',plan)

    public_ip = get_public_outbound_ip()
    print("IP pública de salida hacia Converge:", public_ip)
    

    if plan == "temp":
        amount = Decimal("150.00")
        company_subscription = "basic"
    elif plan == "full":
        amount = Decimal("250.00")
        company_subscription = "premium"
    else:
        return Response({"error": "Invalid plan"}, status=400)

    try:
        company = Company.objects.get(account_id=request.user.id_account)
    except Company.DoesNotExist:
        return Response({"error": "Company not found for this account"}, status=404)
    
    # ============================================================
    # CUENTA SIN PAGO
    # No crea Payment y no solicita token a Converge.
    # ============================================================
    if account_bypasses_subscription(request.user):
        company.subscription = company_subscription
        company.is_active = True

        company.save(
            update_fields=[
                "subscription",
                "is_active",
                "updated_at"
            ]
        )

        return Response(
            {
                "message": (
                    "Subscription activated without payment "
                    "for authorized account."
                ),
                "subscription": company.subscription,
                "plan": PLAN_LABELS.get(
                    company.subscription
                ),
                "payment_status": "bypass",
                "amount": None,
                "reference": None,
                "token": None,
                "post_url": None
            },
            status=200
        )

    reference = f"INV-{timezone.now():%Y%m%d%H%M%S}-{request.user.id_account:04d}"

    next_payment_date = timezone.now().date() + relativedelta(months=1)

    payment = Payment.objects.create(
        company=company,
        invoice_number=reference,
        amount=amount,
        status="pending",
        billing_cycle="MONTHLY",
        next_payment_date=next_payment_date,
    )

    payload = {
        "ssl_transaction_type": "ccaddrecurring",
        "ssl_account_id": settings.CONVERGE_ACCOUNT_ID, 
        "ssl_user_id": settings.CONVERGE_USER_ID, 
        "ssl_pin": settings.CONVERGE_PIN,

        "ssl_amount": amount,
        "ssl_invoice_number": reference,
        "ssl_customer_code": str(request.user.id_account),
        "ssl_description": f"Subscription plan {plan}",

        "ssl_next_payment_date": next_payment_date.strftime("%m/%d/%Y"),
        "ssl_billing_cycle": "MONTHLY",
    
        "ssl_result_format": "HTML",
        "ssl_receipt_link_url": "https://www.professionalhospitalityconnections.com/converge-response/", #"https://ruthe-unretributive-superscientifically.ngrok-free.dev/converge-response/"
        "ssl_error_url": "https://www.professionalhospitalityconnections.com/converge-response/",#"https://ruthe-unretributive-superscientifically.ngrok-free.dev/converge-response/"
    }

    try:
        response = requests.post(
            settings.CONVERGE_HPP_URL,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30
        )

        print("STATUS:", response.status_code)
        print("RESPONSE:", response.text)
        print("PAYLOAD:", payload)

        if response.status_code != 200:
            payment.status = "failed"
            payment.save()

            return Response({
                "error": "Gateway error",
                "details": response.text
            }, status=500)

        token = response.text.strip()

        if not token:
            payment.status = "failed"
            payment.save()

            return Response({
                "error": "Token not generated",
                "gateway_response": response.text
            }, status=500)

        return Response({
            "token": token,
            "reference": reference,
            "post_url": settings.CONVERGE_POST_URL,
        }, status=200)

    except requests.exceptions.RequestException as e:
        payment.status = "failed"
        payment.save()

        return Response({
            "error": "Payment service unavailable",
            "details": str(e)
        }, status=500)


@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def converge_response(request):
    print("=== CONVERGE RESPONSE ===")
    print("Method:", request.method)

    data = request.data if request.method == "POST" else request.query_params

    print("CONVERGE DATA:", data)
    print("CONVERGE QUERY:", request.query_params)

    invoice_number = data.get("ssl_invoice_number")
    ssl_result = data.get("ssl_result")
    ssl_result_message = data.get("ssl_result_message")
    ssl_recurring_id = data.get("ssl_recurring_id")

    if not invoice_number:
        return Response({"error": "Missing invoice number"}, status=400)

    # ============================================================
    # CASO 1: Pago único de upgrade basic -> premium
    # Invoice: UPG-YYYYMMDDHHMMSS-0005
    # ============================================================
    if invoice_number.startswith("UPG-"):

        if ssl_result != "0":
            return Response({
                "message": "Upgrade payment failed",
                "invoice_number": invoice_number,
                "result": ssl_result,
                "result_message": ssl_result_message
            }, status=400)

        customer_code = data.get("ssl_customer_code")

        if not customer_code:
            return Response({
                "error": "Missing customer code for upgrade",
                "invoice_number": invoice_number
            }, status=400)

        try:
            company = Company.objects.get(account_id=int(customer_code))
        except Company.DoesNotExist:
            return Response({
                "error": "Company not found for upgrade",
                "customer_code": customer_code
            }, status=404)

        try:
            active_payment = Payment.objects.get(
                company=company,
                status="active"
            )
        except Payment.DoesNotExist:
            return Response({
                "error": "Active payment not found for upgrade",
                "company_id": company.id_company
            }, status=404)

        if not active_payment.converge_recurring_id:
            return Response({
                "error": "Missing recurring ID on active payment",
                "payment_id": active_payment.id_payment
            }, status=400)

        update_response = update_recurring_amount_in_converge(
            recurring_id=active_payment.converge_recurring_id,
            amount=Decimal("250.00"),
            next_payment_date=active_payment.next_payment_date
        )

        if not update_response["success"]:
            return Response({
                "error": "Upgrade payment was approved, but recurring update failed",
                "invoice_number": invoice_number,
                "recurring_id": active_payment.converge_recurring_id,
                "details": update_response["raw"]
            }, status=500)

        active_payment.amount = Decimal("250.00")
        active_payment.save()

        company.subscription = "premium"
        company.is_active = 1
        company.save()

        return Response({
            "message": "Upgrade completed",
            "invoice_number": invoice_number,
            "amount_charged": data.get("ssl_amount"),
            "recurring_id": active_payment.converge_recurring_id,
            "new_subscription": "premium"
        }, status=200)

        # return redirect(
        #     "https://www.professionalhospitalityconnections.com/companies-profile/" #"https://ruthe-unretributive-superscientifically.ngrok-free.dev/companies-profile"
        # )

    # ============================================================
    # CASO 2: Alta normal de suscripción recurrente
    # Invoice: INV-YYYYMMDDHHMMSS-0005
    # ============================================================
    try:
        payment = Payment.objects.get(invoice_number=invoice_number)
    except Payment.DoesNotExist:
        return Response({
            "error": "Payment not found",
            "invoice_number": invoice_number
        }, status=404)

    payment.converge_result = ssl_result
    payment.converge_result_message = ssl_result_message
    payment.converge_recurring_id = ssl_recurring_id

    if ssl_result == "0":

        old_active_payments = Payment.objects.filter(
            company=payment.company,
            status="active"
        ).exclude(
            id_payment=payment.id_payment
        )

        for old_payment in old_active_payments:
            if old_payment.converge_recurring_id:
                cancel_response = cancel_recurring_in_converge(
                    old_payment.converge_recurring_id
                )

                if (
                    cancel_response.status_code == 200
                    and "<ssl_result>0</ssl_result>" in cancel_response.text
                ):
                    old_payment.status = "replaced"
                    old_payment.cancelled_at = timezone.now()
                    old_payment.save()
                else:
                    payment.status = "failed"
                    payment.save()

                    return Response({
                        "error": "New subscription was created, but old recurring could not be cancelled",
                        "old_recurring_id": old_payment.converge_recurring_id,
                        "converge_response": cancel_response.text
                    }, status=500)

            else:
                old_payment.status = "replaced"
                old_payment.cancelled_at = timezone.now()
                old_payment.save()

        Payment.objects.filter(
            company=payment.company,
            status="pending"
        ).exclude(
            id_payment=payment.id_payment
        ).update(
            status="expired"
        )

        payment.status = "active"
        payment.started_at = timezone.now()
        payment.save()

        company = payment.company

        if payment.amount == Decimal("150.00"):
            company.subscription = "basic"
        elif payment.amount == Decimal("250.00"):
            company.subscription = "premium"

        company.is_active = 1
        company.save()

        return Response({
            "message": "Subscription activated",
            "invoice_number": invoice_number,
            "recurring_id": ssl_recurring_id
        }, status=200)

        # return redirect(
        #     "https://www.professionalhospitalityconnections.com/companies-profile/" #https://ruthe-unretributive-superscientifically.ngrok-free.dev/companies-profile"
        # )

    payment.status = "failed"
    payment.save()

    return Response({
        "message": "Payment failed",
        "invoice_number": invoice_number,
        "result": ssl_result,
        "result_message": ssl_result_message
    }, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_subscription(request):
    try:
        company = Company.objects.get(account_id=request.user.id_account)
    except Company.DoesNotExist:
        return Response({"error": "Company not found"}, status=404)

    try:
        payment = Payment.objects.get(company=company, status="active")
    except Payment.DoesNotExist:
        return Response({"error": "No active subscription found"}, status=404)

    if not payment.converge_recurring_id:
        return Response({"error": "Missing recurring ID"}, status=400)

    xml = f"""
    <txn>
        <ssl_transaction_type>ccdeleterecurring</ssl_transaction_type>
        <ssl_account_id>{settings.CONVERGE_ACCOUNT_ID}</ssl_account_id>
        <ssl_user_id>{settings.CONVERGE_USER_ID}</ssl_user_id>
        <ssl_pin>{settings.CONVERGE_PIN}</ssl_pin>
        <ssl_recurring_id>{payment.converge_recurring_id}</ssl_recurring_id>
    </txn>
    """

    response = requests.post(
        settings.CONVERGE_XML_URL,
        data={"xmldata": xml},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30
    )

    print("CANCEL STATUS:", response.status_code)
    print("CANCEL RESPONSE:", response.text)

    if response.status_code != 200:
        return Response({"error": "Converge error", "details": response.text}, status=500)

    if "<ssl_result>0</ssl_result>" in response.text:
        payment.status = "cancelled"
        payment.cancelled_at = timezone.now()
        payment.save()

        # company.is_active = 0
        company.save()

        return Response({
            "message": "Subscription cancelled successfully.",
            "cancelled_at": payment.cancelled_at
        })

    return Response({
        "error": "Cancellation rejected by Converge",
        "details": response.text
    }, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_subscriptions(request):
    today = timezone.now().date()

    expired = Payment.objects.filter(
        status="cancellation_pending",
        next_payment_date__lte=today
    )

    count = 0

    for payment in expired:
        payment.status = "cancelled"
        payment.save()

        company = payment.company
        company.is_active = 0
        company.save()

        count += 1

    try:
        company = Company.objects.get(account_id=request.user.id_account)
    except Company.DoesNotExist:
        return Response({
            "message": "Subscriptions synchronized",
            "cancelled_subscriptions": count,
            "subscription": None
        }, status=404)
    
    # No busca Payment para las cuentas autorizadas.
    if account_bypasses_subscription(request.user):
        return Response(
            {
                "message": (
                    "Subscriptions synchronized"
                ),
                "cancelled_subscriptions": count,
                "subscription": {
                    "company_id": company.id_company,
                    "plan": PLAN_LABELS.get(
                        company.subscription
                    ),
                    "is_active": True,
                    "company_is_active": True,
                    "payment_status": "bypass",
                    "amount": None,
                    "next_payment_date": None,
                    "client_since": (
                        company.created_at.date()
                    ),
                    "recurring_id": None
                }
            },
            status=200
        )

    payment = Payment.objects.filter(
        company=company
    ).order_by("-created_at").first()

    subscription_active = (
        payment is not None
        and payment.status == "active"
        and company.is_active == 1
    )

    return Response({
        "message": "Subscriptions synchronized",
        "cancelled_subscriptions": count,
        "subscription": {
            "company_id": company.id_company,
            "plan": PLAN_LABELS.get(company.subscription),
            "is_active": subscription_active,
            "company_is_active": bool(company.is_active),
            "payment_status": payment.status if payment else None,
            "amount": str(payment.amount) if payment else None,
            "next_payment_date": payment.next_payment_date if payment else None,
            "client_since": payment.created_at.date() if payment else None,
            "recurring_id": payment.converge_recurring_id if payment else None
        }
    }, status=200)


def cancel_recurring_in_converge(recurring_id):

    xml = f"""
    <txn>
        <ssl_transaction_type>ccdeleterecurring</ssl_transaction_type>
        <ssl_account_id>{settings.CONVERGE_ACCOUNT_ID}</ssl_account_id>
        <ssl_user_id>{settings.CONVERGE_USER_ID}</ssl_user_id>
        <ssl_pin>{settings.CONVERGE_PIN}</ssl_pin>
        <ssl_recurring_id>{recurring_id}</ssl_recurring_id>
    </txn>
    """

    response = requests.post(
        settings.CONVERGE_XML_URL,
        data={"xmldata": xml},
        headers={
            "Content-Type":
            "application/x-www-form-urlencoded"
        },
        timeout=30
    )

    return response

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_plan(request):
    print('Cambio de plan')
    try:
        company = Company.objects.get(account_id=request.user.id_account)
    except Company.DoesNotExist:
        return Response({"error": "Company not found"}, status=404)

    current_subscription = company.subscription
    
    print('current_subscription:',current_subscription)


    if current_subscription == "basic":
        new_amount = Decimal("250.00")
        new_subscription = "premium"
    elif current_subscription == "premium":
        new_amount = Decimal("150.00")
        new_subscription = "basic"
    else:
        return Response({"error": "Invalid current subscription"}, status=400)

    try:
        company = Company.objects.get(account_id=request.user.id_account)
    except Company.DoesNotExist:
        return Response({"error": "Company not found"}, status=404)

    # ============================================================
    # CAMBIO LOCAL PARA CUENTAS AUTORIZADAS
    # No busca Payment y no llama a Converge.
    # ============================================================
    if account_bypasses_subscription(request.user):
        company.subscription = new_subscription
        company.is_active = True

        company.save(
            update_fields=[
                "subscription",
                "is_active",
                "updated_at"
            ]
        )

        return Response(
            {
                "message": (
                    "Plan changed locally for "
                    "authorized account."
                ),
                "current_subscription": (
                    current_subscription
                ),
                "new_subscription": new_subscription,
                "plan": PLAN_LABELS.get(
                    new_subscription
                ),
                "new_amount": None,
                "payment_status": "bypass",
                "recurring_id": None,
                "converge_updated": False
            },
            status=200
        )
        
    try:
        active_payment = Payment.objects.get(
            company=company,
            status="active"
        )
    except Payment.DoesNotExist:
        return Response({"error": "No active subscription found"}, status=404)

    current_amount = active_payment.amount

    if current_amount == new_amount:
        return Response({
            "message": "Company already has this plan",
            "subscription": current_subscription
        }, status=400)

    if not active_payment.converge_recurring_id:
        return Response({"error": "Missing recurring ID"}, status=400)

    # premium -> basic: no refund, update recurring only
    if current_amount > new_amount:
        update_response = update_recurring_amount_in_converge(
            recurring_id=active_payment.converge_recurring_id,
            amount=new_amount,
            next_payment_date=active_payment.next_payment_date
        )

        if not update_response["success"]:
            return Response({
                "error": "Could not update recurring payment in Converge",
                "details": update_response["raw"]
            }, status=500)

        active_payment.amount = new_amount
        active_payment.save()

        company.subscription = new_subscription
        company.save()

        return Response({
            "message": "Plan changed successfully",
            "new_subscription": new_subscription,
            "new_amount": str(new_amount),
            "recurring_id": active_payment.converge_recurring_id
        }, status=200)

    # basic -> premium: charge prorated difference first
    today = timezone.now().date()
    next_payment_date = active_payment.next_payment_date

    if not next_payment_date or next_payment_date <= today:
        days_left = 0
    else:
        days_left = (next_payment_date - today).days

    monthly_difference = new_amount - current_amount

    prorated_amount = (
        monthly_difference * Decimal(days_left) / Decimal("30")
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    if prorated_amount <= 0:
        prorated_amount = Decimal("0.01")

    reference = f"UPG-{timezone.now():%Y%m%d%H%M%S}-{request.user.id_account:04d}"

    payload = {
        "ssl_transaction_type": "ccsale",
        "ssl_account_id": settings.CONVERGE_ACCOUNT_ID,
        "ssl_user_id": settings.CONVERGE_USER_ID,
        "ssl_pin": settings.CONVERGE_PIN,

        "ssl_amount": f"{prorated_amount:.2f}",
        "ssl_invoice_number": reference,
        "ssl_customer_code": str(request.user.id_account),
        "ssl_description": f"Upgrade {current_subscription} to {new_subscription}",

        "ssl_result_format": "HTML",
        "ssl_receipt_link_url": "https://www.professionalhospitalityconnections.com/converge-response/",
        "ssl_error_url": "https://www.professionalhospitalityconnections.com/converge-response/",
    }

    response = requests.post(
        settings.CONVERGE_HPP_URL,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30
    )

    print("CHANGE PLAN STATUS:", response.status_code)
    print("CHANGE PLAN RESPONSE:", response.text)
    print("CHANGE PLAN PAYLOAD:", payload)

    if response.status_code != 200:
        return Response({
            "error": "Gateway error",
            "details": response.text
        }, status=500)

    token = response.text.strip()

    return Response({
        "token": token,
        "reference": reference,
        "post_url": settings.CONVERGE_POST_URL,
        "current_subscription": current_subscription,
        "new_subscription": new_subscription,
        "prorated_amount": str(prorated_amount),
        "days_left": days_left,
        "recurring_id": active_payment.converge_recurring_id
    }, status=200)


def update_recurring_amount_in_converge(recurring_id, amount, next_payment_date):
    xml = f"""
    <txn>
        <ssl_transaction_type>ccupdaterecurring</ssl_transaction_type>
        <ssl_account_id>{settings.CONVERGE_ACCOUNT_ID}</ssl_account_id>
        <ssl_user_id>{settings.CONVERGE_USER_ID}</ssl_user_id>
        <ssl_pin>{settings.CONVERGE_PIN}</ssl_pin>
        <ssl_recurring_id>{recurring_id}</ssl_recurring_id>
        <ssl_amount>{amount:.2f}</ssl_amount>
        <ssl_billing_cycle>MONTHLY</ssl_billing_cycle>
        <ssl_next_payment_date>{next_payment_date.strftime("%m/%d/%Y")}</ssl_next_payment_date>
    </txn>
    """

    response = requests.post(
        settings.CONVERGE_XML_URL,
        data={"xmldata": xml},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30
    )

    print("UPDATE RECURRING STATUS:", response.status_code)
    print("UPDATE RECURRING RESPONSE:", response.text)

    success = (
        response.status_code == 200
        and "<ssl_result>0</ssl_result>" in response.text
    )

    return {
        "success": success,
        "raw": response.text
    }