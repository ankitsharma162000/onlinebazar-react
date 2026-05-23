from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = "E-Commerce Admin — MCA Project"
admin.site.site_title = "E-Commerce Admin"
admin.site.index_title = "Founders: Ankit Sharma & Niraj Kumar"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('', include('store.urls')),
    path('user/', include('users.urls')),
    path('seller/', include('seller.urls')),
    path('superadmin/', include('superadmin.urls')),
    path('payments/', include('payments.urls')),
    path('chat/', include('chatbot.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) \
  + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
