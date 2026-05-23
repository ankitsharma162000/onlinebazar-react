from rest_framework import serializers
from store.models import Product, Order, OrderItem, Review, Cart, Wishlist, Discount, CATEGORY_CHOICES
from users.models import UserProfile, BazarMembership
from seller.models import Seller, SellerOrderRequest


class SellerPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seller
        fields = ['seller_id', 'name', 'district', 'state']


class ProductSerializer(serializers.ModelSerializer):
    seller = SellerPublicSerializer(read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)
    stock_badge = serializers.SerializerMethodField()
    product_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['product_id', 'product_name', 'category', 'price', 'description',
                  'stock_quantity', 'product_image', 'product_image_url', 'is_active',
                  'created_at', 'seller', 'average_rating', 'review_count', 'stock_badge',
                  'manufacturing_date', 'expiry_date']

    def get_stock_badge(self, obj):
        badge = obj.stock_badge
        return {'status': badge[0], 'label': badge[1], 'color': badge[2]}

    def get_product_image_url(self, obj):
        request = self.context.get('request')
        if obj.product_image and request:
            return request.build_absolute_uri(obj.product_image.url)
        return None


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'user_name', 'rating', 'review_text', 'created_at']


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['user_id', 'name', 'email', 'phone_number', 'gender',
                  'address_line', 'house_no', 'nearby_landmark',
                  'district', 'state', 'pincode', 'created_at']


class UserRegisterSerializer(serializers.Serializer):
    name = serializers.CharField()
    email = serializers.EmailField()
    phone_number = serializers.CharField(max_length=10)
    gender = serializers.ChoiceField(choices=['Male', 'Female', 'Other'])
    password = serializers.CharField(min_length=6)
    address_line = serializers.CharField()
    house_no = serializers.CharField()
    nearby_landmark = serializers.CharField(required=False, allow_blank=True)
    district = serializers.CharField()
    state = serializers.CharField()
    pincode = serializers.CharField(max_length=6)


class SellerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seller
        fields = ['seller_id', 'name', 'email', 'phone_number',
                  'address_line', 'district', 'state', 'pincode', 'created_at']


class SellerRegisterSerializer(serializers.Serializer):
    name = serializers.CharField()
    email = serializers.EmailField()
    phone_number = serializers.CharField(max_length=10)
    password = serializers.CharField(min_length=6)
    address_line = serializers.CharField()
    district = serializers.CharField()
    state = serializers.CharField()
    pincode = serializers.CharField(max_length=6)


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.product_name', read_only=True)
    product_image_url = serializers.SerializerMethodField()
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product_id', 'product_name', 'product_image_url',
                  'quantity', 'price_at_purchase', 'subtotal']

    def get_product_image_url(self, obj):
        request = self.context.get('request')
        if obj.product.product_image and request:
            return request.build_absolute_uri(obj.product.product_image.url)
        return None


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    tracking_steps = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['order_id', 'order_date', 'total_amount', 'subtotal',
                  'delivery_charge', 'platform_fee', 'payment_method',
                  'payment_status', 'order_status', 'delivery_address',
                  'is_bazar_member', 'items', 'tracking_steps']

    def get_tracking_steps(self, obj):
        return [{'step': s, 'done': d} for s, d in obj.tracking_steps]


class CartSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'product', 'quantity', 'added_at']


class WishlistSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'product', 'added_at']


class MembershipSerializer(serializers.ModelSerializer):
    days_remaining = serializers.IntegerField(read_only=True)
    is_valid = serializers.SerializerMethodField()

    class Meta:
        model = BazarMembership
        fields = ['id', 'plan', 'status', 'start_date', 'end_date',
                  'amount_paid', 'days_remaining', 'is_valid']

    def get_is_valid(self, obj):
        return obj.is_valid()


class SellerOrderRequestSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='order_item.product.product_name', read_only=True)
    quantity = serializers.IntegerField(source='order_item.quantity', read_only=True)
    customer_name = serializers.CharField(source='order.user.name', read_only=True)
    delivery_address = serializers.CharField(source='order.delivery_address', read_only=True)
    order_date = serializers.DateTimeField(source='order.order_date', read_only=True)
    delivery_partner_name = serializers.CharField(read_only=True)

    class Meta:
        model = SellerOrderRequest
        fields = ['id', 'status', 'product_name', 'quantity', 'customer_name',
                  'delivery_address', 'order_date', 'delivery_partner',
                  'delivery_partner_name', 'tracking_id', 'rejection_reason',
                  'accepted_at', 'shipped_at']
