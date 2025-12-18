from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q, Max

from .models import Message
from .serializers import MessageSerializer
from candidates.models import Candidate
from companies.models import Company
from accounts.models import Account


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_message(request):
    user_account = request.user  # Account logueado
    account_type = user_account.subscription  # candidate, company, premium
    print("user_account:",user_account.id_account)

    receiver_candidate_id = request.data.get("receiver_candidate_id")
    receiver_company_id = request.data.get("receiver_company_id")
    text = request.data.get("message")

    if not text:
        return Response({"error": "message is required"}, status=400)

    # -------------------------------------------------------
    # Determinar receiver_account_id según tipo de cuenta
    # -------------------------------------------------------
    if account_type == "candidate":  # candidato enviando a empresa
        if not receiver_company_id:
            return Response({"error": "Must send receiver_company_id"}, status=400)
        try:
            company = Company.objects.get(account_id=receiver_company_id)
            receiver_account_id = company.account_id
        except Company.DoesNotExist:
            return Response({"error": "Company not found"}, status=404)

    elif account_type in ["company", "premium"]:  # empresa enviando a candidato
        if not receiver_candidate_id:
            return Response({"error": "Must send receiver_candidate_id"}, status=400)
        try:
            candidate = Candidate.objects.get(id_candidate=receiver_candidate_id)
            receiver_account_id = candidate.account_id
        except Candidate.DoesNotExist:
            return Response({"error": "Candidate not found"}, status=404)
    else:
        return Response({"error": "Unknown account type"}, status=400)

    # -------------------------------------------------------
    # Encontrar conversation_id existente (1 a 1)
    # -------------------------------------------------------
    conversation = Message.objects.filter(
        Q(sender_account=user_account, receiver_account_id=receiver_account_id) |
        Q(sender_account_id=receiver_account_id, receiver_account=user_account)
    ).order_by('-created_at').first()

    if conversation:
        conversation_id = conversation.conversation_id
    else:
        # No hay conversación previa → asignar el siguiente conversation_id secuencial
        max_conv = Message.objects.aggregate(Max('conversation_id'))['conversation_id__max'] or 0
        conversation_id = max_conv + 1

    # -------------------------------------------------------
    # Crear el mensaje
    # -------------------------------------------------------
    message = Message.objects.create(
        sender_account=user_account,
        receiver_account_id=receiver_account_id,
        message=text,
        status=0,
        conversation_id=conversation_id
    )

    return Response(MessageSerializer(message).data, status=201)

# ---------------------------------------------------------
# 2. LISTA DE CHATS (CON QUIÉN HE HABLADO)
# ---------------------------------------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def list_chats(request):
    user_account = request.user

    chat_partners_ids = (
        Message.objects.filter(sender_account_id=user_account.id_account)
        .values_list('receiver_account_id', flat=True)
        .union(
            Message.objects.filter(receiver_account_id=user_account.id_account)
            .values_list('sender_account_id', flat=True)
        )
    )

    result = []
    for acc_id in chat_partners_ids:
        unread_count = Message.objects.filter(
            sender_account_id=acc_id,
            receiver_account_id=user_account.id_account,
            status=0
        ).count()

        has_unread = unread_count > 0

        if user_account.subscription == 'candidate':
            company = Company.objects.get(account_id=acc_id)
            result.append({
                "company_id": company.id_company,  # 👈 mejor que account_id
                "company_name": company.name,
                "has_unread": has_unread
            })
        else:
            candidate = Candidate.objects.get(account_id=acc_id)
            result.append({
                "candidate_id": candidate.id_candidate,
                "candidate_name": f"{candidate.first_name} {candidate.last_name}",
                "has_unread": has_unread
            })

    return Response(result, status=200)



# ---------------------------------------------------------
# 3. CHAT DETALLADO (LOS MENSAJES ENTRE YO Y LA OTRA PERSONA)
# ---------------------------------------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_detail(request):
    user_account = request.user

    candidate_id = request.data.get("candidate_id")
    company_id = request.data.get("company_id")

    if candidate_id:
        try:
            acc_id = Candidate.objects.get(account_id=candidate_id).account_id
        except Candidate.DoesNotExist:
            return Response({"error": "Candidate not found"}, status=404)
    elif company_id:
        try:
            acc_id = Company.objects.get(account_id=company_id).account_id
        except Company.DoesNotExist:
            return Response({"error": "Company not found"}, status=404)
    else:
        return Response({"error": "Must send candidate_id or company_id"}, status=400)

    # Todos los mensajes entre yo y la otra cuenta
    messages = Message.objects.filter(
        sender_account_id__in=[user_account.id_account, acc_id],
        receiver_account_id__in=[user_account.id_account, acc_id]
    ).order_by("created_at")

    # Marcar como leídos los mensajes que me enviaron a mí y aún no están leídos
    Message.objects.filter(
        sender_account_id=acc_id,
        receiver_account_id=user_account.id_account,
        status=0
    ).update(status=1)

    data = [{
        "from": "me" if m.sender_account_id == user_account.id_account else "other",
        "message": m.message,
        "status": m.status,
        "created_at": m.created_at
    } for m in messages]

    return Response(data, status=200)


# ---------------------------------------------------------
# 4. MARCAR COMO LEÍDO
# ---------------------------------------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_read(request):
    message_id = request.data.get("id_message")
    user_account = request.user

    try:
        # Solo se puede marcar como leído si el mensaje fue enviado a este usuario
        msg = Message.objects.get(id_message=message_id, receiver_account=user_account)
        msg.status = 1
        msg.save()
        return Response({"message": "read"}, status=200)
    except Message.DoesNotExist:
        return Response({"error": "Message not found or not authorized"}, status=404)
