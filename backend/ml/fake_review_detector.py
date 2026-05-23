"""
Fake Review Detector — OnlineBazar
NLP-based detection using heuristics + keyword analysis
Works without external APIs — uses scikit-learn style logic
"""
import re
from datetime import timedelta


FAKE_SIGNALS = {
    # Overly generic praise (often fake)
    "generic_praise": [
        "best product ever", "amazing quality", "super fast delivery",
        "100% genuine", "must buy", "highly recommend", "love it",
        "perfect product", "excellent quality", "very good product",
        "nice product", "good quality", "best seller", "worth it",
        "totally worth", "very satisfied", "5 stars", "five stars",
    ],
    # Very short reviews
    # Repetition patterns
    "spam_phrases": [
        "buy this now", "order now", "don't miss", "limited offer",
        "click here", "visit website", "check this out",
    ],
    # Suspicious patterns
    "suspicious": [
        "i got paid", "free product", "given for review",
        "received for testing", "sponsored", "gifted",
    ]
}


def analyze_review(review_text: str, rating: int, user_id=None, product_id=None) -> dict:
    """
    Returns a dict with:
    - is_fake: bool
    - confidence: float (0-100)
    - reasons: list of strings
    - label: 'Genuine' | 'Suspicious' | 'Likely Fake'
    """
    text = review_text.lower().strip()
    reasons = []
    score = 0  # Higher = more likely fake

    # 1. Very short review with high rating
    word_count = len(text.split())
    if word_count < 5 and rating == 5:
        score += 25
        reasons.append(f"Very short review ({word_count} words) with 5-star rating")

    # 2. All caps (shouting = suspicious)
    caps_ratio = sum(1 for c in review_text if c.isupper()) / max(len(review_text), 1)
    if caps_ratio > 0.5 and len(review_text) > 10:
        score += 20
        reasons.append("Excessive use of CAPITAL LETTERS")

    # 3. Excessive punctuation
    excl_count = review_text.count('!')
    if excl_count >= 3:
        score += 15
        reasons.append(f"Excessive exclamation marks ({excl_count}!)")

    # 4. Generic praise phrases
    generic_hits = [p for p in FAKE_SIGNALS["generic_praise"] if p in text]
    if len(generic_hits) >= 2:
        score += 20
        reasons.append(f"Generic praise phrases: {', '.join(generic_hits[:3])}")

    # 5. Spam phrases
    spam_hits = [p for p in FAKE_SIGNALS["spam_phrases"] if p in text]
    if spam_hits:
        score += 35
        reasons.append(f"Spam language detected: {', '.join(spam_hits)}")

    # 6. Suspicious disclosure
    susp_hits = [p for p in FAKE_SIGNALS["suspicious"] if p in text]
    if susp_hits:
        score += 40
        reasons.append(f"Suspicious disclosure: {', '.join(susp_hits)}")

    # 7. Repeated words (e.g. "good good good product")
    words = text.split()
    if len(words) > 3:
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.5:
            score += 20
            reasons.append("High word repetition detected")

    # 8. Review is just emojis or symbols
    alpha_ratio = sum(1 for c in text if c.isalpha()) / max(len(text), 1)
    if alpha_ratio < 0.4 and len(text) > 3:
        score += 15
        reasons.append("Review contains mostly non-alphabetic characters")

    # 9. Perfect rating with no specific feedback
    if rating == 5 and word_count < 10 and not any(
        word in text for word in ['because', 'since', 'as', 'quality', 'delivery', 'packaging', 'price', 'worth']
    ):
        score += 15
        reasons.append("5-star rating with no specific feedback")

    # Check if user reviewed multiple products on same day (if we have DB access)
    if user_id and product_id:
        try:
            from store.models import Review
            from django.utils import timezone
            today = timezone.now().date()
            same_day_reviews = Review.objects.filter(
                user_id=user_id,
                created_at__date=today
            ).count()
            if same_day_reviews >= 5:
                score += 30
                reasons.append(f"User reviewed {same_day_reviews} products today (suspicious activity)")
        except Exception:
            pass

    # Determine label
    score = min(score, 100)
    if score >= 60:
        label = "Likely Fake"
        is_fake = True
    elif score >= 30:
        label = "Suspicious"
        is_fake = False
    else:
        label = "Genuine"
        is_fake = False

    return {
        "is_fake": is_fake,
        "confidence": score,
        "label": label,
        "reasons": reasons if reasons else ["No suspicious signals detected"],
        "color": "danger" if score >= 60 else ("warning" if score >= 30 else "success"),
    }


def bulk_analyze_reviews(product_id):
    """Analyze all reviews for a product"""
    try:
        from store.models import Review
        reviews = Review.objects.filter(product_id=product_id)
        results = []
        for r in reviews:
            analysis = analyze_review(r.review_text, r.rating, r.user_id, product_id)
            results.append({
                "review": r,
                "analysis": analysis,
            })
        fake_count = sum(1 for r in results if r["analysis"]["is_fake"])
        suspicious_count = sum(1 for r in results if r["analysis"]["label"] == "Suspicious")
        return {
            "results": results,
            "total": len(results),
            "fake_count": fake_count,
            "suspicious_count": suspicious_count,
            "genuine_count": len(results) - fake_count - suspicious_count,
            "fake_percentage": round(fake_count / max(len(results), 1) * 100, 1),
        }
    except Exception as e:
        return {"results": [], "total": 0, "fake_count": 0, "suspicious_count": 0, "genuine_count": 0, "fake_percentage": 0}
