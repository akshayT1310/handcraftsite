from .models import CartItem, WishlistItem

def cart_count(request):
    """Add cart item count and wishlist count to all templates"""
    context = {'cart_count': 0, 'wishlist_count': 0}
    if request.user.is_authenticated:
        context['cart_count'] = CartItem.objects.filter(user=request.user).count()
        context['wishlist_count'] = WishlistItem.objects.filter(user=request.user).count()
    return context
