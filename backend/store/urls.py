from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('product/<uuid:product_id>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/<uuid:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:cart_id>/', views.update_cart, name='update_cart'),
    path('cart/coupon/apply/', views.apply_coupon, name='apply_coupon'),
    path('cart/coupon/remove/', views.remove_coupon, name='remove_coupon'),
    path('wishlist/add/<uuid:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:item_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/success/<uuid:order_id>/', views.order_success, name='order_success'),
    path('order/track/<uuid:order_id>/', views.track_order, name='track_order'),
    path('compare/', views.compare_products, name='compare_products'),
    path('search/', views.advanced_search, name='advanced_search'),
    path('price-alert/set/<uuid:product_id>/', views.set_price_alert, name='set_price_alert'),
    path('price-alert/my/', views.my_price_alerts, name='my_price_alerts'),
    path('price-alert/delete/<int:alert_id>/', views.delete_price_alert, name='delete_price_alert'),
    path('order/bill/<uuid:order_id>/', views.order_bill, name='order_bill'),
    path('order/bill/<uuid:order_id>/pdf/', views.order_bill_pdf, name='order_bill_pdf'),
    path('order/return/<int:order_item_id>/', views.request_return, name='request_return'),
    path('returns/my/', views.my_returns, name='my_returns'),
    path('returns/cancel/<uuid:return_id>/', views.cancel_return, name='cancel_return'),
]
