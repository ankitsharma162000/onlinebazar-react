"""
ML Module 4: Content-Based Product Recommendations
Uses TF-IDF + Cosine Similarity on user search history
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


def get_recommendations(user_id, top_n=6):
    try:
        # Import here to avoid circular imports at module load
        from store.models import SearchHistory, Product

        # Get user's last 10 searches
        searches = SearchHistory.objects.filter(
            user__user_id=user_id
        ).values_list('searched_query', flat=True).order_by('-searched_at')[:10]

        if not searches:
            # Cold start: return highest rated / newest products
            return list(Product.objects.filter(
                is_active=True, seller__is_blacklisted=False
            ).order_by('-created_at')[:top_n])

        user_profile = ' '.join(searches)

        products = list(Product.objects.filter(
            is_active=True, seller__is_blacklisted=False, stock_quantity__gt=0
        ))
        if not products:
            return []

        # Build corpus: product name + category + description
        corpus = [f"{p.product_name} {p.category} {p.description}" for p in products]
        corpus.append(user_profile)  # append user profile as last doc

        vectorizer = TfidfVectorizer(stop_words='english', max_features=500)
        tfidf_matrix = vectorizer.fit_transform(corpus)

        # Similarity of user profile (last) vs all products
        user_vec  = tfidf_matrix[-1]
        prod_vecs = tfidf_matrix[:-1]
        scores    = cosine_similarity(user_vec, prod_vecs).flatten()

        top_indices = np.argsort(scores)[::-1][:top_n]
        return [products[i] for i in top_indices if scores[i] > 0]

    except Exception:
        return []
