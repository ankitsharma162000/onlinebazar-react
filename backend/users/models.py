from django.db import models
import uuid


class UserProfile(models.Model):
    GENDER_CHOICES = [('Male','Male'),('Female','Female'),('Other','Other')]

    user_id      = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name         = models.CharField(max_length=100)
    gender       = models.CharField(max_length=10, choices=GENDER_CHOICES)
    email        = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=10)
    password     = models.CharField(max_length=256)
    address_line = models.CharField(max_length=255)
    nearby_landmark = models.CharField(max_length=200, blank=True, null=True)
    house_no     = models.CharField(max_length=50)
    district     = models.CharField(max_length=100)
    state        = models.CharField(max_length=100)
    pincode      = models.CharField(max_length=6)
    is_active         = models.BooleanField(default=True)
    suspension_reason = models.TextField(blank=True, null=True)
    created_at        = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.email})"

    def get_full_address(self):
        parts = [self.house_no, self.address_line]
        if self.nearby_landmark:
            parts.append(f"Near {self.nearby_landmark}")
        parts += [self.district, self.state, self.pincode]
        return ', '.join(parts)

    class Meta:
        db_table = 'users_userprofile'
        ordering = ['-created_at']


class OTPVerification(models.Model):
    """OTP for phone/email verification and OTP login"""
    phone_number = models.CharField(max_length=10)
    otp          = models.CharField(max_length=6)
    purpose      = models.CharField(max_length=20, default='login')  # login / register / reset
    is_used      = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)
    expires_at   = models.DateTimeField()

    def is_valid(self):
        from django.utils import timezone
        return not self.is_used and self.expires_at > timezone.now()

    def __str__(self):
        return f"OTP {self.otp} for {self.phone_number}"

    class Meta:
        db_table = 'users_otpverification'
        ordering = ['-created_at']


class BazarMembership(models.Model):
    """OnlineBazar Prime Membership"""
    PLAN_CHOICES = [('monthly', 'Monthly - ₹199'), ('yearly', 'Yearly - ₹999')]
    STATUS_CHOICES = [('active', 'Active'), ('expired', 'Expired'), ('cancelled', 'Cancelled')]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user        = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='membership')
    plan        = models.CharField(max_length=10, choices=PLAN_CHOICES)
    status      = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')
    start_date  = models.DateField(auto_now_add=True)
    end_date    = models.DateField()
    amount_paid = models.DecimalField(max_digits=8, decimal_places=2)
    payment_id  = models.CharField(max_length=100, blank=True, null=True)
    auto_renew  = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        from django.utils import timezone
        return self.status == 'active' and self.end_date >= timezone.now().date()

    @property
    def days_remaining(self):
        from django.utils import timezone
        delta = self.end_date - timezone.now().date()
        return max(delta.days, 0)

    def __str__(self):
        return f"{self.user.name} — {self.plan} ({self.status})"

    class Meta:
        db_table = 'users_bazarmembership'
