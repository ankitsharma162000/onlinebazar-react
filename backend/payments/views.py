from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json

from store.models import Order
from users.models import UserProfile


def initiate_payment(request, order_id):
    uid = request.session.get('user_id')
    if not uid: return redirect('user_login')
    order = get_object_or_404(Order, order_id=order_id)
    try:
        import razorpay
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        rz_order = client.order.create({
            'amount': int(float(order.total_amount) * 100),
            'currency': 'INR',
            'payment_capture': 1,
        })
        order.razorpay_order_id = rz_order['id']
        order.save()
        return render(request, 'payments/pay.html', {
            'order': order,
            'razorpay_order_id': rz_order['id'],
            'razorpay_key': settings.RAZORPAY_KEY_ID,
            'amount': int(float(order.total_amount) * 100),
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
def payment_callback(request):
    if request.method == 'POST':
        data = request.POST
        try:
            import razorpay
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            client.utility.verify_payment_signature({
                'razorpay_order_id':   data['razorpay_order_id'],
                'razorpay_payment_id': data['razorpay_payment_id'],
                'razorpay_signature':  data['razorpay_signature'],
            })
            order = Order.objects.get(razorpay_order_id=data['razorpay_order_id'])
            order.razorpay_payment_id = data['razorpay_payment_id']
            order.payment_status = 'Paid'
            order.save()
            return redirect('order_success', order_id=order.order_id)
        except Exception:
            return render(request, 'payments/failed.html')
    return redirect('home')
