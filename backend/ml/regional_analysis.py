"""
ML Module 2: Regional Demand Analysis
Groups orders by user state and product category
"""


def get_regional_data(seller):
    """Returns top states for a specific seller's products."""
    try:
        from store.models import OrderItem
        from django.db.models import Sum

        items = OrderItem.objects.filter(
            product__seller=seller
        ).select_related('order__user', 'product')

        region_map = {}
        for item in items:
            state = item.order.user.state or 'Unknown'
            cat   = item.product.category
            key   = (state, cat)
            region_map[key] = region_map.get(key, 0) + item.quantity

        # Convert to sorted list
        data = [{'state': k[0], 'category': k[1], 'quantity': v}
                for k, v in sorted(region_map.items(), key=lambda x: -x[1])]
        return data[:10]
    except Exception:
        return []


def get_all_regional_data():
    """Returns top states across all sellers (for SuperAdmin)."""
    try:
        from store.models import OrderItem
        from django.db.models import Sum

        items = OrderItem.objects.select_related('order__user', 'product').all()

        region_map = {}
        for item in items:
            state = item.order.user.state or 'Unknown'
            cat   = item.product.category
            key   = (state, cat)
            region_map[key] = region_map.get(key, 0) + item.quantity

        data = [{'state': k[0], 'category': k[1], 'quantity': v}
                for k, v in sorted(region_map.items(), key=lambda x: -x[1])]
        return data[:15]
    except Exception:
        return []
