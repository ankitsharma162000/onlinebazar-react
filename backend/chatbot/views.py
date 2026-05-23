import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import ChatSession, ChatMessage, PendingQuestion
from .brain import find_answer


def _get_or_create_session(request):
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key
    session, _ = ChatSession.objects.get_or_create(
        session_key=session_key,
        defaults={'user_name': request.session.get('user_name', 'Guest')}
    )
    return session


def get_order_history(request):
    """Return buyer's recent orders as a list for the chatbot to display."""
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'orders': [], 'logged_in': False})

        from users.models import UserProfile
        from store.models import Order, OrderItem
        user = UserProfile.objects.get(user_id=user_id)
        orders = Order.objects.filter(user=user).order_by('-order_date')[:10]

        order_list = []
        for o in orders:
            items = OrderItem.objects.filter(order=o).select_related('product__seller')
            item_details = []
            for i in items:
                item_details.append({
                    'product_name': i.product.product_name,
                    'quantity': i.quantity,
                    'price': float(i.price_at_purchase),
                    'seller_email': i.product.seller.email if i.product.seller else None,
                    'seller_name': i.product.seller.name if i.product.seller else 'Unknown',
                })
            order_list.append({
                'order_id': str(o.order_id),
                'short_id': str(o.order_id)[:8].upper(),
                'date': o.order_date.strftime('%d %b %Y'),
                'status': o.order_status,
                'total': float(o.total_amount),
                'items': item_details,
            })

        return JsonResponse({'orders': order_list, 'logged_in': True})
    except Exception as e:
        return JsonResponse({'orders': [], 'error': str(e)})


@csrf_exempt
@require_POST
def chat_message(request):
    try:
        data = json.loads(request.body)
        user_msg     = data.get('message', '').strip()
        order_id     = data.get('order_id', '')       # set when buyer picked an order
        product_name = data.get('product_name', '')   # specific product in that order
        seller_email = data.get('seller_email', '')   # seller of that product
        seller_name  = data.get('seller_name', '')

        if not user_msg:
            return JsonResponse({'error': 'Empty message'}, status=400)

        session = _get_or_create_session(request)
        ChatMessage.objects.create(session=session, sender='user', message=user_msg)

        # Try to find an answer from brain
        answer, source = find_answer(user_msg)

        if answer:
            ChatMessage.objects.create(
                session=session, sender='bot', message=answer, status='answered'
            )
            return JsonResponse({'reply': answer, 'source': source, 'status': 'answered'})

        else:
            # Escalate: if buyer selected an order+product, go to seller; else superadmin
            if seller_email and order_id:
                pending = PendingQuestion.objects.create(
                    session=session,
                    question=user_msg,
                    escalated_to='seller',
                    seller_email=seller_email,
                    order_id=order_id,
                    product_name=product_name,
                )
                bot_reply = (
                    f"🙋 I don't have the answer for that. Your question about "
                    f"<b>{product_name}</b> (Order #{order_id[:8].upper()}) has been forwarded "
                    f"to the seller <b>{seller_name}</b>. They will reply shortly in this chat!"
                )
            else:
                pending = PendingQuestion.objects.create(
                    session=session,
                    question=user_msg,
                    escalated_to='superadmin',
                )
                bot_reply = (
                    "🙋 I don't have an answer to that yet. Your question has been forwarded to "
                    "our support team. Please wait — they will reply shortly in this chat!"
                )

            ChatMessage.objects.create(
                session=session, sender='bot', message=bot_reply, status='pending'
            )
            return JsonResponse({
                'reply': bot_reply,
                'source': 'escalated',
                'status': 'pending',
                'pending_id': str(pending.id),
            })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def check_updates(request):
    """Frontend polls this every 5 seconds for seller/admin replies."""
    try:
        session = _get_or_create_session(request)

        answered = PendingQuestion.objects.filter(
            session=session,
            status='answered',
            answer__isnull=False,
        ).exclude(answer='')

        replies = []
        for q in answered:
            label = '👨‍💼 Seller' if q.escalated_to == 'seller' else '🛡️ Support Team'
            replies.append({
                'question': q.question,
                'answer': q.answer,
                'from': label,
            })
            ChatMessage.objects.create(
                session=session,
                sender='seller' if q.escalated_to == 'seller' else 'admin',
                message=q.answer,
                status='answered'
            )
            q.delete()

        return JsonResponse({'replies': replies})
    except Exception as e:
        return JsonResponse({'replies': [], 'error': str(e)})
