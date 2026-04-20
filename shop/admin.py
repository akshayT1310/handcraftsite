# shop/admin.py

from django.contrib import admin
from .models import Product, Order, OrderItem, CartItem
from django.contrib import admin
from .models import *


class ProductAdmin(admin.ModelAdmin):
    # Sirf wahi fields rakhein jo aapne models.py mein Product model mein di hain
    # Example: Agar sirf name aur price hai, toh wahi likhein
    list_display = ('name', 'price', 'created_at')
    search_fields = ('name',)
    list_filter = ('created_at',)
    list_editable = ('price',) # Stock hata diya kyunki error aa raha tha

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price', 'item_total')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

class OrderAdmin(admin.ModelAdmin):
    # Agar Order model mein status nahi hai, toh ise bhi list_display se hata dein
    list_display = ('id', 'full_name', 'email', 'phone', 'total_amount', 'payment_status', 'status', 'created_at')
    search_fields = ('full_name', 'email', 'phone')
    list_filter = ('status', 'payment_status', 'created_at')
    inlines = [OrderItemInline]
    readonly_fields = ('created_at', 'cancelled_at')

    fieldsets = (
        ('Customer Information', {
            'fields': ('user', 'full_name', 'email', 'phone')
        }),
        ('Shipping Address', {
            'fields': ('address', 'city', 'pincode')
        }),
        ('Order Details', {
            'fields': ('total_amount', 'payment_status', 'status', 'razorpay_order_id', 'created_at')
        }),
        ('Cancellation Information', {
            'fields': ('cancelled_at', 'cancellation_reason', 'refund_status'),
            'classes': ('collapse',),
        }),
    )
from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price')
    
admin.site.register(Order, OrderAdmin)
admin.site.register(CartItem) # Simple register