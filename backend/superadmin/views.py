from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

from users.models import UserProfile
from seller.models import Seller
from store.models import Product, Order, OrderItem, Discount, StockAlert
from ml.sales_prediction import get_seasonal_prediction
from ml.regional_analysis import get_all_regional_data

SUPERADMIN_EMAIL    = 'admin@ecommerce.com'
SUPERADMIN_PASSWORD = 'Admin@123'


def superadmin_login(request):
    if request.session.get('role') == 'superadmin':
        return redirect('superadmin_dashboard')
    if request.method == 'POST':
        email = request.POST.get('email','').lower().strip()
        pw    = request.POST.get('password','')
        if email == SUPERADMIN_EMAIL and pw == SUPERADMIN_PASSWORD:
            request.session['role']          = 'superadmin'
            request.session['superadmin']    = True
            request.session['superadmin_name'] = 'Super Admin'
            messages.success(request, 'Welcome, Super Admin!')
            return redirect('superadmin_dashboard')
        messages.error(request, 'Invalid credentials.')
    return render(request, 'superadmin/login.html')


def superadmin_logout(request):
    request.session.flush()
    return redirect('superadmin_login')


def _sa_check(request):
    return request.session.get('role') == 'superadmin'


def superadmin_dashboard(request):
    if not _sa_check(request): return redirect('superadmin_login')

    total_users   = UserProfile.objects.filter(is_active=True).count()
    total_sellers = Seller.objects.count()
    blacklisted   = Seller.objects.filter(is_blacklisted=True).count()
    total_products= Product.objects.filter(is_active=True).count()
    total_revenue = Order.objects.filter(payment_status='Paid').aggregate(t=Sum('total_amount'))['t'] or 0
    total_orders  = Order.objects.count()

    # Membership stats
    try:
        from users.models import BazarMembership
        from django.utils import timezone as tz
        total_members = BazarMembership.objects.filter(
            status='active', end_date__gte=tz.now().date()
        ).count()
    except Exception:
        total_members = 0

    # Pending seller order requests
    try:
        from seller.models import SellerOrderRequest
        pending_seller_requests = SellerOrderRequest.objects.filter(status='pending').count()
    except Exception:
        pending_seller_requests = 0

    # Chart: last 12 months revenue
    labels, rev_data = [], []
    for i in range(11, -1, -1):
        d   = timezone.now().date().replace(day=1) - timedelta(days=i*30)
        rev = Order.objects.filter(order_date__year=d.year, order_date__month=d.month,
                                   payment_status='Paid').aggregate(t=Sum('total_amount'))['t'] or 0
        labels.append(d.strftime('%b %Y')); rev_data.append(float(rev))

    # Payment method breakdown
    pm_data = list(Order.objects.values('payment_method').annotate(c=Count('order_id')))

    predictions   = get_seasonal_prediction()
    regional_data = get_all_regional_data()
    recent_orders = Order.objects.order_by('-order_date')[:10]
    alerts        = StockAlert.objects.filter(is_resolved=False).select_related('product__seller')[:10]

    return render(request, 'superadmin/dashboard.html', {
        'total_users': total_users, 'total_sellers': total_sellers,
        'blacklisted': blacklisted, 'total_products': total_products,
        'total_revenue': total_revenue, 'total_orders': total_orders,
        'total_members': total_members,
        'pending_seller_requests': pending_seller_requests,
        'labels': labels, 'rev_data': rev_data, 'pm_data': pm_data,
        'predictions': predictions, 'regional_data': regional_data,
        'recent_orders': recent_orders, 'alerts': alerts,
    })


def manage_users(request):
    if not _sa_check(request): return redirect('superadmin_login')
    q     = request.GET.get('q','')
    users = UserProfile.objects.all().order_by('-created_at')
    if q: users = users.filter(name__icontains=q) | users.filter(email__icontains=q)
    return render(request, 'superadmin/users.html', {'users': users, 'q': q})


def toggle_user(request, user_id):
    if not _sa_check(request): return redirect('superadmin_login')
    user = get_object_or_404(UserProfile, user_id=user_id)
    if user.is_active:
        # Suspending — reason required via POST
        if request.method == 'POST':
            reason = request.POST.get('reason', '').strip()
            if not reason:
                messages.error(request, 'Please provide a suspension reason.')
                return redirect('manage_users')
            user.is_active = False
            user.suspension_reason = reason
            user.save()
            messages.success(request, f'User "{user.name}" has been suspended.')
        else:
            messages.error(request, 'Invalid request.')
    else:
        # Re-activating
        user.is_active = True
        user.suspension_reason = None
        user.save()
        messages.success(request, f'User "{user.name}" has been activated.')
    return redirect('manage_users')


def manage_sellers(request):
    if not _sa_check(request): return redirect('superadmin_login')
    q       = request.GET.get('q','')
    sellers = Seller.objects.all().order_by('-created_at')
    if q: sellers = sellers.filter(name__icontains=q) | sellers.filter(email__icontains=q)
    return render(request, 'superadmin/sellers.html', {'sellers': sellers, 'q': q})


def blacklist_seller(request, seller_id):
    if not _sa_check(request): return redirect('superadmin_login')
    seller = get_object_or_404(Seller, seller_id=seller_id)
    if request.method == 'POST':
        seller.is_blacklisted  = True
        seller.blacklist_reason= request.POST.get('reason', 'Violation of platform policies.')
        seller.save()
        messages.success(request, f'Seller "{seller.name}" has been blacklisted.')
    return redirect('manage_sellers')


def whitelist_seller(request, seller_id):
    if not _sa_check(request): return redirect('superadmin_login')
    seller = get_object_or_404(Seller, seller_id=seller_id)
    seller.is_blacklisted  = False
    seller.blacklist_reason= None
    seller.save()
    messages.success(request, f'Seller "{seller.name}" has been whitelisted.')
    return redirect('manage_sellers')


def manage_products(request):
    if not _sa_check(request): return redirect('superadmin_login')
    q        = request.GET.get('q','')
    products = Product.objects.select_related('seller').order_by('-created_at')
    if q: products = products.filter(product_name__icontains=q)
    return render(request, 'superadmin/products.html', {'products': products, 'q': q})


def manage_discounts(request):
    if not _sa_check(request): return redirect('superadmin_login')
    discounts = Discount.objects.all().order_by('-valid_from')
    return render(request, 'superadmin/discounts.html', {'discounts': discounts})


def add_discount(request):
    if not _sa_check(request): return redirect('superadmin_login')
    if request.method == 'POST':
        d = request.POST
        Discount.objects.create(
            code=d['code'].upper().strip(),
            discount_type=d['discount_type'],
            value=d['value'],
            applicable_category=d.get('applicable_category','') or None,
            festival_name=d.get('festival_name','') or None,
            valid_from=d['valid_from'],
            valid_until=d['valid_until'],
            is_active=True,
        )
        messages.success(request, f'Discount code "{d["code"].upper()}" created!')
        return redirect('manage_discounts')
    from store.models import CATEGORY_CHOICES
    return render(request, 'superadmin/discount_form.html', {'categories': CATEGORY_CHOICES})


def toggle_discount(request, discount_id):
    if not _sa_check(request): return redirect('superadmin_login')
    d = get_object_or_404(Discount, discount_id=discount_id)
    d.is_active = not d.is_active; d.save()
    messages.success(request, f'Discount "{d.code}" {"enabled" if d.is_active else "disabled"}.')
    return redirect('manage_discounts')


def delete_discount(request, discount_id):
    if not _sa_check(request): return redirect('superadmin_login')
    d = get_object_or_404(Discount, discount_id=discount_id)
    d.delete()
    messages.success(request, 'Discount deleted.')
    return redirect('manage_discounts')


def analytics(request):
    if not _sa_check(request): return redirect('superadmin_login')
    predictions   = get_seasonal_prediction()
    regional_data = get_all_regional_data()
    return render(request, 'superadmin/analytics.html', {
        'predictions': predictions, 'regional_data': regional_data,
    })


# ── Chatbot Management Views ──────────────────────────────────────────────

def chatbot_management(request):
    if not _sa_check(request): return redirect('superadmin_login')
    from chatbot.models import PendingQuestion, ChatKnowledge
    context = {
        'pending_questions': PendingQuestion.objects.filter(status='pending').select_related('session'),
        'pending_count':     PendingQuestion.objects.filter(status='pending').count(),
        'knowledge_items':   ChatKnowledge.objects.all(),
        'knowledge_count':   ChatKnowledge.objects.count(),
    }
    return render(request, 'superadmin/chatbot.html', context)


def chatbot_answer(request):
    if not _sa_check(request): return redirect('superadmin_login')
    import json
    from django.http import JsonResponse
    from django.utils import timezone
    from chatbot.models import PendingQuestion, ChatKnowledge
    data = json.loads(request.body)
    try:
        pq = PendingQuestion.objects.get(id=data['pending_id'])
        pq.answer = data['answer']
        pq.status = 'answered'
        pq.answered_at = timezone.now()
        pq.save()
        # Save to knowledge base
        if data.get('save_to_knowledge', True):
            q_text = data.get('question', pq.question)
            words  = [w for w in q_text.lower().split() if len(w) > 3]
            ChatKnowledge.objects.create(
                question=q_text,
                keywords=', '.join(words[:8]),
                answer=data['answer']
            )
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def chatbot_add_knowledge(request):
    if not _sa_check(request): return redirect('superadmin_login')
    import json
    from django.http import JsonResponse
    from chatbot.models import ChatKnowledge
    data = json.loads(request.body)
    try:
        ChatKnowledge.objects.create(
            question=data['question'],
            keywords=data['keywords'],
            answer=data['answer']
        )
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def chatbot_delete_knowledge(request, kb_id):
    if not _sa_check(request): return redirect('superadmin_login')
    from django.http import JsonResponse
    from chatbot.models import ChatKnowledge
    try:
        ChatKnowledge.objects.get(id=kb_id).delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ── Demand Forecast ──────────────────────────────────────────────────────

def demand_forecast(request):
    if not _sa_check(request): return redirect('superadmin_login')
    import json
    from ml.demand_forecast import get_demand_forecast, get_low_stock_products, get_seller_rankings
    forecast  = get_demand_forecast()
    low_stock = get_low_stock_products()
    rankings  = get_seller_rankings()
    # Serialize forecast for JS — remove non-serializable objects
    forecast_json = json.dumps([{
        'category': f['category'],
        'history':  f['history'],
        'months':   f['months'],
        'predicted_next': f['predicted_next'],
        'growth_pct': f['growth_pct'],
        'trend': f['trend'],
    } for f in forecast])
    return render(request, 'superadmin/demand_forecast.html', {
        'forecast': forecast,
        'forecast_json': forecast_json,
        'low_stock': low_stock,
        'rankings': rankings,
        'low_stock_count': len(list(low_stock)),
    })


# ── PDF Sales Report ─────────────────────────────────────────────────────

def sales_report_pdf(request):
    if not _sa_check(request): return redirect('superadmin_login')
    import io, os
    from django.http import HttpResponse
    from django.utils import timezone
    from store.models import Order, OrderItem
    from django.db.models import Sum, Count

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        HAS_REPORTLAB = True
    except ImportError:
        HAS_REPORTLAB = False

    if not HAS_REPORTLAB:
        # Fallback: CSV export
        import csv
        from django.http import HttpResponse
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="sales_report.csv"'
        writer = csv.writer(response)
        writer.writerow(['Order ID', 'Date', 'Amount', 'Status', 'Payment'])
        for order in Order.objects.all().order_by('-order_date')[:500]:
            writer.writerow([
                str(order.order_id)[:8],
                order.order_date.strftime('%d-%m-%Y'),
                order.total_amount,
                order.order_status,
                order.payment_method,
            ])
        return response

    # PDF with reportlab
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=1.5*cm, leftMargin=1.5*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    story  = []

    title_style = ParagraphStyle('Title', parent=styles['Title'],
                                  fontSize=22, textColor=colors.HexColor('#2874F0'),
                                  alignment=TA_CENTER, spaceAfter=6)
    sub_style = ParagraphStyle('Sub', parent=styles['Normal'],
                                fontSize=10, textColor=colors.grey,
                                alignment=TA_CENTER, spaceAfter=16)
    head_style = ParagraphStyle('Head', parent=styles['Heading2'],
                                 fontSize=13, textColor=colors.HexColor('#2874F0'),
                                 spaceBefore=14, spaceAfter=6)

    story.append(Paragraph("🛒 OnlineBazar", title_style))
    story.append(Paragraph(f"Sales Report — Generated on {timezone.now().strftime('%d %b %Y, %I:%M %p')}",
                            sub_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#FB641B')))
    story.append(Spacer(1, 14))

    # Summary stats
    total_orders  = Order.objects.count()
    total_revenue = Order.objects.filter(payment_status='Paid').aggregate(t=Sum('total_amount'))['t'] or 0
    delivered     = Order.objects.filter(order_status='Delivered').count()
    pending       = Order.objects.filter(order_status='Placed').count()

    story.append(Paragraph("📊 Summary", head_style))
    summary_data = [
        ['Metric', 'Value'],
        ['Total Orders', str(total_orders)],
        ['Total Revenue', f'₹{total_revenue:,.2f}'],
        ['Delivered Orders', str(delivered)],
        ['Pending Orders', str(pending)],
    ]
    summary_table = Table(summary_data, colWidths=[8*cm, 8*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2874F0')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F1F3F6')]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 16))

    # Category-wise sales
    story.append(Paragraph("📦 Category-wise Sales", head_style))
    cat_data = [['Category', 'Units Sold', 'Revenue']]
    from store.models import CATEGORY_CHOICES
    for cat, label in CATEGORY_CHOICES:
        items = OrderItem.objects.filter(product__category=cat)
        units = items.aggregate(u=Sum('quantity'))['u'] or 0
        rev   = items.aggregate(r=Sum('price_at_purchase'))['r'] or 0
        if units > 0:
            cat_data.append([label, str(units), f'₹{rev:,.2f}'])
    cat_table = Table(cat_data, colWidths=[7*cm, 5*cm, 6*cm])
    cat_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#FB641B')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#FFF3E0')]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
    ]))
    story.append(cat_table)
    story.append(Spacer(1, 16))

    # Recent 20 orders
    story.append(Paragraph("🧾 Recent Orders", head_style))
    order_data = [['Order ID', 'Date', 'Amount', 'Status', 'Payment']]
    for order in Order.objects.all().order_by('-order_date')[:20]:
        order_data.append([
            str(order.order_id)[:8].upper(),
            order.order_date.strftime('%d %b %Y'),
            f'₹{order.total_amount:,.2f}',
            order.order_status,
            order.payment_method,
        ])
    order_table = Table(order_data, colWidths=[3.5*cm, 3.5*cm, 3.5*cm, 4*cm, 3.5*cm])
    order_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2874F0')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F1F3F6')]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(order_table)

    # Footer
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
    story.append(Paragraph("Founders: Ankit Sharma & Niraj Kumar | OnlineBazar MCA Project",
                            ParagraphStyle('footer', parent=styles['Normal'],
                                           fontSize=8, textColor=colors.grey,
                                           alignment=TA_CENTER, spaceBefore=8)))

    doc.build(story)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="OnlineBazar_Sales_Report_{timezone.now().strftime("%Y%m%d")}.pdf"'
    return response


# ── Fake Review Detection ──────────────────────────────────────────────────

def fake_reviews(request):
    if not _sa_check(request): return redirect('superadmin_login')
    from store.models import Product, Review
    from ml.fake_review_detector import analyze_review

    # Analyze all reviews
    all_reviews = Review.objects.select_related('product', 'user').order_by('-created_at')[:200]
    analyzed = []
    fake_count = 0
    suspicious_count = 0
    for rev in all_reviews:
        result = analyze_review(rev.review_text, rev.rating, rev.user_id, rev.product_id)
        analyzed.append({'review': rev, 'analysis': result})
        if result['label'] == 'Likely Fake':
            fake_count += 1
        elif result['label'] == 'Suspicious':
            suspicious_count += 1

    # Sort: fakes first
    analyzed.sort(key=lambda x: x['analysis']['confidence'], reverse=True)

    return render(request, 'superadmin/fake_reviews.html', {
        'analyzed': analyzed,
        'fake_count': fake_count,
        'suspicious_count': suspicious_count,
        'genuine_count': len(analyzed) - fake_count - suspicious_count,
        'total': len(analyzed),
    })


def delete_review(request, review_id):
    if not _sa_check(request): return redirect('superadmin_login')
    from store.models import Review
    from django.http import JsonResponse
    try:
        Review.objects.get(id=review_id).delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ── Dynamic Pricing ──────────────────────────────────────────────────────

def dynamic_pricing(request):
    if not _sa_check(request): return redirect('superadmin_login')
    from ml.dynamic_pricing import get_all_pricing_recommendations, get_dynamic_price
    from store.models import Product
    import json

    recommendations = get_all_pricing_recommendations()

    # Handle apply price
    if request.method == 'POST':
        from django.http import JsonResponse
        data = json.loads(request.body)
        try:
            product = Product.objects.get(product_id=data['product_id'])
            product.price = data['new_price']
            product.save(update_fields=['price'])
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return render(request, 'superadmin/dynamic_pricing.html', {
        'recommendations': recommendations,
        'total_products': len(recommendations),
    })


# ── Return Requests Management ───────────────────────────────────────────

def return_requests(request):
    if not _sa_check(request): return redirect('superadmin_login')
    from store.models import ReturnRequest
    import json

    status_filter = request.GET.get('status', 'all')
    qs = ReturnRequest.objects.select_related(
        'user', 'order', 'order_item', 'order_item__product'
    )
    if status_filter != 'all':
        qs = qs.filter(status=status_filter)

    counts = {
        'all':      ReturnRequest.objects.count(),
        'pending':  ReturnRequest.objects.filter(status='pending').count(),
        'approved': ReturnRequest.objects.filter(status='approved').count(),
        'rejected': ReturnRequest.objects.filter(status='rejected').count(),
        'refunded': ReturnRequest.objects.filter(status='refunded').count(),
    }

    # Handle status update via POST
    if request.method == 'POST':
        from django.http import JsonResponse
        data = json.loads(request.body)
        try:
            rr = ReturnRequest.objects.get(id=data['return_id'])
            rr.status     = data['status']
            rr.admin_note = data.get('admin_note', data.get('note', ''))
            if data['status'] == 'refunded':
                from django.utils import timezone
                rr.resolved_at = timezone.now()
                # Restore stock if return approved
                if rr.order_item:
                    prod = rr.order_item.product
                    prod.stock_quantity += rr.order_item.quantity
                    prod.save(update_fields=['stock_quantity'])
            rr.save()
            return JsonResponse({'success': True, 'message': f'Status updated to {rr.get_status_display()}'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return render(request, 'superadmin/return_requests.html', {
        'returns': qs,
        'counts': counts,
        'status_filter': status_filter,
        'filter_choices': [
            ('all',      'All'),
            ('pending',  '⏳ Pending'),
            ('approved', '✅ Approved'),
            ('picked_up','📦 Picked Up'),
            ('refunded', '💰 Refunded'),
            ('rejected', '❌ Rejected'),
        ],
    })


# ─── SUPERADMIN SELLER ACTIVITY LOG ──────────────────────────────────────────

def seller_activity_log(request):
    from store.models import SellerActivity, SellerDiscount
    from seller.models import Seller
    activities = SellerActivity.objects.select_related('seller', 'product').order_by('-created_at')
    # Filter by seller if requested
    seller_filter = request.GET.get('seller_id')
    if seller_filter:
        activities = activities.filter(seller__seller_id=seller_filter)
    action_filter = request.GET.get('action')
    if action_filter:
        activities = activities.filter(action=action_filter)
    sellers = Seller.objects.all()
    # Summary counts
    from django.db.models import Count
    summary = SellerActivity.objects.values('action').annotate(count=Count('id')).order_by('-count')
    return render(request, 'superadmin/seller_activity_log.html', {
        'activities': activities,
        'sellers': sellers,
        'seller_filter': seller_filter,
        'action_filter': action_filter,
        'summary': summary,
    })
