from .models import Cart, CATEGORY_CHOICES
from users.models import UserProfile


def cart_count(request):
    count = 0
    uid = request.session.get('user_id')
    if uid and request.session.get('role') == 'user':
        try:
            user = UserProfile.objects.get(user_id=uid)
            count = Cart.objects.filter(user=user).count()
        except UserProfile.DoesNotExist:
            pass
    return {'cart_count': count}


def categories_list(request):
    return {'all_categories': CATEGORY_CHOICES}
