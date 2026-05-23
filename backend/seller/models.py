from django.db import models
import uuid


DELIVERY_PARTNERS = [
    ('bluedart',   'Blue Dart Express'),
    ('delhivery',  'Delhivery'),
    ('dtdc',       'DTDC Courier'),
    ('ecom',       'Ecom Express'),
    ('xpressbees', 'XpressBees'),
    ('shadowfax',  'Shadowfax'),
]


class Seller(models.Model):
    seller_id   = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name        = models.CharField(max_length=100)
    email       = models.EmailField(unique=True)
    phone_number= models.CharField(max_length=10)
    password    = models.CharField(max_length=256)
    address_line= models.CharField(max_length=255)
    district    = models.CharField(max_length=100)
    state       = models.CharField(max_length=100)
    pincode     = models.CharField(max_length=6)
    is_blacklisted  = models.BooleanField(default=False)
    blacklist_reason= models.TextField(blank=True, null=True)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.email})"

    @property
    def business_name(self):
        """Alias for name — used in templates"""
        return self.name

    class Meta:
        db_table = 'store_seller'
        ordering = ['-created_at']


class SellerOrderRequest(models.Model):
    """
    When a user places an order, a request is sent to each seller.
    Seller must Accept or Reject. On Accept → choose delivery partner → shipped.
    """
    STATUS_CHOICES = [
        ('pending',   'Pending Seller Action'),
        ('accepted',  'Accepted'),
        ('rejected',  'Rejected'),
        ('shipped',   'Shipped'),
        ('delivered', 'Delivered'),
    ]

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order           = models.ForeignKey('store.Order', on_delete=models.CASCADE, related_name='seller_requests')
    seller          = models.ForeignKey(Seller, on_delete=models.CASCADE, related_name='order_requests')
    order_item      = models.ForeignKey('store.OrderItem', on_delete=models.CASCADE, related_name='seller_request')
    status          = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    delivery_partner= models.CharField(max_length=20, choices=DELIVERY_PARTNERS, blank=True, null=True)
    tracking_id     = models.CharField(max_length=100, blank=True, null=True)
    rejection_reason= models.TextField(blank=True, null=True)
    accepted_at     = models.DateTimeField(null=True, blank=True)
    shipped_at      = models.DateTimeField(null=True, blank=True)
    delivered_at    = models.DateTimeField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Request #{str(self.id)[:8]} — {self.seller.name} [{self.status}]"

    @property
    def delivery_partner_name(self):
        partners = dict(DELIVERY_PARTNERS)
        return partners.get(self.delivery_partner, self.delivery_partner or '—')

    class Meta:
        db_table = 'seller_orderrequest'
        ordering = ['-created_at']

