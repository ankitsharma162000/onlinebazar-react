"""
Dynamic Pricing Engine — OnlineBazar
Adjusts suggested price based on:
- Stock level (low stock = higher price)
- Demand trend (high demand = higher price)
- Day of week / time factors
- Competition (avg category price)
"""
from decimal import Decimal
import datetime


def get_dynamic_price(product) -> dict:
    """
    Returns pricing recommendation for a product.
    """
    base_price = float(product.price)
    stock = product.stock_quantity
    category = product.category

    multiplier = 1.0
    reasons = []

    # 1. Stock factor — low stock → increase price (scarcity)
    if stock == 0:
        multiplier *= 1.0  # out of stock, no change
        reasons.append("Out of stock — price unchanged")
    elif stock <= 5:
        multiplier *= 1.15
        reasons.append(f"Critical low stock ({stock} units) → +15%")
    elif stock <= 15:
        multiplier *= 1.08
        reasons.append(f"Low stock ({stock} units) → +8%")
    elif stock >= 200:
        multiplier *= 0.92
        reasons.append(f"High stock ({stock} units) → -8% to boost sales")
    elif stock >= 100:
        multiplier *= 0.96
        reasons.append(f"Good stock ({stock} units) → -4% to attract buyers")

    # 2. Day of week factor
    today = datetime.datetime.now().weekday()  # 0=Mon, 6=Sun
    if today in (5, 6):  # Weekend
        multiplier *= 1.05
        reasons.append("Weekend demand boost → +5%")
    elif today == 0:  # Monday
        multiplier *= 0.97
        reasons.append("Monday slow start → -3%")

    # 3. Time of day factor
    hour = datetime.datetime.now().hour
    if 18 <= hour <= 22:  # Evening peak shopping
        multiplier *= 1.03
        reasons.append("Evening peak hours → +3%")
    elif 0 <= hour <= 6:  # Late night
        multiplier *= 0.97
        reasons.append("Late night low traffic → -3%")

    # 4. Category demand factor
    try:
        from store.models import OrderItem
        from django.utils import timezone
        from django.db.models import Sum
        last_7 = timezone.now() - datetime.timedelta(days=7)
        cat_sales = OrderItem.objects.filter(
            product__category=category,
            order__order_date__gte=last_7
        ).aggregate(total=Sum('quantity'))['total'] or 0

        if cat_sales > 500:
            multiplier *= 1.1
            reasons.append(f"High category demand ({cat_sales} units/week) → +10%")
        elif cat_sales > 200:
            multiplier *= 1.05
            reasons.append(f"Good category demand ({cat_sales} units/week) → +5%")
        elif cat_sales < 20:
            multiplier *= 0.95
            reasons.append(f"Low category demand ({cat_sales} units/week) → -5%")
    except Exception:
        pass

    # 5. Review rating factor
    avg_rating = product.average_rating
    if avg_rating >= 4.5:
        multiplier *= 1.05
        reasons.append(f"Highly rated ({avg_rating}★) → +5%")
    elif avg_rating > 0 and avg_rating < 3.0:
        multiplier *= 0.93
        reasons.append(f"Low rating ({avg_rating}★) → -7% to attract buyers")

    # Calculate final price
    suggested_price = round(base_price * multiplier, 2)
    change_pct = round((multiplier - 1) * 100, 1)

    return {
        "base_price": base_price,
        "suggested_price": suggested_price,
        "change_pct": change_pct,
        "multiplier": round(multiplier, 3),
        "direction": "up" if multiplier > 1.01 else ("down" if multiplier < 0.99 else "stable"),
        "reasons": reasons,
        "recommendation": (
            "Increase price" if multiplier > 1.05 else
            "Slight increase" if multiplier > 1.01 else
            "Slight decrease" if multiplier > 0.97 else
            "Decrease price"
        ) if multiplier != 1.0 else "Keep current price"
    }


def get_all_pricing_recommendations():
    """Get dynamic pricing for all active products"""
    try:
        from store.models import Product
        products = Product.objects.filter(is_active=True).select_related('seller')[:50]
        results = []
        for p in products:
            rec = get_dynamic_price(p)
            if abs(rec['change_pct']) >= 3:  # Only show significant changes
                results.append({"product": p, "rec": rec})
        results.sort(key=lambda x: abs(x['rec']['change_pct']), reverse=True)
        return results
    except Exception:
        return []
