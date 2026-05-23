from django.contrib import admin
from .models import Product, ProductImage, Order, OrderItem, Review, Cart, Wishlist, Discount, SearchHistory, StockAlert


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display  = ['product_name', 'seller', 'category', 'price', 'stock_quantity', 'is_active']
    list_filter   = ['category', 'is_active']
    search_fields = ['product_name', 'seller__name']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display  = ['order_id', 'user', 'total_amount', 'payment_method', 'payment_status', 'order_status', 'order_date']
    list_filter   = ['order_status', 'payment_method', 'payment_status']
    search_fields = ['user__name', 'user__email']

@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type', 'value', 'valid_from', 'valid_until', 'is_active']

@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = ['product', 'current_stock', 'predicted_demand', 'is_resolved', 'alert_sent_at']

admin.site.register(ProductImage)
admin.site.register(OrderItem)
admin.site.register(Review)
admin.site.register(Cart)
admin.site.register(Wishlist)
admin.site.register(SearchHistory)
