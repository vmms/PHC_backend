from django.db import models
from accounts.models import Account

class Message(models.Model):
    id_message = models.AutoField(primary_key=True)

    sender_account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="sent_messages",
        db_column="sender_account_id"
    )

    receiver_account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="received_messages",
        db_column="receiver_account_id"
    )

    title = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_column="title"
    )

    message = models.TextField()
    status = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)  # fecha de creación
    conversation_id = models.IntegerField(null=True, blank=True)  # permite agrupar chat 1 a 1

    class Meta:
        db_table = "message"
        ordering = ["created_at"]  # ordenar por fecha por defecto

    def __str__(self):
        return f"Message {self.id_message} from {self.sender_account} to {self.receiver_account}"
