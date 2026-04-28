import requests
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
import uuid


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def Process_payment(request):

    plan = request.data.get("subscription")

    if plan == "temp":
        amount = "150.00"
    elif plan == "full":
        amount = "250.00"
    else:
        return Response({"error": "Invalid plan"}, status=400)

    reference = str(uuid.uuid4())

    payload = {
        "ssl_transaction_type": "ccsale",
        "ssl_merchant_id": "2735183",#settings.ELAVON_CONFIG["merchant_id"],
        "ssl_user_id": "apiuser148715", #settings.ELAVON_CONFIG["user_id"],
        "ssl_pin": "JNVO5LI3K9UJO93K6232A3KM7HQYGG9NBD0LAJ55POMAN1VNNMXHIIBR4MML2RRV",#settings.ELAVON_CONFIG["pin"],
        
        "ssl_amount": amount,
        "ssl_invoice_number": reference,
        "ssl_show_form": "PAYMENT_FORM",
    }

    try:
        response = requests.post(
            #"https://api.demo.convergepay.com/hosted-payments/transaction_token",
            "https://api.convergepay.com/hosted-payments/transaction_token",
            data=payload,
            timeout=30
        )
        print(response.text)
        print(payload)

        # ⭐ Validar HTTP response
        if response.status_code != 200:
            return Response({
                "error": "Gateway error",
                "details": response.text
            }, status=500)

        # ⭐ Parsear JSON de forma segura
        try:
            data = response.json()
        except ValueError:
            return Response({
                "error": "Invalid gateway response",
                "details": response.text
            }, status=500)

        token = data.get("ssl_txn_auth_token")

        if not token:
            return Response({
                "error": "Token not generated",
                "gateway_response": data
            }, status=500)

        payment_url = f"https://www.convergepay.com/hosted-payments?ssl_txn_auth_token={token}"

        return Response({
            "payment_url": payment_url,
            "reference": reference
        })

    except requests.exceptions.RequestException as e:
        return Response({
            "error": "Payment service unavailable",
            "details": str(e)
        }, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def Process_payment_test(request):
    plan = request.data.get("subscription")
    if plan == "temp":
        return Response({
            "payment_url": "https://www.convergepay.com/hosted-payments?ssl_txn_auth_token=OidnXG%2BpT%2ByHB6akdilHmQAAAZvsmGMz",
            "reference": "google"
        })
    elif plan == "full":
        return Response({
            "payment_url": "https://www.convergepay.com/hosted-payments?ssl_txn_auth_token=9cyYUJMwTFGUpvcRoHJu5gAAAZvsmSqP", 
            "reference": "google"
        })
    else:
        return Response({"error": "Invalid plan"}, status=400)