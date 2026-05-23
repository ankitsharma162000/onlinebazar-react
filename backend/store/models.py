from django.db import models
from users.models import UserProfile
from seller.models import Seller
import uuid

CATEGORY_CHOICES = [
    ('Electronics','Electronics'),
    ('Clothing','Clothing'),
    ('Food','Food & Groceries'),
    ('Beauty','Beauty & Personal Care'),
    ('Sports','Sports & Fitness'),
    ('Home','Home & Kitchen'),
    ('Books','Books & Stationery'),
    ('Toys','Toys & Games'),
    ('Health','Health & Wellness'),
    ('Other','Other'),
]

ORDER_STATUS = ['Placed','Confirmed','Shipped','Out for Delivery','Delivered','Cancelled']
PAYMENT_METHODS = [('COD','Cash on Delivery'),('UPI','UPI'),
                   ('Card','ATM/Debit Card'),('NetBanking','Net Banking')]
PAYMENT_STATUS  = [('Pending','Pending'),('Paid','Paid'),
                   ('Failed','Failed'),('Refunded','Refunded')]


class Product(models.Model):
    product_id      = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller          = models.ForeignKey(Seller, on_delete=models.CASCADE, related_name='products')
    product_name    = models.CharField(max_length=255)
    category        = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    price           = models.DecimalField(max_digits=10, decimal_places=2)
    description     = models.TextField(blank=True)
    manufacturing_date = models.DateField(null=True, blank=True)
    expiry_date     = models.DateField(null=True, blank=True)
    stock_quantity  = models.IntegerField(default=0)
    product_image   = models.ImageField(upload_to='products/images/', null=True, blank=True)
    is_active       = models.BooleanField(default=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    def __str__(self): return self.product_name

    @property
    def average_rating(self):
        r = self.reviews.all()
        return round(sum(x.rating for x in r)/r.count(), 1) if r.exists() else 0

    @property
    def review_count(self): return self.reviews.count()

    @property
    def stock_badge(self):
        if self.stock_quantity == 0: return ('out','Out of Stock','danger')
        if self.stock_quantity <= 10: return ('low', f'Only {self.stock_quantity} left!','warning')
        return ('in','In Stock','success')

    class Meta:
        db_table = 'store_product'
        ordering = ['-created_at']


class ProductImage(models.Model):
    product    = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image      = models.ImageField(upload_to='products/images/')
    is_primary = models.BooleanField(default=False)
    uploaded_at= models.DateTimeField(auto_now_add=True)
    class Meta: db_table = 'store_productimage'


class Discount(models.Model):
    discount_id  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code         = models.CharField(max_length=50, unique=True)
    discount_type= models.CharField(max_length=10, choices=[('flat','Flat Amount'),('percent','Percentage')])
    value        = models.DecimalField(max_digits=10, decimal_places=2)
    applicable_category = models.CharField(max_length=100, blank=True, null=True)
    festival_name= models.CharField(max_length=100, blank=True, null=True)
    valid_from   = models.DateField()
    valid_until  = models.DateField()
    is_active    = models.BooleanField(default=True)
    def __str__(self): return f"{self.code} ({self.value})"
    class Meta: db_table = 'store_discount'


class Order(models.Model):
    order_id       = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user           = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='orders')
    order_date     = models.DateTimeField(auto_now_add=True)
    total_amount   = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal       = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_charge= models.DecimalField(max_digits=6, decimal_places=2, default=0)
    platform_fee   = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    is_bazar_member= models.BooleanField(default=False)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='Pending')
    order_status   = models.CharField(max_length=30, default='Placed')
    discount       = models.ForeignKey(Discount, on_delete=models.SET_NULL, null=True, blank=True)
    delivery_address = models.TextField()
    razorpay_order_id  = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id= models.CharField(max_length=100, blank=True, null=True)

    def __str__(self): return f"Order#{str(self.order_id)[:8]}"

    @property
    def tracking_steps(self):
        steps = ['Placed','Confirmed','Shipped','Out for Delivery','Delivered']
        idx = steps.index(self.order_status) if self.order_status in steps else 0
        return [(s, i <= idx) for i, s in enumerate(steps)]

    class Meta:
        db_table = 'store_order'
        ordering = ['-order_date']


class OrderItem(models.Model):
    order             = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product           = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity          = models.IntegerField(default=1)
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)
    @property
    def subtotal(self): return self.quantity * self.price_at_purchase
    class Meta: db_table = 'store_orderitem'


class Review(models.Model):
    user       = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='reviews')
    product    = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    rating     = models.IntegerField(default=5)
    review_text= models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'store_review'
        unique_together = ('user','product')
        ordering = ['-created_at']


class Cart(models.Model):
    user     = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='cart_items')
    product  = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'store_cart'
        unique_together = ('user','product')


class Wishlist(models.Model):
    user     = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='wishlist_items')
    product  = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'store_wishlist'
        unique_together = ('user','product')


class SearchHistory(models.Model):
    user          = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='searches')
    searched_query= models.CharField(max_length=255)
    category      = models.CharField(max_length=100, blank=True)
    searched_at   = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'store_searchhistory'
        ordering = ['-searched_at']


class StockAlert(models.Model):
    product          = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='alerts')
    predicted_demand = models.FloatField()
    current_stock    = models.IntegerField()
    alert_sent_at    = models.DateTimeField(auto_now_add=True)
    is_resolved      = models.BooleanField(default=False)
    class Meta:
        db_table = 'store_stockalert'
        ordering = ['-alert_sent_at']


class PriceAlert(models.Model):
    """User sets target price for a product — notified when price drops"""
    user        = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='price_alerts')
    product     = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='price_alerts')
    target_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    triggered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'product')
        db_table = 'store_pricealert'

    def __str__(self):
        return f"{self.user} wants {self.product} at ₹{self.target_price}"


class RecentlyViewed(models.Model):
    """Track recently viewed products per user"""
    user      = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='recently_viewed')
    product   = models.ForeignKey(Product, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'product')
        db_table = 'store_recentlyviewed'
        ordering = ['-viewed_at']


class ReturnRequest(models.Model):
    """User requests return/refund for a delivered order item"""

    REASON_CHOICES = [
        ('damaged',     'Product is damaged/defective'),
        ('wrong_item',  'Wrong item delivered'),
        ('not_working', 'Product not working'),
        ('size_issue',  'Size/fit issue'),
        ('quality',     'Poor quality'),
        ('not_needed',  'No longer needed'),
        ('other',       'Other reason'),
    ]
    STATUS_CHOICES = [
        ('pending',   'Pending Review'),
        ('approved',  'Approved'),
        ('rejected',  'Rejected'),
        ('picked_up', 'Item Picked Up'),
        ('refunded',  'Refund Processed'),
    ]
    TYPE_CHOICES = [
        ('return',    'Return & Refund'),
        ('exchange',  'Exchange'),
        ('refund',    'Refund Only'),
    ]

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user         = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='return_requests')
    order        = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='return_requests')
    order_item   = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='return_requests')
    return_type  = models.CharField(max_length=10, choices=TYPE_CHOICES, default='return')
    reason       = models.CharField(max_length=20, choices=REASON_CHOICES)
    description  = models.TextField(help_text='Describe the issue in detail')
    product_image= models.ImageField(upload_to='returns/', null=True, blank=True)
    status       = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    admin_note   = models.TextField(blank=True, null=True)
    seller_note  = models.TextField(blank=True, null=True)
    refund_amount= models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)
    resolved_at  = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'store_returnrequest'
        ordering = ['-created_at']

    def __str__(self):
        return f"Return #{str(self.id)[:8]} — {self.user.name} [{self.status}]"

    @property
    def is_within_return_window(self):
        """Returns can be raised within 7 days of delivery"""
        from django.utils import timezone
        if self.order.order_status == 'Delivered':
            days = (timezone.now() - self.order.order_date).days
            return days <= 7
        return False


class SellerDiscount(models.Model):
    """Seller-level product discount — seller applies to own products"""
    DISCOUNT_TYPE = [
        ('flat',    'Flat Amount (Rs.)'),
        ('percent', 'Percentage (%)'),
    ]
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller       = models.ForeignKey('seller.Seller', on_delete=models.CASCADE, related_name='seller_discounts')
    product      = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='seller_discounts')
    discount_type= models.CharField(max_length=10, choices=DISCOUNT_TYPE)
    value        = models.DecimalField(max_digits=8, decimal_places=2)
    is_active    = models.BooleanField(default=True)
    start_date   = models.DateField(null=True, blank=True)
    end_date     = models.DateField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    def discounted_price(self):
        p = self.product.price
        if self.discount_type == 'flat':
            return max(0, p - self.value)
        else:
            return round(p * (1 - self.value / 100), 2)

    def __str__(self):
        return f"{self.product.product_name} — {self.value}{'%' if self.discount_type=='percent' else ' Rs.'} off"

    class Meta:
        db_table = 'store_sellerdiscount'
        ordering = ['-created_at']


class SellerActivity(models.Model):
    """Audit log — tracks all seller actions for SuperAdmin visibility"""
    ACTION_CHOICES = [
        ('discount_added',    'Discount Added'),
        ('discount_removed',  'Discount Removed'),
        ('price_changed',     'Price Changed'),
        ('return_approved',   'Return Approved'),
        ('return_rejected',   'Return Rejected'),
    ]
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller     = models.ForeignKey('seller.Seller', on_delete=models.CASCADE, related_name='activities')
    action     = models.CharField(max_length=30, choices=ACTION_CHOICES)
    product    = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    details    = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.seller.name} — {self.action} at {self.created_at:%d %b %Y %H:%M}"

    class Meta:
        db_table = 'store_selleractivity'
        ordering = ['-created_at']
