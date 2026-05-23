from django.urls import path
from . import views

urlpatterns = [
    path('message/',  views.chat_message,      name='chat_message'),
    path('updates/',  views.check_updates,     name='chat_updates'),
    path('orders/',   views.get_order_history, name='chat_orders'),
]
