from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display  = ['name', 'email', 'phone_number', 'state', 'is_active', 'created_at']
    list_filter   = ['is_active', 'state', 'gender']
    search_fields = ['name', 'email', 'phone_number']
