from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone

from .models import (Product, Cart, Wishlist, Order, OrderItem,
                     Review, Discount, SearchHistory, StockAlert, CATEGORY_CHOICES)
from users.models import UserProfile
from ml.recommendations import get_recommendations
from ml.stock_alert import check_and_generate_stock_alerts


def _get_user(request):
    uid = request.session.get('user_id')
    if uid and request.session.get('role') == 'user':
        try:
            return UserProfile.objects.get(user_id=uid)
        except UserProfile.DoesNotExist:
            pass
    return None


# ─── HOME ────────────────────────────────────────────────────────────
def home(request):
    user = _get_user(request)
    query    = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()

    products = Product.objects.filter(is_active=True, seller__is_blacklisted=False)
    if query:
        products = products.filter(
            Q(product_name__icontains=query) | Q(description__icontains=query)
            | Q(category__icontains=query))
        if user:
            SearchHistory.objects.create(user=user, searched_query=query,
                                         category=category or '')
    if category:
        products = products.filter(category=category)

    featured     = Product.objects.filter(is_active=True, seller__is_blacklisted=False).order_by('?')[:8]
    recommended  = get_recommendations(str(user.user_id)) if user else []

    # Membership status for navbar badge
    is_member = False
    if user:
        try:
            from users.models import BazarMembership
            m = BazarMembership.objects.get(user=user)
            is_member = m.is_valid()
        except Exception:
            pass

    # Pagination — 12 products per page
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    return render(request, 'store/home.html', {
        'products': page_obj, 'recommended': recommended,
        'featured': featured, 'query': query,
        'selected_category': category,
        'is_member': is_member,
        'all_categories': CATEGORY_CHOICES,
        'page_obj': page_obj,
        'paginator': paginator,
    })


# ─── PRODUCT DETAIL ──────────────────────────────────────────────────
def product_detail(request, product_id):
    product = get_object_or_404(Product, product_id=product_id, is_active=True)
    user    = _get_user(request)
    reviews = product.reviews.select_related('user').order_by('-created_at')
    in_wishlist  = False
    user_review  = None

    if user:
        in_wishlist = Wishlist.objects.filter(user=user, product=product).exists()
        user_review = Review.objects.filter(user=user, product=product).first()
        SearchHistory.objects.create(user=user,
                                     searched_query=product.product_name,
                                     category=product.category)
    if request.method == 'POST' and user:
        if not user_review:
            Review.objects.create(user=user, product=product,
                                  rating=int(request.POST.get('rating', 5)),
                                  review_text=request.POST.get('review_text', ''))
            messages.success(request, 'Your review has been submitted!')
        else:
            messages.warning(request, 'You have already reviewed this product.')
        return redirect('product_detail', product_id=product_id)

    related = Product.objects.filter(category=product.category,
                                     is_active=True).exclude(product_id=product_id)[:4]
    return render(request, 'store/product_detail.html', {
        'product': product, 'reviews': reviews,
        'in_wishlist': in_wishlist, 'user_review': user_review,
        'related': related, 'user': user,
        'range5': range(1, 6),
    })


# ─── CART ────────────────────────────────────────────────────────────
def cart_view(request):
    user = _get_user(request)
    if not user:
        messages.warning(request, 'Please login to view your cart.')
        return redirect('user_login')

    items       = Cart.objects.filter(user=user).select_related('product')
    subtotal    = sum(float(i.product.price) * i.quantity for i in items)
    disc_amount = 0
    disc_obj    = None
    code        = request.session.get('coupon_code')

    if code:
        today = timezone.now().date()
        try:
            d = Discount.objects.get(code=code, is_active=True,
                                     valid_from__lte=today, valid_until__gte=today)
            disc_amount = float(d.value) if d.discount_type == 'flat' \
                          else subtotal * float(d.value) / 100
            disc_obj = d
        except Discount.DoesNotExist:
            request.session.pop('coupon_code', None)

    total = max(0, subtotal - disc_amount)
    return render(request, 'store/cart.html', {
        'items': items, 'subtotal': round(subtotal, 2),
        'disc_amount': round(disc_amount, 2),
        'total': round(total, 2), 'coupon_code': code,
        'disc_obj': disc_obj, 'user': user,
    })


def add_to_cart(request, product_id):
    user = _get_user(request)
    if not user:
        messages.warning(request, 'Please login to add items to cart.')
        return redirect('user_login')
    product = get_object_or_404(Product, product_id=product_id, is_active=True)
    if product.stock_quantity == 0:
        messages.error(request, 'This product is out of stock.')
        return redirect(request.META.get('HTTP_REFERER', 'home'))
    item, created = Cart.objects.get_or_create(user=user, product=product)
    if not created:
        if item.quantity < product.stock_quantity:
            item.quantity += 1; item.save()
            messages.success(request, 'Cart quantity updated.')
        else:
            messages.warning(request, f'Only {product.stock_quantity} units available.')
    else:
        messages.success(request, f'"{product.product_name}" added to cart!')
    return redirect(request.META.get('HTTP_REFERER', 'home'))


def update_cart(request, cart_id):
    user = _get_user(request)
    if not user:
        return redirect('user_login')
    item   = get_object_or_404(Cart, id=cart_id, user=user)
    action = request.POST.get('action')
    if action == 'increase' and item.quantity < item.product.stock_quantity:
        item.quantity += 1; item.save()
    elif action == 'decrease':
        if item.quantity > 1: item.quantity -= 1; item.save()
        else: item.delete()
    elif action == 'remove':
        item.delete()
    return redirect('cart_view')


def apply_coupon(request):
    user = _get_user(request)
    if not user: return redirect('user_login')
    if request.method == 'POST':
        code  = request.POST.get('coupon_code', '').strip().upper()
        today = timezone.now().date()
        try:
            Discount.objects.get(code=code, is_active=True,
                                 valid_from__lte=today, valid_until__gte=today)
            request.session['coupon_code'] = code
            messages.success(request, f'Coupon "{code}" applied!')
        except Discount.DoesNotExist:
            request.session.pop('coupon_code', None)
            messages.error(request, 'Invalid or expired coupon code.')
    return redirect('cart_view')


def remove_coupon(request):
    request.session.pop('coupon_code', None)
    messages.info(request, 'Coupon removed.')
    return redirect('cart_view')


# ─── WISHLIST ────────────────────────────────────────────────────────
def add_to_wishlist(request, product_id):
    user = _get_user(request)
    if not user: return redirect('user_login')
    product = get_object_or_404(Product, product_id=product_id)
    _, created = Wishlist.objects.get_or_create(user=user, product=product)
    msg = f'"{product.product_name}" added to wishlist!' if created else 'Already in your wishlist.'
    messages.success(request, msg) if created else messages.info(request, msg)
    return redirect(request.META.get('HTTP_REFERER', 'home'))


def remove_from_wishlist(request, item_id):
    user = _get_user(request)
    if not user: return redirect('user_login')
    Wishlist.objects.filter(id=item_id, user=user).delete()
    messages.success(request, 'Removed from wishlist.')
    return redirect(request.META.get('HTTP_REFERER', 'user_dashboard'))


# ─── CHECKOUT ────────────────────────────────────────────────────────
def checkout(request):
    user = _get_user(request)
    if not user: return redirect('user_login')

    items = Cart.objects.filter(user=user).select_related('product')
    if not items.exists():
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart_view')

    subtotal    = sum(float(i.product.price) * i.quantity for i in items)
    disc_amount = 0
    disc_obj    = None
    code        = request.session.get('coupon_code')

    if code:
        today = timezone.now().date()
        try:
            d = Discount.objects.get(code=code, is_active=True,
                                     valid_from__lte=today, valid_until__gte=today)
            disc_amount = float(d.value) if d.discount_type == 'flat' \
                          else subtotal * float(d.value) / 100
            disc_obj = d
        except Discount.DoesNotExist:
            pass

    # ── Membership charges ──
    from decimal import Decimal
    delivery_charge, platform_fee, is_member = _get_membership_charges(user, subtotal)
    total = max(0, subtotal - disc_amount + float(delivery_charge) + float(platform_fee))

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'COD')
        delivery_addr  = user.get_full_address()

        try:
            with transaction.atomic():
                for item in items:
                    p = Product.objects.select_for_update().get(product_id=item.product.product_id)
                    if p.stock_quantity < item.quantity:
                        raise ValueError(f'Insufficient stock for "{p.product_name}". '
                                         f'Only {p.stock_quantity} units left.')
                    p.stock_quantity -= item.quantity
                    p.save()

                order = Order.objects.create(
                    user=user,
                    subtotal=round(subtotal - disc_amount, 2),
                    delivery_charge=delivery_charge,
                    platform_fee=platform_fee,
                    is_bazar_member=is_member,
                    total_amount=round(total, 2),
                    payment_method=payment_method,
                    payment_status='Paid' if payment_method != 'COD' else 'Pending',
                    order_status='Placed',
                    discount=disc_obj,
                    delivery_address=delivery_addr,
                )
                for item in items:
                    oi = OrderItem.objects.create(
                        order=order, product=item.product,
                        quantity=item.quantity,
                        price_at_purchase=item.product.price,
                    )
                    # ── Create seller order request ──
                    try:
                        from seller.models import SellerOrderRequest
                        SellerOrderRequest.objects.create(
                            order=order,
                            seller=item.product.seller,
                            order_item=oi,
                        )
                    except Exception:
                        pass

                items.delete()
                request.session.pop('coupon_code', None)

                from seller.models import Seller
                for s in Seller.objects.filter(is_active=True):
                    check_and_generate_stock_alerts(s)

                messages.success(request, f'Order placed! ID: {str(order.order_id)[:8].upper()}')
                return redirect('order_success', order_id=order.order_id)

        except ValueError as e:
            messages.error(request, str(e))
            return redirect('cart_view')

    from django.conf import settings
    return render(request, 'store/checkout.html', {
        'items': items,
        'subtotal': round(subtotal, 2),
        'disc_amount': round(disc_amount, 2),
        'delivery_charge': delivery_charge,
        'platform_fee': platform_fee,
        'is_member': is_member,
        'total': round(total, 2),
        'user': user,
        'disc_obj': disc_obj,
        'razorpay_key': settings.RAZORPAY_KEY_ID,
    })


def order_success(request, order_id):
    user  = _get_user(request)
    order = get_object_or_404(Order, order_id=order_id)
    return render(request, 'store/order_success.html', {'order': order, 'user': user})


# ─── ORDER TRACKING ──────────────────────────────────────────────────
def track_order(request, order_id):
    user  = _get_user(request)
    if not user: return redirect('user_login')
    order = get_object_or_404(Order, order_id=order_id, user=user)
    return render(request, 'users/track_order.html', {'order': order, 'user': user})


# ═══════════════════════════════════════════════════════════════
# FEATURE: Product Comparison
# ═══════════════════════════════════════════════════════════════
def compare_products(request):
    ids = request.GET.getlist('ids')
    products = []
    if ids:
        for pid in ids[:3]:  # max 3
            try:
                products.append(Product.objects.get(product_id=pid, is_active=True))
            except Product.DoesNotExist:
                pass
    all_products = Product.objects.filter(is_active=True).order_by('product_name')
    return render(request, 'store/compare.html', {
        'products': products,
        'all_products': all_products,
    })


# ═══════════════════════════════════════════════════════════════
# FEATURE: Price Drop Alert
# ═══════════════════════════════════════════════════════════════
def set_price_alert(request, product_id):
    from django.http import JsonResponse
    user = _get_user(request)
    if not user:
        return JsonResponse({'success': False, 'error': 'Login required'})
    product = get_object_or_404(Product, product_id=product_id)
    target = request.POST.get('target_price')
    try:
        from .models import PriceAlert
        from decimal import Decimal
        alert, created = PriceAlert.objects.update_or_create(
            user=user, product=product,
            defaults={'target_price': Decimal(target), 'is_active': True}
        )
        return JsonResponse({'success': True, 'message': f'Alert set for ₹{target}!'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def my_price_alerts(request):
    user = _get_user(request)
    if not user:
        return redirect('user_login')
    from .models import PriceAlert
    alerts = PriceAlert.objects.filter(user=user, is_active=True).select_related('product')
    # Check if any alerts triggered
    triggered = []
    for alert in alerts:
        if alert.product.price <= alert.target_price:
            triggered.append(alert)
    return render(request, 'store/price_alerts.html', {
        'alerts': alerts, 'triggered': triggered
    })


def delete_price_alert(request, alert_id):
    user = _get_user(request)
    if not user:
        return redirect('user_login')
    from .models import PriceAlert
    try:
        PriceAlert.objects.get(id=alert_id, user=user).delete()
        messages.success(request, 'Price alert removed.')
    except:
        pass
    return redirect('my_price_alerts')


# ═══════════════════════════════════════════════════════════════
# FEATURE: Recently Viewed (track in product_detail)
# ═══════════════════════════════════════════════════════════════
def _track_recently_viewed(user, product):
    if not user:
        return
    try:
        from .models import RecentlyViewed
        rv, _ = RecentlyViewed.objects.update_or_create(
            user=user, product=product,
            defaults={}
        )
        # Keep only last 10
        old_ids = RecentlyViewed.objects.filter(user=user).order_by('-viewed_at').values_list('id', flat=True)[10:]
        RecentlyViewed.objects.filter(id__in=list(old_ids)).delete()
    except:
        pass


# ═══════════════════════════════════════════════════════════════
# FEATURE: Advanced Search
# ═══════════════════════════════════════════════════════════════
def advanced_search(request):
    query    = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    min_rating = request.GET.get('min_rating', '')
    sort_by  = request.GET.get('sort', 'newest')

    products = Product.objects.filter(is_active=True, seller__is_blacklisted=False)

    if query:
        products = products.filter(
            Q(product_name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__icontains=query)
        )
    if category:
        products = products.filter(category=category)
    if min_price:
        try: products = products.filter(price__gte=float(min_price))
        except: pass
    if max_price:
        try: products = products.filter(price__lte=float(max_price))
        except: pass

    # Sort
    sort_map = {
        'newest':    '-created_at',
        'price_asc': 'price',
        'price_desc':'-price',
        'name':      'product_name',
    }
    products = products.order_by(sort_map.get(sort_by, '-created_at'))

    # Rating filter (post-query since it's a property)
    if min_rating:
        try:
            min_r = float(min_rating)
            products = [p for p in products if p.average_rating >= min_r]
        except:
            pass

    user = _get_user(request)
    return render(request, 'store/search.html', {
        'products': products,
        'query': query, 'category': category,
        'min_price': min_price, 'max_price': max_price,
        'min_rating': min_rating, 'sort_by': sort_by,
        'all_categories': CATEGORY_CHOICES,
        'result_count': len(products) if isinstance(products, list) else products.count(),
    })


# ═══════════════════════════════════════════════════════════════
# BAZAR MEMBERSHIP — Pricing Helper
# ═══════════════════════════════════════════════════════════════

def _get_membership_charges(user, subtotal):
    """Returns (delivery_charge, platform_fee, is_member)"""
    from decimal import Decimal
    is_member = False
    try:
        from users.models import BazarMembership
        m = BazarMembership.objects.get(user=user)
        is_member = m.is_valid()
    except Exception:
        pass

    if is_member:
        delivery_charge = Decimal('0.00')   # FREE for members
        platform_fee    = Decimal('0.00')   # No platform fee
    else:
        # Non-member: ₹50 delivery if order < ₹500
        delivery_charge = Decimal('0.00') if subtotal >= 500 else Decimal('50.00')
        platform_fee    = Decimal('5.00')   # Always ₹5 platform fee

    return delivery_charge, platform_fee, is_member


# ═══════════════════════════════════════════════════════════════
# BILL / INVOICE
# ═══════════════════════════════════════════════════════════════

def order_bill(request, order_id):
    user  = _get_user(request)
    order = get_object_or_404(Order, order_id=order_id, user=user)
    items = order.items.select_related('product', 'product__seller')
    # Group items by seller
    sellers = {}
    for item in items:
        sid = str(item.product.seller.seller_id)
        if sid not in sellers:
            sellers[sid] = {'seller': item.product.seller, 'items': []}
        sellers[sid]['items'].append(item)
    return render(request, 'store/bill.html', {
        'order': order,
        'items': items,
        'sellers': list(sellers.values()),
        'user': user,
    })


def order_bill_pdf(request, order_id):
    """Generate professional PDF invoice"""
    user  = _get_user(request)
    order = get_object_or_404(Order, order_id=order_id, user=user)
    items = order.items.select_related('product', 'product__seller')

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        import io
        from django.http import HttpResponse
    except ImportError:
        messages.error(request, 'PDF generation requires reportlab. Run: pip install reportlab')
        return redirect('order_bill', order_id=order_id)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=1.5*cm, leftMargin=1.5*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    story  = []

    # Styles
    brand_style = ParagraphStyle('brand', fontSize=24, textColor=colors.HexColor('#2874F0'),
                                  fontName='Helvetica-Bold', alignment=TA_LEFT, spaceAfter=2)
    tagline_style = ParagraphStyle('tagline', fontSize=9, textColor=colors.HexColor('#FB641B'),
                                    fontName='Helvetica', alignment=TA_LEFT, spaceAfter=4)
    h2 = ParagraphStyle('h2', fontSize=13, textColor=colors.HexColor('#2874F0'),
                          fontName='Helvetica-Bold', spaceBefore=12, spaceAfter=6)
    normal = ParagraphStyle('norm', fontSize=9, fontName='Helvetica', spaceAfter=3)
    small  = ParagraphStyle('sm', fontSize=8, fontName='Helvetica', textColor=colors.grey)
    center = ParagraphStyle('center', fontSize=9, fontName='Helvetica', alignment=TA_CENTER)

    # ── Header ──
    header_data = [[
        Paragraph('<b>🛒 OnlineBazar</b>', brand_style),
        Paragraph(f'<b>TAX INVOICE</b>', ParagraphStyle('inv', fontSize=16, textColor=colors.white,
                  fontName='Helvetica-Bold', alignment=TA_RIGHT))
    ]]
    header_table = Table(header_data, colWidths=[9*cm, 9*cm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (1,0), (1,0), colors.HexColor('#2874F0')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (1,0), (1,0), 10),
        ('BOTTOMPADDING', (1,0), (1,0), 10),
        ('RIGHTPADDING', (1,0), (1,0), 10),
    ]))
    story.append(header_table)
    story.append(Paragraph('India\'s Growing Marketplace', tagline_style))
    story.append(Spacer(1, 2))

    if order.is_bazar_member:
        story.append(Paragraph('⭐ Bazar Prime Member Order — Free Delivery + No Platform Fee',
                               ParagraphStyle('prime', fontSize=9, textColor=colors.HexColor('#FB641B'),
                                               fontName='Helvetica-Bold', spaceAfter=4)))

    story.append(HRFlowable(width='100%', thickness=2, color=colors.HexColor('#FB641B')))
    story.append(Spacer(1, 8))

    # ── Order Info + Addresses ──
    seller = items.first().product.seller if items.exists() else None

    addr_data = [
        [
            Paragraph('<b>FROM (Seller)</b>', ParagraphStyle('lbl', fontSize=8, textColor=colors.grey, fontName='Helvetica-Bold')),
            Paragraph('', normal),
            Paragraph('<b>TO (Ship To)</b>', ParagraphStyle('lbl', fontSize=8, textColor=colors.grey, fontName='Helvetica-Bold')),
        ],
        [
            Paragraph(f'<b>{seller.name if seller else "OnlineBazar"}</b>', normal),
            Paragraph('', normal),
            Paragraph(f'<b>{user.name}</b>', normal),
        ],
        [
            Paragraph(f'{seller.address_line if seller else ""}, {seller.district if seller else ""}<br/>{seller.state if seller else ""} — {seller.pincode if seller else ""}', normal),
            Paragraph('', normal),
            Paragraph(f'{user.address_line}, {user.house_no}<br/>{user.district}, {user.state} — {user.pincode}', normal),
        ],
        [
            Paragraph(f'📧 {seller.email if seller else ""}', small),
            Paragraph('', normal),
            Paragraph(f'📱 {user.phone_number}', small),
        ],
    ]
    addr_table = Table(addr_data, colWidths=[8*cm, 2*cm, 8*cm])
    addr_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#F8F9FF')),
        ('BACKGROUND', (2,0), (2,-1), colors.HexColor('#FFF8F0')),
        ('BOX', (0,0), (0,-1), 0.5, colors.lightgrey),
        ('BOX', (2,0), (2,-1), 0.5, colors.lightgrey),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(addr_table)
    story.append(Spacer(1, 6))

    # Order meta
    meta_data = [['Order ID', f'#{str(order.order_id)[:12].upper()}',
                  'Order Date', order.order_date.strftime('%d %b %Y, %I:%M %p'),
                  'Status', order.order_status]]
    meta_table = Table(meta_data, colWidths=[2.5*cm, 4.5*cm, 2.5*cm, 4*cm, 2*cm, 3*cm])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#2874F0')),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.white),
        ('FONTNAME', (0,0), (0,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # ── Products Table ──
    story.append(Paragraph('📦 Order Items', h2))
    prod_data = [['#', 'Product Name', 'Seller', 'Qty', 'Unit Price', 'Subtotal']]
    for i, item in enumerate(items, 1):
        prod_data.append([
            str(i),
            item.product.product_name[:40],
            item.product.seller.name[:20],
            str(item.quantity),
            f'₹{item.price_at_purchase:,.2f}',
            f'₹{item.subtotal:,.2f}',
        ])
    prod_table = Table(prod_data, colWidths=[0.8*cm, 6*cm, 3.5*cm, 1.2*cm, 2.5*cm, 2.5*cm])
    prod_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2874F0')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F1F3F6')]),
        ('GRID', (0,0), (-1,-1), 0.4, colors.lightgrey),
        ('ALIGN', (3,0), (-1,-1), 'CENTER'),
        ('ALIGN', (4,0), (-1,-1), 'RIGHT'),
        ('ALIGN', (5,0), (-1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(prod_table)
    story.append(Spacer(1, 10))

    # ── Bill Summary ──
    story.append(Paragraph('💰 Bill Summary', h2))
    subtotal_val = float(order.subtotal) if order.subtotal else sum(float(i.subtotal) for i in items)
    delivery     = float(order.delivery_charge)
    platform     = float(order.platform_fee)
    total        = float(order.total_amount)

    bill_data = [
        ['', 'Product Subtotal', f'₹{subtotal_val:,.2f}'],
        ['', 'Delivery Charges', '₹0.00 (FREE — Bazar Prime)' if order.is_bazar_member else (f'₹{delivery:,.2f}' if delivery > 0 else '₹0.00 (Free above ₹500)')],
        ['', 'Platform Fee', '₹0.00 (Bazar Prime benefit)' if order.is_bazar_member else f'₹{platform:,.2f}'],
        ['', 'Discount', '₹0.00'],
        ['TOTAL', '', f'₹{total:,.2f}'],
    ]
    bill_table = Table(bill_data, colWidths=[3*cm, 7*cm, 8*cm])
    bill_table.setStyle(TableStyle([
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ALIGN', (2,0), (2,-1), 'RIGHT'),
        ('LINEABOVE', (0,-1), (-1,-1), 1.5, colors.HexColor('#2874F0')),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#2874F0')),
        ('TEXTCOLOR', (0,-1), (-1,-1), colors.white),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,-1), (-1,-1), 11),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(bill_table)

    # ── Footer ──
    story.append(Spacer(1, 16))
    story.append(HRFlowable(width='100%', thickness=1, color=colors.lightgrey))
    story.append(Paragraph(
        'Thank you for shopping with OnlineBazar! | Founders: Ankit Sharma & Niraj Kumar',
        ParagraphStyle('footer', fontSize=8, textColor=colors.grey, alignment=TA_CENTER, spaceBefore=6)
    ))
    story.append(Paragraph(
        'This is a computer-generated invoice and does not require a signature.',
        ParagraphStyle('footer2', fontSize=7, textColor=colors.lightgrey, alignment=TA_CENTER)
    ))

    doc.build(story)
    buffer.seek(0)
    from django.http import HttpResponse
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="OnlineBazar_Invoice_{str(order.order_id)[:8].upper()}.pdf"'
    return response


# ═══════════════════════════════════════════════════════════════
# PRODUCT RETURN SYSTEM
# ═══════════════════════════════════════════════════════════════

def request_return(request, order_item_id):
    """User raises a return request for a delivered order item"""
    user = _get_user(request)
    if not user:
        return redirect('user_login')

    from .models import ReturnRequest, OrderItem as OI
    order_item = get_object_or_404(OI, id=order_item_id, order__user=user)
    order      = order_item.order

    # Only delivered orders can be returned
    if order.order_status != 'Delivered':
        messages.error(request, 'Returns can only be raised for delivered orders.')
        return redirect('order_history')

    # Check 7 day window
    from django.utils import timezone as tz
    days_since = (tz.now() - order.order_date).days
    if days_since > 7:
        messages.error(request, f'Return window expired. Returns allowed within 7 days of delivery. ({days_since} days ago)')
        return redirect('order_history')

    # Check if already requested
    existing = ReturnRequest.objects.filter(order_item=order_item).first()
    if existing:
        messages.info(request, f'Return already raised. Status: {existing.get_status_display()}')
        return redirect('my_returns')

    if request.method == 'POST':
        reason      = request.POST.get('reason', '')
        description = request.POST.get('description', '').strip()
        return_type = request.POST.get('return_type', 'return')
        image       = request.FILES.get('product_image')

        if not reason or not description:
            messages.error(request, 'Please fill all required fields.')
            return render(request, 'store/return_request.html', {
                'order_item': order_item, 'order': order,
                'reasons': ReturnRequest.REASON_CHOICES,
                'types': ReturnRequest.TYPE_CHOICES,
                'days_since': days_since,
            })

        rr = ReturnRequest.objects.create(
            user=user, order=order, order_item=order_item,
            return_type=return_type, reason=reason,
            description=description,
            refund_amount=order_item.price_at_purchase,
        )
        if image:
            rr.product_image = image
            rr.save(update_fields=['product_image'])

        messages.success(request, f'✅ Return request raised! ID: #{str(rr.id)[:8].upper()}. We will review within 24-48 hours.')
        return redirect('my_returns')

    return render(request, 'store/return_request.html', {
        'order_item': order_item, 'order': order,
        'reasons': ReturnRequest.REASON_CHOICES,
        'types':   ReturnRequest.TYPE_CHOICES,
        'days_since': days_since,
    })


def my_returns(request):
    """User views all their return requests"""
    user = _get_user(request)
    if not user:
        return redirect('user_login')

    from .models import ReturnRequest
    returns = ReturnRequest.objects.filter(user=user).select_related(
        'order', 'order_item', 'order_item__product'
    )
    steps = [
        ('pending',   'Submitted'),
        ('approved',  'Approved'),
        ('picked_up', 'Picked Up'),
        ('refunded',  'Refunded'),
    ]
    return render(request, 'store/my_returns.html', {'returns': returns, 'steps': steps})


def cancel_return(request, return_id):
    """User cancels a pending return"""
    user = _get_user(request)
    if not user:
        return redirect('user_login')

    from .models import ReturnRequest
    try:
        rr = ReturnRequest.objects.get(id=return_id, user=user, status='pending')
        rr.delete()
        messages.success(request, 'Return request cancelled.')
    except ReturnRequest.DoesNotExist:
        messages.error(request, 'Cannot cancel this return request.')
    return redirect('my_returns')
