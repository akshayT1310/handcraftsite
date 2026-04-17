from django.urls import path
from . import views

urlpatterns = [
    # Default Homepage - Beautiful Intro/Landing
    path('', views.home, name='home'),
    path('home/', views.home, name='home'),  # Alias for /home/
    
    # Shop/Products Page (Product Catalog)
    path('shop/', views.shop_page, name='shop'),
    
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    
    # Reviews
    path('product/<int:product_id>/reviews/', views.product_reviews, name='product_reviews'),
    path('product/<int:product_id>/add-review/', views.add_review, name='add_review'),

    # Registration & Login
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Customer Profile
    path('profile/', views.customer_profile, name='customer_profile'),
    path('profile/update-phone/', views.update_phone, name='update_phone'),

    # Shopping Cart
    path('cart/', views.cart_view, name='cart_view'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('update-cart/<int:item_id>/<str:action>/', views.update_cart, name='update_cart'),
    path('remove-item/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),

    # Checkout & Payment
    path('checkout/', views.checkout, name='checkout'),
    path('payment/', views.payment_view, name='payment_view'),
    path('thanks/', views.thanks, name='thanks'),

    # Orders
    path('my-orders/', views.my_orders, name='my_orders'),
    path('orders/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),

    # Wishlist
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),

    # Product Management (Admin)
    path('products/manage/', views.product_list_admin, name='product_list_admin'),
    path('products/add/', views.add_product, name='add_product'),
    path('products/<int:product_id>/edit/', views.edit_product, name='edit_product'),
    path('products/<int:product_id>/delete/', views.delete_product, name='delete_product'),

    # Order Management (Admin)
    path('orders/manage/', views.admin_orders_list, name='admin_orders_list'),
    path('orders/<int:order_id>/', views.admin_order_detail, name='admin_order_detail'),
]
