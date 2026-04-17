from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.urls import reverse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from .models import Product, Order, OrderItem, CartItem, Review, WishlistItem
from .forms import UserRegisterForm, ProductForm, ReviewForm # Ensure this matches your forms.py
from .notifications import (
    send_order_confirmation_email, 
    send_order_status_update_email, 
    send_order_confirmation_sms, 
    send_order_status_sms,
    send_order_cancelled_email,
    send_order_cancelled_sms,
    send_admin_cancellation_alert,
)

# --- 1. AUTHENTICATION VIEWS ---

def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account ban gaya hai {username}! Ab login karein.')
            # Redirecting to Login page as requested
            return redirect('login') 
        else:
            messages.error(request, "Registration failed. Details sahi se bharein.")
    else:
        form = UserRegisterForm()
    return render(request, 'shop/register.html', {'form': form})

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Swagat hai, {username}!")
                return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'shop/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "Logged out successfully.")
    return redirect('login')


# --- 2. SHOP & PRODUCTS ---

def home(request):
    """Home page with featured products"""
    products = Product.objects.filter(is_active=True).order_by('-id')[:6]
    return render(request, 'shop/home.html', {'products': products})

def shop_page(request):
    """Shop page with filters, search, and pagination"""
    products = Product.objects.filter(is_active=True).prefetch_related('reviews')

    # Category filter
    category = request.GET.get('category', '')
    if category:
        products = products.filter(category=category)

    # Price range filter
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    if min_price:
        try:
            products = products.filter(price__gte=int(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            products = products.filter(price__lte=int(max_price))
        except ValueError:
            pass

    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )

    # Sort
    sort_by = request.GET.get('sort', '-id')
    valid_sorts = ['price', '-price', 'name', '-name', 'id', '-id', '-created_at']
    if sort_by in valid_sorts:
        products = products.order_by(sort_by)
    else:
        products = products.order_by('-id')

    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get all categories for filter dropdown
    categories = Product.CATEGORY_CHOICES

    context = {
        'products': page_obj,
        'page_obj': page_obj,
        'categories': categories,
        'current_category': category,
        'current_min_price': min_price,
        'current_max_price': max_price,
        'search_query': search_query,
        'current_sort': sort_by,
    }
    return render(request, 'shop_page.html', context)

def product_detail(request, product_id):
    """Display detailed view of a single product"""
    product = get_object_or_404(Product, id=product_id)
    # Get other products for "similar products" section (excluding current product)
    other_products = Product.objects.exclude(id=product_id).filter(is_active=True)[:4]
    
    return render(request, 'shop/product_detail.html', {
        'product': product,
        'other_products': other_products,
    })


# --- 3. CART SYSTEM (ADVANCED) ---

@login_required(login_url='login')
def cart_view(request):
    cart_items = CartItem.objects.filter(user=request.user).select_related('product')
    
    # Calculate total using list comprehension
    # item_total is already a @property in CartItem model, no need to set it manually
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    return render(request, 'shop/cart.html', {
        'cart_items': cart_items,
        'total': total,
    })

@login_required(login_url='login')
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)

    if not created:
        cart_item.quantity += 1
        cart_item.save()
        message = f"{product.name} quantity updated."
    else:
        message = f"{product.name} added to cart!"

    # Check if AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        cart_count = CartItem.objects.filter(user=request.user).count()
        return JsonResponse({
            'success': True,
            'message': message,
            'cart_count': cart_count,
            'product_name': product.name
        })

    messages.info(request, message)
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required(login_url='login')
def update_cart(request, item_id, action):
    cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
    if action == 'increase':
        cart_item.quantity += 1
    elif action == 'decrease' and cart_item.quantity > 1:
        cart_item.quantity -= 1
    cart_item.save()
    return redirect('cart_view')

@login_required(login_url='login')
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
    cart_item.delete()
    messages.warning(request, "Item removed from cart.")
    return redirect('cart_view')


# --- 4. CHECKOUT & ORDERS ---

@login_required(login_url='login')
def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user)
    if not cart_items:
        messages.warning(request, "Aapka cart khali hai!")
        return redirect('home')

    total = sum(item.product.price * item.quantity for item in cart_items)

    if request.method == "POST":
        # Order create logic
        order = Order.objects.create(
            user=request.user,
            full_name=request.POST.get('full_name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            address=request.POST.get('address'),
            city=request.POST.get('city'),
            pincode=request.POST.get('pincode'),
            total_amount=total
        )

        # Save each cart item as an OrderItem
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )

        # Send order confirmation email
        send_order_confirmation_email(order)

        # Send order confirmation SMS
        if order.phone:
            send_order_confirmation_sms(order)

        # Cart khali karein order ke baad
        cart_items.delete()
        request.session['order_id'] = order.id
        return redirect('payment_view')

    return render(request, 'shop/checkout.html', {'total': total})

@login_required(login_url='login')
@login_required(login_url='login')
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-id')
    return render(request, 'shop/my_orders.html', {'orders': orders})


@login_required(login_url='login')
def cancel_order(request, order_id):
    """Customer cancels their order (only if Pending/not yet processed by admin)"""
    order = get_object_or_404(Order, id=order_id)
    
    # Verify ownership - check if user is set and matches current user
    if order.user is None or order.user != request.user:
        messages.error(request, 'You do not have permission to cancel this order.')
        return redirect('my_orders')
    
    # Check if order is already cancelled
    if order.status == 'Cancelled':
        messages.error(request, 'This order has already been cancelled.')
        return redirect('my_orders')
    
    # Check if order can be cancelled (only if still Pending)
    if order.status != 'Pending':
        messages.error(request, f'Orders cannot be cancelled once processing has started. Current status: {order.status}')
        return redirect('my_orders')
    
    if request.method == 'POST':
        try:
            reason = request.POST.get('reason', '').strip()
            
            # Cancel the order
            order.status = 'Cancelled'
            order.cancelled_at = timezone.now()
            order.cancellation_reason = reason if reason else 'No reason provided'
            
            # If order was paid, set refund status to Pending
            if order.payment_status:
                order.refund_status = 'Pending'
            
            order.save()
            
            # Send notifications
            send_order_cancelled_email(order, reason=reason if reason else None)
            if order.phone:
                send_order_cancelled_sms(order, reason=reason if reason else None)
            send_admin_cancellation_alert(order, cancelled_by='Customer', reason=reason if reason else None)
            
            messages.success(request, f'✓ Order #{order.id} has been cancelled successfully.')
            return redirect('my_orders')
        except Exception as e:
            messages.error(request, f'Error cancelling order: {str(e)}')
            return redirect('my_orders')
    
    # GET request - show confirmation page
    return render(request, 'shop/cancel_order_confirm.html', {'order': order})


@login_required(login_url='login')
def customer_profile(request):
    """Customer profile page showing personal details and all orders"""
    user = request.user
    orders = Order.objects.filter(user=user).order_by('-created_at')

    # Calculate statistics
    total_orders = orders.count()
    total_spent = sum(order.total_amount for order in orders)

    context = {
        'user': user,
        'orders': orders,
        'total_orders': total_orders,
        'total_spent': total_spent,
    }

    return render(request, 'shop/profile.html', context)

@login_required(login_url='login')
def update_phone(request):
    """Update user's phone number"""
    if request.method == 'POST':
        phone = request.POST.get('phone')
        user = request.user
        
        # Update phone in Django User model (if using custom profile)
        # For now, we'll save it in session for checkout auto-fill
        request.session['user_phone'] = phone
        
        messages.success(request, f'✓ Phone number updated: {phone}')
    
    return redirect('customer_profile')


@login_required(login_url='login')
def payment_view(request):
    """Handle payment processing"""
    order_id = request.session.get('order_id')
    if not order_id:
        messages.warning(request, "Koi order nahi mile!")
        return redirect('home')
    
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if request.method == 'POST':
        # Payment processing logic here
        # For now, we'll just mark as paid
        order.payment_status = True
        order.save()
        messages.success(request, "Payment successful! Thank you for your order.")
        return redirect('thanks')
    
    return render(request, 'shop/payment.html', {'order': order})


@login_required(login_url='login')
def thanks(request):
    """Order confirmation page"""
    order_id = request.session.get('order_id')
    if not order_id:
        messages.warning(request, "Koi order nahi mile!")
        return redirect('home')
    
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Clear the session after displaying order
    if 'order_id' in request.session:
        del request.session['order_id']
    
    return render(request, 'shop/thanks.html', {'order': order})


# --- 5. PRODUCT MANAGEMENT (Admin) ---

def is_admin(user):
    """Check if user is superuser/admin"""
    return user.is_superuser or user.is_staff

@login_required(login_url='login')
@user_passes_test(is_admin)
def add_product(request):
    """Add new product to store"""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'✓ Product "{product.name}" added successfully!')
            return redirect('home')
        else:
            messages.error(request, 'Error adding product. Please check the form.')
    else:
        form = ProductForm()
    
    return render(request, 'shop/add_product.html', {'form': form})

@login_required(login_url='login')
@user_passes_test(is_admin)
def edit_product(request, product_id):
    """Edit existing product"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'✓ Product "{product.name}" updated successfully!')
            return redirect('home')
        else:
            messages.error(request, 'Error updating product. Please check the form.')
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'shop/edit_product.html', {'form': form, 'product': product})

@login_required(login_url='login')
@user_passes_test(is_admin)
def delete_product(request, product_id):
    """Delete product from store"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'✓ Product "{product_name}" deleted successfully!')
        return redirect('home')
    
    return render(request, 'shop/delete_product.html', {'product': product})

@login_required(login_url='login')
@user_passes_test(is_admin)
def product_list_admin(request):
    """Admin view to see all products"""
    products = Product.objects.all().order_by('-created_at')
    return render(request, 'shop/product_list_admin.html', {'products': products})


# --- 6. ADMIN ORDER MANAGEMENT ---

@login_required(login_url='login')
@user_passes_test(is_admin)
def admin_orders_list(request):
    """Admin view to see all orders"""
    orders = Order.objects.all().order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    # Count by status
    all_count = Order.objects.count()
    pending_count = Order.objects.filter(status='Pending').count()
    packed_count = Order.objects.filter(status='Packed').count()
    shipped_count = Order.objects.filter(status='Shipped').count()
    delivered_count = Order.objects.filter(status='Delivered').count()
    
    context = {
        'orders': orders,
        'all_count': all_count,
        'pending_count': pending_count,
        'packed_count': packed_count,
        'shipped_count': shipped_count,
        'delivered_count': delivered_count,
        'current_status': status_filter,
    }
    return render(request, 'shop/admin_orders.html', context)

@login_required(login_url='login')
@user_passes_test(is_admin)
def admin_order_detail(request, order_id):
    """Admin view order details with action buttons"""
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'delete_order':
            order_id_to_delete = order.id
            order.delete()
            messages.success(request, f'✓ Order #{order_id_to_delete} deleted successfully!')
            return redirect('admin_orders_list')

        if action == 'update_status':
            new_status = request.POST.get('status')
            if new_status in dict(Order.STATUS_CHOICES):
                old_status = order.status
                order.status = new_status
                order.save()
                
                # Send status update email
                send_order_status_update_email(order)
                
                # Send status update SMS
                if order.phone:
                    send_order_status_sms(order)
                
                messages.success(request, f'✓ Order status updated to: {new_status}')
                return redirect('admin_order_detail', order_id=order.id)

        elif action == 'mark_paid':
            order.payment_status = True
            order.save()
            messages.success(request, '✓ Order marked as paid')
            return redirect('admin_order_detail', order_id=order.id)
        
        elif action == 'cancel_order':
            # Admin cancels order (no restrictions)
            reason = request.POST.get('reason', '').strip()
            order.status = 'Cancelled'
            order.cancelled_at = timezone.now()
            order.cancellation_reason = reason
            
            # If order was paid, set refund status to Pending
            if order.payment_status:
                order.refund_status = 'Pending'
            
            order.save()
            
            # Send notifications
            send_order_cancelled_email(order, reason=reason if reason else None)
            if order.phone:
                send_order_cancelled_sms(order, reason=reason if reason else None)
            send_admin_cancellation_alert(order, cancelled_by='Admin', reason=reason if reason else None)
            
            messages.success(request, f'✓ Order #{order.id} cancelled successfully.')
            return redirect('admin_order_detail', order_id=order.id)
        
        elif action == 'update_refund_status':
            new_refund_status = request.POST.get('refund_status')
            if new_refund_status in dict(Order.REFUND_STATUS_CHOICES):
                order.refund_status = new_refund_status
                order.save()
                messages.success(request, f'✓ Refund status updated to: {new_refund_status}')
                return redirect('admin_order_detail', order_id=order.id)

    context = {
        'order': order,
        'order_status_choices': Order.STATUS_CHOICES,
        'refund_status_choices': Order.REFUND_STATUS_CHOICES,
    }
    return render(request, 'shop/admin_order_detail.html', context)


# --- 7. WISHLIST ---

@login_required(login_url='login')
def wishlist_view(request):
    """Display user's wishlist"""
    wishlist_items = WishlistItem.objects.filter(user=request.user).select_related('product')
    return render(request, 'shop/wishlist.html', {'wishlist_items': wishlist_items})

@login_required(login_url='login')
def toggle_wishlist(request, product_id):
    """Add or remove product from wishlist (AJAX)"""
    product = get_object_or_404(Product, id=product_id)
    
    wishlist_item, created = WishlistItem.objects.get_or_create(user=request.user, product=product)
    
    if not created:
        # Already in wishlist, remove it
        wishlist_item.delete()
        is_wishlisted = False
        message = f"{product.name} removed from wishlist"
    else:
        is_wishlisted = True
        message = f"{product.name} added to wishlist"

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        wishlist_count = WishlistItem.objects.filter(user=request.user).count()
        return JsonResponse({
            'success': True,
            'is_wishlisted': is_wishlisted,
            'message': message,
            'wishlist_count': wishlist_count
        })

    messages.info(request, message)
    return redirect(request.META.get('HTTP_REFERER', 'home'))


# --- 8. REVIEW SYSTEM ---

def product_reviews(request, product_id):
    """Display all reviews for a product"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    reviews = product.reviews.filter(is_approved=True).order_by('-created_at')
    
    # Calculate rating distribution
    rating_counts = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    for review in reviews:
        rating_counts[review.rating] += 1
    
    total_reviews = reviews.count()
    avg_rating = product.average_rating()
    
    # Create rating bars data as list for easier template iteration
    rating_bars = []
    for star in [5, 4, 3, 2, 1]:
        count = rating_counts[star]
        percentage = (count / total_reviews * 100) if total_reviews > 0 else 0
        rating_bars.append({
            'star': star,
            'count': count,
            'percentage': percentage
        })
    
    context = {
        'product': product,
        'reviews': reviews,
        'rating_bars': rating_bars,
        'total_reviews': total_reviews,
        'avg_rating': avg_rating,
    }
    
    return render(request, 'shop/product_reviews.html', context)

@login_required(login_url='login')
def add_review(request, product_id):
    """Add a new review for a product"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    # Check if user already reviewed this product
    existing_review = Review.objects.filter(product=product, user=request.user).first()
    
    if existing_review:
        messages.warning(request, "You have already reviewed this product.")
        return redirect('product_reviews', product_id=product.id)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, "Thank you! Your review has been submitted.")
            return redirect('product_reviews', product_id=product.id)
    else:
        form = ReviewForm()
    
    return render(request, 'shop/add_review.html', {
        'form': form,
        'product': product,
    })