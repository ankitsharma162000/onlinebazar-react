"""
ML Module 3: Automated Low Stock Warning
Predicts daily sales rate and alerts seller if stock < 7-day demand
"""
from django.utils import timezone
from datetime import timedelta


def check_and_generate_stock_alerts(seller):
    try:
        from store.models import Product, OrderItem, StockAlert
        from django.db.models import Sum

        products  = Product.objects.filter(seller=seller, is_active=True)
        ago30     = timezone.now() - timedelta(days=30)

        for product in products:
            sold = OrderItem.objects.filter(
                product=product,
                order__order_date__gte=ago30
            ).aggregate(total=Sum('quantity'))['total'] or 0

            avg_daily     = sold / 30.0
            demand_7_days = avg_daily * 7

            if product.stock_quantity < demand_7_days and demand_7_days > 0:
                StockAlert.objects.update_or_create(
                    product=product,
                    is_resolved=False,
                    defaults={
                        'predicted_demand': round(demand_7_days, 2),
                        'current_stock':    product.stock_quantity,
                    }
                )
    except Exception:
        pass
