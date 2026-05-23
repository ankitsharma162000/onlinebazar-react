from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('auth/user/register/', views.user_register),
    path('auth/user/login/', views.user_login),
    path('auth/seller/register/', views.seller_register),
    path('auth/seller/login/', views.seller_login),
    path('auth/user/me/', views.user_me),
    path('auth/seller/me/', views.seller_me),

    # Products
    path('products/', views.product_list),
    path('products/featured/', views.featured_products),
    path('products/recommended/', views.recommended_products),
    path('products/categories/', views.categories),
    path('products/<uuid:product_id>/', views.product_detail),
    path('products/<uuid:product_id>/review/', views.add_review),

    # Cart
    path('cart/', views.cart_list),
    path('cart/add/', views.cart_add),
    path('cart/<int:cart_id>/', views.cart_update),

    # Wishlist
    path('wishlist/', views.wishlist_list),
    path('wishlist/toggle/', views.wishlist_toggle),

    # Coupon
    path('coupon/apply/', views.apply_coupon),

    # Orders
    path('orders/', views.order_list),
    path('orders/checkout/', views.checkout),
    path('orders/<uuid:order_id>/', views.order_detail),

    # Membership
    path('membership/', views.membership_status),
    path('membership/join/', views.join_membership),

    # Seller
    path('seller/me/', views.seller_me),
    path('seller/stats/', views.seller_dashboard_stats),
    path('seller/products/', views.seller_products),
    path('seller/products/add/', views.seller_add_product),
    path('seller/products/<uuid:product_id>/', views.seller_product_detail),
    path('seller/orders/', views.seller_orders),
    path('seller/orders/<uuid:req_id>/action/', views.seller_order_action),

    # Utility
    path('pincode/', views.pincode_lookup),
]
