from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.user_register, name='user_register'),
    path('login/', views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('profile/edit/', views.user_profile_edit, name='user_profile_edit'),
    path('profile/password/', views.user_change_password, name='user_change_password'),
    path('orders/', views.order_history, name='order_history'),
    path('login/otp/', views.otp_login_request, name='otp_login_request'),
    path('login/otp/verify/', views.otp_login_verify, name='otp_login_verify'),
    path('login/otp/resend/', views.otp_resend, name='otp_resend'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('forgot-password/verify/', views.forgot_password_verify, name='forgot_password_verify'),
    path('forgot-password/reset/', views.forgot_password_reset, name='forgot_password_reset'),
    path('membership/', views.membership_page, name='membership_page'),
    path('membership/join/', views.join_membership, name='join_membership'),
    path('membership/cancel/', views.cancel_membership, name='cancel_membership'),
    path('pincode-lookup/', views.pincode_lookup, name='pincode_lookup'),
]
