from django.contrib import admin
from .models import Seller

@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display  = ['name', 'email', 'phone_number', 'state', 'is_blacklisted', 'created_at']
    list_filter   = ['is_blacklisted', 'state']
    search_fields = ['name', 'email']
