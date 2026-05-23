import hashlib
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from store.models import (Product, Cart, Wishlist, Order, OrderItem,
                          Review, Discount, CATEGORY_CHOICES)
from users.models import UserProfile, BazarMembership
from seller.models import Seller, SellerOrderRequest, DELIVERY_PARTNERS
from ml.recommendations import get_recommendations
from ml.stock_alert import check_and_generate_stock_alerts

from .serializers import (
    ProductSerializer, ReviewSerializer, UserProfileSerializer,
    UserRegisterSerializer, SellerSerializer, SellerRegisterSerializer,
    OrderSerializer, CartSerializer, WishlistSerializer,
    MembershipSerializer, SellerOrderRequestSerializer,
)


def hash_password(raw):
    return hashlib.sha256(raw.encode()).hexdigest()


def simple_tokens(payload: dict):
    """Simple JWT-like tokens without Django User model dependency."""
    import jwt, datetime
    from django.conf import settings
    secret = settings.SECRET_KEY
    now = datetime.datetime.utcnow()
    access_payload = {**payload, 'exp': now + datetime.timedelta(hours=24), 'type': 'access'}
    refresh_payload = {**payload, 'exp': now + datetime.timedelta(days=30), 'type': 'refresh'}
    return {
        'access': jwt.encode(access_payload, secret, algorithm='HS256'),
        'refresh': jwt.encode(refresh_payload, secret, algorithm='HS256'),
    }


def decode_token(request):
    """Decode JWT from Authorization header."""
    import jwt
    from django.conf import settings
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    token = auth.split(' ', 1)[1]
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
    except Exception:
        return None


def get_user_from_token(request):
    payload = decode_token(request)
    if not payload or payload.get('role') != 'user':
        return None
    try:
        return UserProfile.objects.get(user_id=payload['user_id'])
    except UserProfile.DoesNotExist:
        return None


def get_seller_from_token(request):
    payload = decode_token(request)
    if not payload or payload.get('role') != 'seller':
        return None
    try:
        return Seller.objects.get(seller_id=payload['seller_id'])
    except Seller.DoesNotExist:
        return None


# ─── AUTH ─────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def user_register(request):
    ser = UserRegisterSerializer(data=request.data)
    if not ser.is_valid():
        return Response({'errors': ser.errors}, status=400)
    d = ser.validated_data
    if UserProfile.objects.filter(email=d['email']).exists():
        return Response({'error': 'Email already registered.'}, status=400)
    user = UserProfile.objects.create(
        name=d['name'], email=d['email'], phone_number=d['phone_number'],
        gender=d['gender'], password=hash_password(d['password']),
        address_line=d['address_line'], house_no=d['house_no'],
        nearby_landmark=d.get('nearby_landmark', ''),
        district=d['district'], state=d['state'], pincode=d['pincode'],
    )
    tokens = simple_tokens({'user_id': str(user.user_id), 'role': 'user', 'name': user.name})
    return Response({'user': UserProfileSerializer(user).data, **tokens}, status=201)


@api_view(['POST'])
@permission_classes([AllowAny])
def user_login(request):
    email = request.data.get('email', '')
    password = request.data.get('password', '')
    try:
        user = UserProfile.objects.get(email=email, password=hash_password(password))
        if not user.is_active:
            return Response({'error': 'Account suspended.'}, status=403)
        tokens = simple_tokens({'user_id': str(user.user_id), 'role': 'user', 'name': user.name})
        return Response({'user': UserProfileSerializer(user).data, **tokens})
    except UserProfile.DoesNotExist:
        return Response({'error': 'Invalid credentials.'}, status=401)


@api_view(['POST'])
@permission_classes([AllowAny])
def seller_register(request):
    ser = SellerRegisterSerializer(data=request.data)
    if not ser.is_valid():
        return Response({'errors': ser.errors}, status=400)
    d = ser.validated_data
    if Seller.objects.filter(email=d['email']).exists():
        return Response({'error': 'Email already registered.'}, status=400)
    seller = Seller.objects.create(
        name=d['name'], email=d['email'], phone_number=d['phone_number'],
        password=hash_password(d['password']),
        address_line=d['address_line'], district=d['district'],
        state=d['state'], pincode=d['pincode'],
    )
    tokens = simple_tokens({'seller_id': str(seller.seller_id), 'role': 'seller', 'name': seller.name})
    return Response({'seller': SellerSerializer(seller).data, **tokens}, status=201)


@api_view(['POST'])
@permission_classes([AllowAny])
def seller_login(request):
    email = request.data.get('email', '')
    password = request.data.get('password', '')
    try:
        seller = Seller.objects.get(email=email, password=hash_password(password))
        if seller.is_blacklisted:
            return Response({'error': 'Account blacklisted.'}, status=403)
        tokens = simple_tokens({'seller_id': str(seller.seller_id), 'role': 'seller', 'name': seller.name})
        return Response({'seller': SellerSerializer(seller).data, **tokens})
    except Seller.DoesNotExist:
        return Response({'error': 'Invalid credentials.'}, status=401)


@api_view(['GET'])
def user_me(request):
    user = get_user_from_token(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=401)
    return Response(UserProfileSerializer(user).data)


@api_view(['GET'])
def seller_me(request):
    seller = get_seller_from_token(request)
    if not seller:
        return Response({'error': 'Unauthorized'}, status=401)
    return Response(SellerSerializer(seller).data)


# ─── PRODUCTS ─────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def product_list(request):
    products = Product.objects.filter(is_active=True, seller__is_blacklisted=False)
    q = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    sort = request.GET.get('sort', 'newest')

    if q:
        products = products.filter(
            Q(product_name__icontains=q) | Q(description__icontains=q) | Q(category__icontains=q)
        )
    if category:
        products = products.filter(category=category)
    if min_price:
        try: products = products.filter(price__gte=float(min_price))
        except: pass
    if max_price:
        try: products = products.filter(price__lte=float(max_price))
        except: pass

    sort_map = {'newest': '-created_at', 'price_asc': 'price', 'price_desc': '-price', 'name': 'product_name'}
    products = products.order_by(sort_map.get(sort, '-created_at'))

    # Pagination
    from django.core.paginator import Paginator
    page = request.GET.get('page', 1)
    paginator = Paginator(products, 12)
    try:
        page_obj = paginator.page(page)
    except:
        page_obj = paginator.page(1)

    ser = ProductSerializer(page_obj.object_list, many=True, context={'request': request})
    return Response({
        'results': ser.data,
        'count': paginator.count,
        'num_pages': paginator.num_pages,
        'current_page': page_obj.number,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def product_detail(request, product_id):
    try:
        product = Product.objects.get(product_id=product_id, is_active=True)
    except Product.DoesNotExist:
        return Response({'error': 'Not found'}, status=404)
    reviews = ReviewSerializer(product.reviews.all(), many=True).data
    related = ProductSerializer(
        Product.objects.filter(category=product.category, is_active=True).exclude(product_id=product_id)[:4],
        many=True, context={'request': request}
    ).data
    return Response({
        'product': ProductSerializer(product, context={'request': request}).data,
        'reviews': reviews,
        'related': related,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def categories(request):
    return Response([{'value': v, 'label': l} for v, l in CATEGORY_CHOICES])


@api_view(['GET'])
@permission_classes([AllowAny])
def featured_products(request):
    products = Product.objects.filter(is_active=True, seller__is_blacklisted=False).order_by('?')[:8]
    return Response(ProductSerializer(products, many=True, context={'request': request}).data)


@api_view(['GET'])
def recommended_products(request):
    user = get_user_from_token(request)
    if not user:
        return Response([])
    recs = get_recommendations(str(user.user_id))
    return Response(ProductSerializer(recs, many=True, context={'request': request}).data)


# ─── REVIEWS ──────────────────────────────────────────────────────────────

@api_view(['POST'])
def add_review(request, product_id):
    user = get_user_from_token(request)
    if not user:
        return Response({'error': 'Login required'}, status=401)
    try:
        product = Product.objects.get(product_id=product_id)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=404)
    if Review.objects.filter(user=user, product=product).exists():
        return Response({'error': 'Already reviewed'}, status=400)
    review = Review.objects.create(
        user=user, product=product,
        rating=int(request.data.get('rating', 5)),
        review_text=request.data.get('review_text', '')
    )
    return Response(ReviewSerializer(review).data, status=201)


# ─── CART ─────────────────────────────────────────────────────────────────

@api_view(['GET'])
def cart_list(request):
    user = get_user_from_token(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=401)
    items = Cart.objects.filter(user=user).select_related('product')
    return Response(CartSerializer(items, many=True, context={'request': request}).data)


@api_view(['POST'])
def cart_add(request):
    user = get_user_from_token(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=401)
    product_id = request.data.get('product_id')
    try:
        product = Product.objects.get(product_id=product_id, is_active=True)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=404)
    if product.stock_quantity == 0:
        return Response({'error': 'Out of stock'}, status=400)
    item, created = Cart.objects.get_or_create(user=user, product=product)
    if not created:
        if item.quantity < product.stock_quantity:
            item.quantity += 1
            item.save()
        else:
            return Response({'error': f'Only {product.stock_quantity} available'}, status=400)
    return Response({'message': 'Added to cart', 'quantity': item.quantity})


@api_view(['PATCH'])
def cart_update(request, cart_id):
    user = get_user_from_token(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=401)
    try:
        item = Cart.objects.get(id=cart_id, user=user)
    except Cart.DoesNotExist:
        return Response({'error': 'Not found'}, status=404)
    action = request.data.get('action')
    if action == 'increase' and item.quantity < item.product.stock_quantity:
        item.quantity += 1; item.save()
    elif action == 'decrease':
        if item.quantity > 1: item.quantity -= 1; item.save()
        else: item.delete(); return Response({'message': 'Removed'})
    elif action == 'remove':
        item.delete(); return Response({'message': 'Removed'})
    return Response({'quantity': item.quantity})


# ─── WISHLIST ─────────────────────────────────────────────────────────────

@api_view(['GET'])
def wishlist_list(request):
    user = get_user_from_token(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=401)
    items = Wishlist.objects.filter(user=user).select_related('product')
    return Response(WishlistSerializer(items, many=True, context={'request': request}).data)


@api_view(['POST'])
def wishlist_toggle(request):
    user = get_user_from_token(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=401)
    product_id = request.data.get('product_id')
    try:
        product = Product.objects.get(product_id=product_id)
    except Product.DoesNotExist:
        return Response({'error': 'Not found'}, status=404)
    item, created = Wishlist.objects.get_or_create(user=user, product=product)
    if not created:
        item.delete()
        return Response({'wishlisted': False})
    return Response({'wishlisted': True})


# ─── COUPON ───────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def apply_coupon(request):
    code = request.data.get('code', '').strip().upper()
    today = timezone.now().date()
    try:
        d = Discount.objects.get(code=code, is_active=True,
                                 valid_from__lte=today, valid_until__gte=today)
        return Response({'valid': True, 'discount_type': d.discount_type, 'value': float(d.value)})
    except Discount.DoesNotExist:
        return Response({'valid': False, 'error': 'Invalid or expired coupon'}, status=400)


# ─── CHECKOUT / ORDERS ────────────────────────────────────────────────────

def _get_membership_charges(user, subtotal):
    from decimal import Decimal
    is_member = False
    try:
        m = BazarMembership.objects.get(user=user)
        is_member = m.is_valid()
    except Exception:
        pass
    if is_member:
        return Decimal('0'), Decimal('0'), True
    return (Decimal('0') if subtotal >= 500 else Decimal('50')), Decimal('5'), False


@api_view(['POST'])
def checkout(request):
    user = get_user_from_token(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=401)

    items = Cart.objects.filter(user=user).select_related('product')
    if not items.exists():
        return Response({'error': 'Cart is empty'}, status=400)

    payment_method = request.data.get('payment_method', 'COD')
    coupon_code = request.data.get('coupon_code', '').strip().upper()

    subtotal = sum(float(i.product.price) * i.quantity for i in items)
    disc_amount = 0
    disc_obj = None

    if coupon_code:
        today = timezone.now().date()
        try:
            d = Discount.objects.get(code=coupon_code, is_active=True,
                                     valid_from__lte=today, valid_until__gte=today)
            disc_amount = float(d.value) if d.discount_type == 'flat' else subtotal * float(d.value) / 100
            disc_obj = d
        except Discount.DoesNotExist:
            pass

    delivery_charge, platform_fee, is_member = _get_membership_charges(user, subtotal)
    total = max(0, subtotal - disc_amount + float(delivery_charge) + float(platform_fee))

    try:
        with transaction.atomic():
            for item in items:
                p = Product.objects.select_for_update().get(product_id=item.product.product_id)
                if p.stock_quantity < item.quantity:
                    raise ValueError(f'Insufficient stock for "{p.product_name}".')
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
                delivery_address=user.get_full_address(),
            )
            for item in items:
                oi = OrderItem.objects.create(
                    order=order, product=item.product,
                    quantity=item.quantity,
                    price_at_purchase=item.product.price,
                )
                try:
                    SellerOrderRequest.objects.create(
                        order=order, seller=item.product.seller, order_item=oi)
                except Exception:
                    pass

            items.delete()
            for s in Seller.objects.filter(is_active=True):
                check_and_generate_stock_alerts(s)

    except ValueError as e:
        return Response({'error': str(e)}, status=400)

    return Response(OrderSerializer(order, context={'request': request}).data, status=201)


@api_view(['GET'])
def order_list(request):
    user = get_user_from_token(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=401)
    orders = Order.objects.filter(user=user).prefetch_related('items__product')
    return Response(OrderSerializer(orders, many=True, context={'request': request}).data)


@api_view(['GET'])
def order_detail(request, order_id):
    user = get_user_from_token(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=401)
    try:
        order = Order.objects.get(order_id=order_id, user=user)
    except Order.DoesNotExist:
        return Response({'error': 'Not found'}, status=404)
    return Response(OrderSerializer(order, context={'request': request}).data)


# ─── MEMBERSHIP ───────────────────────────────────────────────────────────

@api_view(['GET'])
def membership_status(request):
    user = get_user_from_token(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=401)
    try:
        m = BazarMembership.objects.get(user=user)
        return Response(MembershipSerializer(m).data)
    except BazarMembership.DoesNotExist:
        return Response({'has_membership': False})


@api_view(['POST'])
def join_membership(request):
    user = get_user_from_token(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=401)
    plan = request.data.get('plan', 'monthly')
    import datetime
    from decimal import Decimal
    amount = Decimal('199') if plan == 'monthly' else Decimal('999')
    days = 30 if plan == 'monthly' else 365
    end_date = timezone.now().date() + datetime.timedelta(days=days)
    m, _ = BazarMembership.objects.update_or_create(
        user=user,
        defaults={'plan': plan, 'status': 'active', 'end_date': end_date, 'amount_paid': amount}
    )
    return Response(MembershipSerializer(m).data, status=201)


# ─── SELLER DASHBOARD ─────────────────────────────────────────────────────

@api_view(['GET'])
def seller_products(request):
    seller = get_seller_from_token(request)
    if not seller:
        return Response({'error': 'Unauthorized'}, status=401)
    products = Product.objects.filter(seller=seller)
    return Response(ProductSerializer(products, many=True, context={'request': request}).data)


@api_view(['POST'])
def seller_add_product(request):
    seller = get_seller_from_token(request)
    if not seller:
        return Response({'error': 'Unauthorized'}, status=401)
    data = request.data
    product = Product.objects.create(
        seller=seller,
        product_name=data.get('product_name'),
        category=data.get('category'),
        price=data.get('price'),
        description=data.get('description', ''),
        stock_quantity=data.get('stock_quantity', 0),
        product_image=request.FILES.get('product_image'),
    )
    return Response(ProductSerializer(product, context={'request': request}).data, status=201)


@api_view(['PATCH', 'DELETE'])
def seller_product_detail(request, product_id):
    seller = get_seller_from_token(request)
    if not seller:
        return Response({'error': 'Unauthorized'}, status=401)
    try:
        product = Product.objects.get(product_id=product_id, seller=seller)
    except Product.DoesNotExist:
        return Response({'error': 'Not found'}, status=404)

    if request.method == 'DELETE':
        product.is_active = False
        product.save()
        return Response({'message': 'Product deactivated'})

    for field in ['product_name', 'category', 'price', 'description', 'stock_quantity']:
        if field in request.data:
            setattr(product, field, request.data[field])
    if 'product_image' in request.FILES:
        product.product_image = request.FILES['product_image']
    product.save()
    return Response(ProductSerializer(product, context={'request': request}).data)


@api_view(['GET'])
def seller_orders(request):
    seller = get_seller_from_token(request)
    if not seller:
        return Response({'error': 'Unauthorized'}, status=401)
    reqs = SellerOrderRequest.objects.filter(seller=seller).select_related(
        'order', 'order__user', 'order_item', 'order_item__product')
    return Response(SellerOrderRequestSerializer(reqs, many=True).data)


@api_view(['PATCH'])
def seller_order_action(request, req_id):
    seller = get_seller_from_token(request)
    if not seller:
        return Response({'error': 'Unauthorized'}, status=401)
    try:
        req = SellerOrderRequest.objects.get(id=req_id, seller=seller)
    except SellerOrderRequest.DoesNotExist:
        return Response({'error': 'Not found'}, status=404)

    action = request.data.get('action')
    if action == 'accept':
        req.status = 'accepted'
        req.accepted_at = timezone.now()
    elif action == 'reject':
        req.status = 'rejected'
        req.rejection_reason = request.data.get('reason', '')
    elif action == 'ship':
        req.status = 'shipped'
        req.delivery_partner = request.data.get('delivery_partner')
        req.tracking_id = request.data.get('tracking_id', '')
        req.shipped_at = timezone.now()
        req.order.order_status = 'Shipped'
        req.order.save()
    req.save()
    return Response(SellerOrderRequestSerializer(req).data)


@api_view(['GET'])
def seller_dashboard_stats(request):
    seller = get_seller_from_token(request)
    if not seller:
        return Response({'error': 'Unauthorized'}, status=401)
    products = Product.objects.filter(seller=seller)
    orders = SellerOrderRequest.objects.filter(seller=seller)
    total_revenue = sum(
        float(r.order_item.price_at_purchase) * r.order_item.quantity
        for r in orders.filter(status__in=['shipped', 'delivered'])
    )
    return Response({
        'total_products': products.count(),
        'active_products': products.filter(is_active=True).count(),
        'pending_orders': orders.filter(status='pending').count(),
        'total_orders': orders.count(),
        'total_revenue': round(total_revenue, 2),
        'low_stock': products.filter(stock_quantity__lte=10, is_active=True).count(),
    })


# ─── PINCODE LOOKUP ───────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def pincode_lookup(request):
    import json, urllib.request
    pincode = request.GET.get('pincode', '').strip()
    if not (pincode.isdigit() and len(pincode) == 6):
        return Response({'success': False, 'error': 'Invalid pincode'}, status=400)
    try:
        url = f'https://api.postalpincode.in/pincode/{pincode}'
        req = urllib.request.Request(url, headers={'User-Agent': 'OnlineBazar/1.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        if data and data[0].get('Status') == 'Success':
            post = data[0]['PostOffice'][0]
            return Response({'success': True, 'district': post.get('District', ''),
                             'state': post.get('State', ''), 'area': post.get('Name', '')})
        return Response({'success': False, 'error': 'Not found'}, status=404)
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)
