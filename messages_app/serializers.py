from rest_framework import serializers
from .models import Message

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = [
            'id_message',
            'sender_account',
            'receiver_account',
            'message',
            'status',
            'created_at',
            'conversation_id'
        ]
