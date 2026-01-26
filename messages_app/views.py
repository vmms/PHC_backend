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
    print(request.data)
    user_account = request.user
    account_type = user_account.subscription
    print(account_type)

    receiver_candidate_id = request.data.get("receiver_candidate_id")
    receiver_company_id = request.data.get("receiver_company_id")
    text = request.data.get("message")
    title = request.data.get("title")  
    origin = request.data.get("origin")

    if not text:
        return Response({"error": "message is required"}, status=400)

    # -------------------------------------------------------
    # VALIDAR SI EL EMISOR (CANDIDATO) ESTÁ ACTIVO
    # -------------------------------------------------------
    if account_type == "candidate":
        try:
            sender_candidate = Candidate.objects.get(account=user_account)
        except Candidate.DoesNotExist:
            return Response(
                {"error": "Candidate profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if not sender_candidate.is_active:
            return Response(
                {"error": "Inactive candidates cannot send messages"},
                status=status.HTTP_403_FORBIDDEN
            )

    # -------------------------------------------------------
    # Determinar receiver_account_id
    # -------------------------------------------------------
    if account_type == "candidate":
        if not receiver_company_id:
            return Response({"error": "Must send receiver_company_id"}, status=400)
        try:
            company = Company.objects.get(id_company=receiver_company_id)
            receiver_account_id = company.account_id
        except Company.DoesNotExist:
            return Response({"error": "Company not found"}, status=404)

    elif account_type in ["company", "premium"]:
        if not receiver_candidate_id:
            return Response({"error": "Must send receiver_candidate_id"}, status=400)
        try:
            candidate = Candidate.objects.get(id_candidate=receiver_candidate_id)
            # -------------------------------------------------------
            # VALIDAR SI EL RECEPTOR (CANDIDATO) ESTÁ ACTIVO
            # -------------------------------------------------------
            if not candidate.is_active:
                return Response(
                    {"error": "Cannot send messages to an inactive candidate"},
                    status=status.HTTP_403_FORBIDDEN
                )
                
            receiver_account_id = candidate.account_id
        except Candidate.DoesNotExist:
            return Response({"error": "Candidate not found"}, status=404)
    else:
        return Response({"error": "Unknown account type"}, status=400)

    # -------------------------------------------------------
    # Buscar conversación existente (1 a 1)
    # -------------------------------------------------------
    conversation = Message.objects.filter(
        Q(sender_account=user_account, receiver_account_id=receiver_account_id) |
        Q(sender_account_id=receiver_account_id, receiver_account=user_account)
    ).order_by('created_at').first()

    if conversation:
        conversation_id = conversation.conversation_id
        conversation_title = title   # solo para ESTE mensaje

    else:
        max_conv = Message.objects.aggregate(
            Max('conversation_id')
        )['conversation_id__max'] or 0

        conversation_id = max_conv + 1
        conversation_title = title

        if origin in ["applications", "search"]:
            try:
                company = Company.objects.get(account_id=request.user.id_account)
                if origin == "applications":
                    company.first_contact_applications += 1
                else:
                    company.first_contact_search += 1
                company.save()
            except Company.DoesNotExist:
                return Response({"error": "Company not found"}, status=404)  

    # -------------------------------------------------------
    # Crear mensaje
    # -------------------------------------------------------
    message = Message.objects.create(
        sender_account=user_account,
        receiver_account_id=receiver_account_id,
        message=text,
        status=0,
        conversation_id=conversation_id,
        title=conversation_title
    )

    return Response(MessageSerializer(message).data, status=201)

# ---------------------------------------------------------
# 2. LISTA DE CHATS (CON QUIÉN HE HABLADO)
# ---------------------------------------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def list_chats(request):
    user_account = request.user
    data = request.data or {}

    title = data.get("title")
    company_name = data.get("company")

    # -----------------------------------
    # 1. Mensajes donde participo
    # -----------------------------------
    messages_qs = Message.objects.filter(
        Q(sender_account_id=user_account.id_account) |
        Q(receiver_account_id=user_account.id_account)
    )

    # -----------------------------------
    # 2. Filtro por title
    # -----------------------------------
    if title:
        messages_qs = messages_qs.filter(title__icontains=title)

    # -----------------------------------
    # 3. Filtro por company (sin duplicar columnas)
    # -----------------------------------
    if company_name:
        company_account_ids = Company.objects.filter(
            name__icontains=company_name
        ).values_list("account_id", flat=True)

        messages_qs = messages_qs.filter(
            Q(sender_account_id__in=company_account_ids) |
            Q(receiver_account_id__in=company_account_ids)
        )

    # -----------------------------------
    # 4. Partners únicos
    # -----------------------------------
    chat_partners_ids = (
        messages_qs.values_list('sender_account_id', flat=True)
        .union(messages_qs.values_list('receiver_account_id', flat=True))
    )

    chat_partners_ids = [
        acc_id for acc_id in chat_partners_ids
        if acc_id != user_account.id_account
    ]

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
                "company_id": company.id_company,
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

def format_date(date):
    if not date:
        return None
    return date.strftime("%m-%d-%Y")

# ---------------------------------------------------------
# 3. CHAT DETALLADO (LOS MENSAJES ENTRE YO Y LA OTRA PERSONA)
# ---------------------------------------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_detail(request):
    user_account = request.user

    id_candidate = request.data.get("candidate_id")
    id_company = request.data.get("company_id")
    print("company_id", id_company)

    if id_candidate:
        try:
            acc_id = Candidate.objects.get(id_candidate=id_candidate).account_id
        except Candidate.DoesNotExist:
            return Response({"error": "Candidate not found"}, status=404)
    elif id_company:
        try:
            acc_id = Company.objects.get(id_company=id_company).account_id
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
        "created_at": format_date(m.created_at),
        "title": m.title
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



