from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
import re

from .models import UserProfile
from store.models import Order, Wishlist, Review
from ml.recommendations import get_recommendations


def user_register(request):
    if request.session.get('user_id'):
        return redirect('home')
    if request.method == 'POST':
        d = request.POST
        errors = []
        email = d.get('email', '').lower().strip()
        phone = d.get('phone_number', '').strip()
        if not re.match(r'^\d{10}$', phone):
            errors.append('Phone number must be exactly 10 digits.')
        if not re.match(r'^\d{6}$', d.get('pincode', '')):
            errors.append('Pincode must be exactly 6 digits.')
        if d.get('password') != d.get('confirm_password'):
            errors.append('Passwords do not match.')
        if len(d.get('password', '')) < 6:
            errors.append('Password must be at least 6 characters.')
        # Check email across both buyer and seller tables
        from seller.models import Seller
        if UserProfile.objects.filter(email=email).exists() or Seller.objects.filter(email=email).exists():
            errors.append('This email address is already registered. Please use a different email.')
        # Check phone across both buyer and seller tables
        if re.match(r'^\d{10}$', phone):
            if UserProfile.objects.filter(phone_number=phone).exists() or Seller.objects.filter(phone_number=phone).exists():
                errors.append('This phone number is already registered. Please use a different phone number.')
        if errors:
            for e in errors: messages.error(request, e)
            return render(request, 'users/register.html', {'data': d})

        UserProfile.objects.create(
            name=d['name'].strip(), gender=d['gender'],
            email=d['email'].lower().strip(),
            phone_number=d['phone_number'].strip(),
            password=make_password(d['password']),
            address_line=d['address_line'].strip(),
            nearby_landmark=d.get('nearby_landmark', '').strip(),
            house_no=d['house_no'].strip(),
            district=d['district'].strip(),
            state=d['state'].strip(),
            pincode=d['pincode'].strip(),
        )
        messages.success(request, 'Account created successfully! Please login.')
        return redirect('user_login')
    return render(request, 'users/register.html')


def user_login(request):
    if request.session.get('user_id'):
        return redirect('home')
    if request.method == 'POST':
        email    = request.POST.get('email', '').lower().strip()
        password = request.POST.get('password', '')
        try:
            user = UserProfile.objects.get(email=email)
            if not user.is_active:
                return render(request, 'users/login.html', {
                    'suspended': True,
                    'suspension_reason': user.suspension_reason or 'No reason provided.',
                    'admin_email': 'admin@ecommerce.com',
                })
            if check_password(password, user.password):
                request.session['user_id']   = str(user.user_id)
                request.session['user_name'] = user.name
                request.session['role']      = 'user'
                # Set prime badge in session
                try:
                    from .models import BazarMembership
                    m = BazarMembership.objects.get(user=user)
                    request.session['is_prime'] = m.is_valid()
                except Exception:
                    request.session['is_prime'] = False
                messages.success(request, f'Welcome back, {user.name}!')
                return redirect('home')
            messages.error(request, 'Incorrect password.')
        except UserProfile.DoesNotExist:
            messages.error(request, 'No account found with this email.')
    return render(request, 'users/login.html')


def user_logout(request):
    request.session.flush()
    messages.success(request, 'Logged out successfully.')
    return redirect('home')


def user_dashboard(request):
    if not request.session.get('user_id') or request.session.get('role') != 'user':
        return redirect('user_login')
    user     = get_object_or_404(UserProfile, user_id=request.session['user_id'])
    orders   = Order.objects.filter(user=user).order_by('-order_date')
    active   = orders.exclude(order_status__in=['Delivered', 'Cancelled'])
    wishlist = Wishlist.objects.filter(user=user).select_related('product')
    reviews  = Review.objects.filter(user=user).select_related('product')
    recommended = get_recommendations(str(user.user_id))

    # ── Chart Data — last 6 months spending ──
    from django.db.models import Sum
    import json
    chart_labels = []
    chart_spending = []
    chart_orders = []
    for i in range(5, -1, -1):
        month_start = (timezone.now().replace(day=1) - timezone.timedelta(days=30*i)).replace(day=1)
        month_end   = (month_start + timezone.timedelta(days=32)).replace(day=1)
        label = month_start.strftime('%b %Y')
        monthly = orders.filter(order_date__gte=month_start, order_date__lt=month_end)
        spending = monthly.aggregate(t=Sum('total_amount'))['t'] or 0
        chart_labels.append(label)
        chart_spending.append(float(spending))
        chart_orders.append(monthly.count())

    # Order status breakdown for pie chart
    status_data = {
        'Delivered':  orders.filter(order_status='Delivered').count(),
        'Shipped':    orders.filter(order_status='Shipped').count(),
        'Placed':     orders.filter(order_status='Placed').count(),
        'Cancelled':  orders.filter(order_status='Cancelled').count(),
    }

    return render(request, 'users/dashboard.html', {
        'user': user, 'orders': orders[:10], 'active_orders': active,
        'wishlist': wishlist, 'reviews': reviews, 'recommended': recommended,
        'chart_labels':   json.dumps(chart_labels),
        'chart_spending': json.dumps(chart_spending),
        'chart_orders':   json.dumps(chart_orders),
        'status_data':    json.dumps(status_data),
        'total_spent':    sum(chart_spending),
    })


def user_profile_edit(request):
    if not request.session.get('user_id') or request.session.get('role') != 'user':
        return redirect('user_login')
    user = get_object_or_404(UserProfile, user_id=request.session['user_id'])
    if request.method == 'POST':
        d = request.POST
        if not re.match(r'^\d{10}$', d.get('phone_number', '')):
            messages.error(request, 'Phone must be 10 digits.')
            return render(request, 'users/profile_edit.html', {'user': user})
        user.name=d['name']; user.phone_number=d['phone_number']
        user.address_line=d['address_line']; user.nearby_landmark=d.get('nearby_landmark','')
        user.house_no=d['house_no']; user.district=d['district']
        user.state=d['state']; user.pincode=d['pincode']
        user.save()
        request.session['user_name'] = user.name
        messages.success(request, 'Profile updated!')
        return redirect('user_dashboard')
    return render(request, 'users/profile_edit.html', {'user': user})


def user_change_password(request):
    if not request.session.get('user_id') or request.session.get('role') != 'user':
        return redirect('user_login')
    user = get_object_or_404(UserProfile, user_id=request.session['user_id'])
    if request.method == 'POST':
        old = request.POST.get('old_password','')
        new = request.POST.get('new_password','')
        cnf = request.POST.get('confirm_password','')
        if not check_password(old, user.password):
            messages.error(request, 'Current password is incorrect.')
        elif new != cnf:
            messages.error(request, 'New passwords do not match.')
        elif len(new) < 6:
            messages.error(request, 'Password must be at least 6 characters.')
        else:
            user.password = make_password(new); user.save()
            messages.success(request, 'Password changed successfully!')
            return redirect('user_dashboard')
    return render(request, 'users/change_password.html', {'user': user})


def order_history(request):
    if not request.session.get('user_id') or request.session.get('role') != 'user':
        return redirect('user_login')
    user   = get_object_or_404(UserProfile, user_id=request.session['user_id'])
    orders = Order.objects.filter(user=user).order_by('-order_date')
    return render(request, 'users/order_history.html', {'orders': orders, 'user': user})


# ═══════════════════════════════════════════════════════
# OTP LOGIN
# ═══════════════════════════════════════════════════════

import random
from django.utils import timezone
from datetime import timedelta


def _generate_otp():
    return str(random.randint(100000, 999999))


def _send_otp_console(phone, otp, purpose):
    """In production replace with SMS API. For now prints to console."""
    print(f"\n{'='*40}")
    print(f"📱 OTP for {phone} [{purpose}]: {otp}")
    print(f"{'='*40}\n")


def otp_login_request(request):
    """Step 1 — User enters phone number, OTP sent"""
    if request.session.get('user_id'):
        return redirect('home')
    if request.method == 'POST':
        phone = request.POST.get('phone_number', '').strip()
        if not re.match(r'^\d{10}$', phone):
            messages.error(request, 'Enter a valid 10-digit mobile number.')
            return render(request, 'users/otp_login.html', {'step': 'phone'})
        try:
            user = UserProfile.objects.get(phone_number=phone)
        except UserProfile.DoesNotExist:
            messages.error(request, 'No account found with this mobile number.')
            return render(request, 'users/otp_login.html', {'step': 'phone'})

        from .models import OTPVerification
        # Invalidate old OTPs
        OTPVerification.objects.filter(phone_number=phone, purpose='login', is_used=False).update(is_used=True)
        otp = _generate_otp()
        OTPVerification.objects.create(
            phone_number=phone, otp=otp, purpose='login',
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        _send_otp_console(phone, otp, 'login')
        request.session['otp_phone'] = phone
        messages.success(request, f'OTP sent to {phone[:4]}XXXXXX! (Check server console for demo OTP)')
        return render(request, 'users/otp_login.html', {'step': 'verify', 'phone': phone, 'demo_otp': otp})
    return render(request, 'users/otp_login.html', {'step': 'phone'})


def otp_login_verify(request):
    """Step 2 — User enters OTP"""
    if request.method == 'POST':
        from .models import OTPVerification
        phone = request.session.get('otp_phone', '')
        otp   = request.POST.get('otp', '').strip()
        try:
            record = OTPVerification.objects.filter(
                phone_number=phone, otp=otp, purpose='login', is_used=False
            ).latest('created_at')
            if record.is_valid():
                record.is_used = True
                record.save()
                user = UserProfile.objects.get(phone_number=phone)
                if not user.is_active:
                    del request.session['otp_phone']
                    return render(request, 'users/otp_login.html', {
                        'step': 'phone',
                        'suspended': True,
                        'suspension_reason': user.suspension_reason or 'No reason provided.',
                        'admin_email': 'admin@ecommerce.com',
                    })
                request.session['user_id']   = str(user.user_id)
                request.session['user_name'] = user.name
                request.session['role']      = 'user'
                del request.session['otp_phone']
                messages.success(request, f'Welcome, {user.name}! Logged in via OTP.')
                return redirect('home')
            else:
                messages.error(request, 'OTP expired. Please request a new one.')
        except (OTPVerification.DoesNotExist, UserProfile.DoesNotExist):
            messages.error(request, 'Invalid OTP. Please try again.')
        return render(request, 'users/otp_login.html', {'step': 'verify', 'phone': phone})
    return redirect('otp_login_request')


def otp_resend(request):
    """Resend OTP"""
    from .models import OTPVerification
    from django.http import JsonResponse
    phone = request.session.get('otp_phone', '')
    if not phone:
        return JsonResponse({'success': False, 'error': 'Session expired'})
    OTPVerification.objects.filter(phone_number=phone, purpose='login', is_used=False).update(is_used=True)
    otp = _generate_otp()
    OTPVerification.objects.create(
        phone_number=phone, otp=otp, purpose='login',
        expires_at=timezone.now() + timedelta(minutes=10)
    )
    _send_otp_console(phone, otp, 'login resend')
    return JsonResponse({'success': True, 'message': 'OTP resent!', 'demo_otp': otp})


# ═══════════════════════════════════════════════════════
# BAZAR MEMBERSHIP
# ═══════════════════════════════════════════════════════

def membership_page(request):
    user = get_object_or_404(UserProfile, user_id=request.session['user_id']) if request.session.get('user_id') else None
    if not user:
        return redirect('user_login')
    from .models import BazarMembership
    membership = BazarMembership.objects.filter(user=user).first()
    is_member  = membership and membership.is_valid()
    return render(request, 'users/membership.html', {
        'user': user,
        'membership': membership,
        'is_member': is_member,
        'monthly_price': 199,
        'yearly_price': 999,
    })


def join_membership(request):
    if request.method != 'POST':
        return redirect('membership_page')
    user = get_object_or_404(UserProfile, user_id=request.session.get('user_id', ''))
    plan = request.POST.get('plan', 'monthly')
    from .models import BazarMembership
    import datetime
    from django.utils import timezone

    amount = 199 if plan == 'monthly' else 999
    if plan == 'monthly':
        end_date = timezone.now().date() + datetime.timedelta(days=30)
    else:
        end_date = timezone.now().date() + datetime.timedelta(days=365)

    BazarMembership.objects.update_or_create(
        user=user,
        defaults={
            'plan': plan,
            'status': 'active',
            'end_date': end_date,
            'amount_paid': amount,
            'payment_id': f'DEMO_{plan.upper()}_{str(user.user_id)[:8]}'
        }
    )
    request.session['is_prime'] = True
    messages.success(request, f'🎉 Welcome to Bazar Prime! Your {plan} membership is now active.')
    return redirect('membership_page')


def cancel_membership(request):
    user = get_object_or_404(UserProfile, user_id=request.session.get('user_id', ''))
    from .models import BazarMembership
    try:
        m = BazarMembership.objects.get(user=user)
        m.status = 'cancelled'
        m.save()
        messages.info(request, 'Membership cancelled. Benefits remain until expiry date.')
    except BazarMembership.DoesNotExist:
        pass
    return redirect('membership_page')


# ═══════════════════════════════════════════════════════
# FORGOT PASSWORD
# ═══════════════════════════════════════════════════════

def forgot_password(request):
    """Step 1 — User enters email, OTP sent"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        try:
            user = UserProfile.objects.get(email=email, is_active=True)
        except UserProfile.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
            return render(request, 'users/forgot_password.html', {'step': 'email'})

        from .models import OTPVerification
        # Invalidate old OTPs
        OTPVerification.objects.filter(phone_number=user.phone_number, purpose='reset', is_used=False).update(is_used=True)
        otp = _generate_otp()
        OTPVerification.objects.create(
            phone_number=user.phone_number,
            otp=otp,
            purpose='reset',
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        # Store in session
        request.session['reset_email'] = email
        request.session['reset_otp']   = otp  # for demo display
        _send_otp_console(user.phone_number, otp, 'password reset')
        messages.success(request, f'OTP sent! Check server console for demo OTP.')
        return render(request, 'users/forgot_password.html', {
            'step': 'otp',
            'email': email,
            'demo_otp': otp,
            'masked_phone': user.phone_number[:2] + 'XXXXXX' + user.phone_number[-2:],
        })
    return render(request, 'users/forgot_password.html', {'step': 'email'})


def forgot_password_verify(request):
    """Step 2 — Verify OTP"""
    if request.method == 'POST':
        from .models import OTPVerification
        email = request.session.get('reset_email', '')
        otp   = request.POST.get('otp', '').strip()
        if not email:
            messages.error(request, 'Session expired. Please try again.')
            return redirect('forgot_password')
        try:
            user   = UserProfile.objects.get(email=email)
            record = OTPVerification.objects.filter(
                phone_number=user.phone_number,
                otp=otp, purpose='reset', is_used=False
            ).latest('created_at')
            if record.is_valid():
                record.is_used = True
                record.save()
                request.session['reset_verified'] = True
                return render(request, 'users/forgot_password.html', {'step': 'newpass', 'email': email})
            else:
                messages.error(request, 'OTP expired. Please request a new one.')
        except (OTPVerification.DoesNotExist, UserProfile.DoesNotExist):
            messages.error(request, 'Invalid OTP. Please try again.')
        return render(request, 'users/forgot_password.html', {
            'step': 'otp', 'email': email,
            'demo_otp': request.session.get('reset_otp', ''),
        })
    return redirect('forgot_password')


def forgot_password_reset(request):
    """Step 3 — Set new password"""
    if request.method == 'POST':
        if not request.session.get('reset_verified'):
            messages.error(request, 'Unauthorized. Please verify OTP first.')
            return redirect('forgot_password')
        email    = request.session.get('reset_email', '')
        password = request.POST.get('password', '').strip()
        confirm  = request.POST.get('confirm_password', '').strip()

        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters.')
            return render(request, 'users/forgot_password.html', {'step': 'newpass', 'email': email})
        if password != confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'users/forgot_password.html', {'step': 'newpass', 'email': email})

        try:
            from django.contrib.auth.hashers import make_password as dj_make_password
            user = UserProfile.objects.get(email=email)
            user.password = dj_make_password(password)
            user.save(update_fields=['password'])
            # Clear session
            del request.session['reset_email']
            del request.session['reset_verified']
            request.session.pop('reset_otp', None)
            messages.success(request, '✅ Password changed successfully! Please login.')
            return redirect('user_login')
        except UserProfile.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('forgot_password')
    return redirect('forgot_password')


# ── Pincode Lookup (shared by User & Seller registration) ──────────────────
def pincode_lookup(request):
    """Return district & state for a 6-digit Indian pincode via api.postalpincode.in"""
    import json, urllib.request, urllib.error
    from django.http import JsonResponse

    pincode = request.GET.get('pincode', '').strip()
    if not (pincode.isdigit() and len(pincode) == 6):
        return JsonResponse({'success': False, 'error': 'Invalid pincode'})
    try:
        url = f'https://api.postalpincode.in/pincode/{pincode}'
        req = urllib.request.Request(url, headers={'User-Agent': 'OnlineBazar/1.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        if data and data[0].get('Status') == 'Success':
            post = data[0]['PostOffice'][0]
            return JsonResponse({
                'success': True,
                'district': post.get('District', ''),
                'state':    post.get('State', ''),
                'area':     post.get('Name', ''),
            })
        return JsonResponse({'success': False, 'error': 'Pincode not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
