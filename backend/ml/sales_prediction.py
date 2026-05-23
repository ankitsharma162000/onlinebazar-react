"""
ML Module 1: Seasonal Category Sales Prediction
Uses Random Forest to predict top-selling categories by season
"""
from sklearn.ensemble import RandomForestClassifier
import numpy as np
from datetime import date


SEASONS = {12: 'Winter', 1: 'Winter', 2: 'Winter',
           3: 'Spring', 4: 'Spring', 5: 'Spring',
           6: 'Summer', 7: 'Summer', 8: 'Summer',
           9: 'Autumn', 10: 'Autumn', 11: 'Autumn'}

SEASON_MAP = {'Spring': 0, 'Summer': 1, 'Autumn': 2, 'Winter': 3}

FESTIVALS = {
    (10, 11): 'Diwali', (12, 12): 'Christmas',
    (1, 1):   'New Year', (3, 3): 'Holi',
    (8, 8):   'Independence Day',
}


def _get_festival_flag(month):
    for (m, _), _ in FESTIVALS.items():
        if m == month:
            return 1
    return 0


def get_seasonal_prediction():
    try:
        from store.models import OrderItem, Order
        from django.db.models import Sum

        # Pull historical data
        data = OrderItem.objects.select_related('order', 'product').all()
        if data.count() < 5:
            return _fallback_predictions()

        X, y = [], []
        for item in data:
            m  = item.order.order_date.month
            s  = SEASON_MAP.get(SEASONS.get(m, 'Summer'), 1)
            ff = _get_festival_flag(m)
            X.append([m, s, ff, item.order.order_date.year])
            y.append(item.product.category)

        clf = RandomForestClassifier(n_estimators=50, random_state=42)
        clf.fit(X, y)

        today      = date.today()
        results    = []
        for offset in [1, 2, 3]:
            future_m   = ((today.month - 1 + offset) % 12) + 1
            future_s   = SEASON_MAP.get(SEASONS.get(future_m, 'Summer'), 1)
            future_ff  = _get_festival_flag(future_m)
            future_yr  = today.year if future_m >= today.month else today.year + 1
            feat       = [[future_m, future_s, future_ff, future_yr]]
            probs      = clf.predict_proba(feat)[0]
            top3_idx   = np.argsort(probs)[::-1][:3]
            cats       = [clf.classes_[i] for i in top3_idx]
            month_name = date(future_yr, future_m, 1).strftime('%B %Y')
            festival   = FESTIVALS.get((future_m, future_m), '')
            results.append({
                'month': month_name,
                'festival': festival,
                'categories': cats,
                'season': SEASONS.get(future_m, ''),
            })
        return results

    except Exception:
        return _fallback_predictions()


def _fallback_predictions():
    today = date.today()
    results = []
    defaults = {
        'Spring': ['Clothing', 'Sports', 'Beauty'],
        'Summer': ['Electronics', 'Food', 'Home'],
        'Autumn': ['Electronics', 'Books', 'Clothing'],
        'Winter': ['Electronics', 'Home', 'Food'],
    }
    for offset in [1, 2, 3]:
        future_m   = ((today.month - 1 + offset) % 12) + 1
        season     = SEASONS.get(future_m, 'Summer')
        future_yr  = today.year if future_m >= today.month else today.year + 1
        month_name = date(future_yr, future_m, 1).strftime('%B %Y')
        results.append({
            'month': month_name,
            'festival': FESTIVALS.get((future_m, future_m), ''),
            'categories': defaults.get(season, ['Electronics', 'Clothing', 'Food']),
            'season': season,
        })
    return results
