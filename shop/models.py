from django.db import models
from django.contrib.auth.models import User

class Product(models.Model):
    CATEGORY_CHOICES = (
        ('jewelry', 'Jewelry'),
        ('home-decor', 'Home Decor'),
        ('textiles', 'Textiles'),
        ('pottery', 'Pottery'),
        ('bags', 'Bags & Accessories'),
        ('other', 'Other'),
    )

    name = models.CharField(max_length=200)
    price = models.IntegerField()
    description = models.TextField()
    image = models.ImageField(upload_to='products')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def average_rating(self):
        reviews = self.reviews.filter(is_approved=True)
        if reviews.exists():
            return round(reviews.aggregate(models.Avg('rating'))['rating__avg'], 1)
        return 0

    def review_count(self):
        return self.reviews.filter(is_approved=True).count()

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    title = models.CharField(max_length=200)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review by {self.user.username} for {self.product.name}"

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    @property
    def item_total(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

class OrderItem(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of order

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Order {self.order.id}"

    @property
    def item_total(self):
        return self.price * self.quantity


class WishlistItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.username}'s wishlist: {self.product.name}"


class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Packed', 'Packed'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    )
    
    REFUND_STATUS_CHOICES = (
        ('None', 'None'),
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
    )

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=6)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.BooleanField(default=False)
    razorpay_order_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Cancellation fields
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True, default='')
    refund_status = models.CharField(max_length=20, choices=REFUND_STATUS_CHOICES, default='None')

    def __str__(self):
        return f"Order {self.id} - {self.full_name}"
