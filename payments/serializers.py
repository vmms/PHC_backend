from rest_framework import serializers


class PaymentSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    card_number = serializers.CharField(max_length=16)
    exp_date = serializers.CharField(max_length=4)  # MMYY
    cvv = serializers.CharField(max_length=4)
    invoice_number = serializers.CharField(max_length=50, required=False)