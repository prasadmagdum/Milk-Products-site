from .models import Cart, WishlistItem


def cart_count(request):
    count = 0
    wishlist_count = 0
    if request.user.is_authenticated:
        count = Cart.objects.filter(user=request.user).values_list('quantity', flat=True)
        count = sum(count)
        wishlist_count = WishlistItem.objects.filter(user=request.user).count()
    return {'cart_count': count, 'wishlist_count': wishlist_count}
