from django.urls import path
from . import views

urlpatterns = [
    path("charge/", views.Process_payment, name="process-payment"),
    path("converge-response/", views.converge_response, name="converge-response"),
    path("cancel/", views.cancel_subscription, name="cancel-subscription"),
    path("sync/", views.sync_subscriptions, name="sync-subscriptions"),
    path("change-plan/", views.change_plan, name="change-plan"),
]