from django.db import models

class Payment(models.Model):
    id_payment = models.AutoField(
        primary_key=True,
        db_column='id_company_subscription'
    )

    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.DO_NOTHING,
        db_column='company_id'
    )

    invoice_number = models.CharField(max_length=30, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=30, default='pending')

    converge_recurring_id = models.CharField(max_length=100, null=True, blank=True)
    converge_result = models.CharField(max_length=10, null=True, blank=True)
    converge_result_message = models.CharField(max_length=100, null=True, blank=True)

    billing_cycle = models.CharField(max_length=30, null=True, blank=True)
    next_payment_date = models.DateField(null=True, blank=True)

    started_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'payment'