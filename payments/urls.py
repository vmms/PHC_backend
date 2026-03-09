from django.urls import path
from . import views

urlpatterns = [
    path("charge/", views.Process_payment, name="process-payment"),
    path("test/", views.Process_payment_test, name="process-payment-test"),
]