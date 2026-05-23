"""
Demand Forecasting — OnlineBazar
Uses order history to predict next 30-day demand per category
Falls back to mock data if no order history exists
"""
import random
from datetime import datetime, timedelta


def get_demand_forecast():
    """Returns forecast data for all categories"""
    try:
        from store.models import OrderItem, Order, CATEGORY_CHOICES
        from django.utils import timezone
        from django.db.models import Sum, Count
        import collections

        categories = [c[0] for c in CATEGORY_CHOICES]
        result = []

        # Get last 6 months of sales per category
        now = timezone.now()
        monthly_data = {}
        for i in range(6, 0, -1):
            month_start = (now.replace(day=1) - timedelta(days=30 * i)).replace(day=1)
            month_end   = (month_start + timedelta(days=32)).replace(day=1)
            label = month_start.strftime('%b %Y')
            monthly_data[label] = {}
            for cat in categories:
                sales = OrderItem.objects.filter(
                    order__order_date__gte=month_start,
                    order__order_date__lt=month_end,
                    product__category=cat
                ).aggregate(total=Sum('quantity'))['total'] or 0
                monthly_data[label][cat] = sales

        # Calculate growth and next month prediction
        months = list(monthly_data.keys())
        for cat in categories:
            history = [monthly_data[m].get(cat, 0) for m in months]
            total = sum(history)
            if total == 0:
                # No real data — generate realistic mock
                base = random.randint(20, 200)
                history = [int(base * (0.7 + 0.1 * i + random.uniform(-0.1, 0.1))) for i in range(6)]
                total = sum(history)

            # Simple linear regression for next month
            n = len(history)
            if n >= 2:
                avg_growth = (history[-1] - history[0]) / max(n - 1, 1)
                predicted = max(0, int(history[-1] + avg_growth))
            else:
                predicted = history[-1] if history else 0

            growth_pct = round(((history[-1] - history[0]) / max(history[0], 1)) * 100, 1)

            result.append({
                'category': cat,
                'history': history,
                'months': months,
                'predicted_next': predicted,
                'growth_pct': growth_pct,
                'trend': 'up' if growth_pct > 0 else 'down',
                'total_6m': total,
            })

        # Sort by predicted demand
        result.sort(key=lambda x: x['predicted_next'], reverse=True)
        return result

    except Exception as e:
        # Fallback mock data
        categories = ['Electronics', 'Clothing', 'Food', 'Beauty', 'Sports', 'Home', 'Books', 'Toys']
        months = [(datetime.now() - timedelta(days=30 * i)).strftime('%b %Y') for i in range(5, -1, -1)]
        result = []
        for cat in categories:
            base = random.randint(30, 300)
            history = [max(0, int(base * (0.6 + 0.08 * i + random.uniform(-0.15, 0.15)))) for i in range(6)]
            predicted = int(history[-1] * 1.05)
            growth = round(((history[-1] - history[0]) / max(history[0], 1)) * 100, 1)
            result.append({
                'category': cat,
                'history': history,
                'months': months,
                'predicted_next': predicted,
                'growth_pct': growth,
                'trend': 'up' if growth > 0 else 'down',
                'total_6m': sum(history),
            })
        result.sort(key=lambda x: x['predicted_next'], reverse=True)
        return result


def get_low_stock_products():
    """Products with stock <= 10"""
    try:
        from store.models import Product
        return Product.objects.filter(
            is_active=True,
            stock_quantity__lte=10
        ).select_related('seller').order_by('stock_quantity')
    except:
        return []


def get_seller_rankings():
    """Rank sellers by revenue, orders, and avg rating"""
    try:
        from seller.models import Seller
        from store.models import OrderItem, Review
        from django.db.models import Sum, Count, Avg

        sellers = Seller.objects.filter(is_blacklisted=False)
        rankings = []
        for seller in sellers:
            revenue = OrderItem.objects.filter(
                product__seller=seller
            ).aggregate(total=Sum('price_at_purchase'))['total'] or 0

            orders = OrderItem.objects.filter(product__seller=seller).count()

            avg_rating = Review.objects.filter(
                product__seller=seller
            ).aggregate(avg=Avg('rating'))['avg'] or 0

            rankings.append({
                'seller': seller,
                'revenue': float(revenue),
                'orders': orders,
                'avg_rating': round(float(avg_rating), 1),
                'score': round(float(revenue) * 0.5 + orders * 100 + float(avg_rating) * 500, 2)
            })

        rankings.sort(key=lambda x: x['score'], reverse=True)
        for i, r in enumerate(rankings):
            r['rank'] = i + 1
        return rankings
    except:
        return []
