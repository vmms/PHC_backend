from django.conf import settings
from django.core.mail import send_mail


def send_new_message_email(receiver_email, message_preview):

    plain_message = f"""
Hello,

You have received a new message on Professional Hospitality Connections.

Message preview:
"{message_preview}"

Please log in to your account to read the full message and continue the conversation.

Best regards,

Professional Hospitality Connections
info@professionalhospitalityconnections.com
www.professionalhospitalityconnections.com
"""

    html_message = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333333;">

<p>Hello,</p>

<p>
You have received a new message on
<strong>Professional Hospitality Connections</strong>.
</p>

<p>
<strong>Message preview:</strong><br>
&quot;{message_preview}&quot;
</p>

<p>
Please log in to your account to read the full message and continue the conversation.
</p>

<p>
Best regards,<br><br>

<strong>Professional Hospitality Connections</strong><br>

<a href="mailto:info@professionalhospitalityconnections.com">
info@professionalhospitalityconnections.com
</a><br>

<a href="https://www.professionalhospitalityconnections.com">
www.professionalhospitalityconnections.com
</a>
</p>

</body>
</html>
"""

    send_mail(
        subject="You have a new message on Professional Hospitality Connections",
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[receiver_email],
        html_message=html_message,
        fail_silently=False
    )