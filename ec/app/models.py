from django.core.validators import RegexValidator
from django.db import models
from django.contrib.auth.models import User
STATE_CHOICES = (
    ('MH', 'Maharashtra'),
    ('GJ', 'Gujarat'),
    ('DL', 'Delhi'),
    ('KA', 'Karnataka'),
    ('TN', 'Tamil Nadu'),
    ('UP', 'Uttar Pradesh'),
    ('RJ', 'Rajasthan'),
    ('WB', 'West Bengal'),
    ('KL', 'Kerala'),
    ('PB', 'Punjab'),
    ('MP', 'Madhya Pradesh'),
)

# Create your models here.
CATEGORY_CHOICES=(
    ('CR','Curd'),
    ('ML','Milk'),
    ('LS','Lassi'),
    ('MS','Milkshake'), 
    ('PN','Paneer'),
    ('GH','Ghee'),
    ('CZ','Cheese'),
    ('IC','Ice-Creams'),

)


class Product(models.Model):
    title= models.CharField(max_length=100)
    selling_price=models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    composition=models.TextField(default='')
    prodapp=models.TextField(default='')
    category=models.CharField(choices=CATEGORY_CHOICES, max_length=2)
    product_image=models.ImageField(upload_to='product')

    def __str__(self):
        return self.title
    

class Customer(models.Model):
    user = models.ForeignKey(User , on_delete=models.CASCADE)
    name= models.CharField(max_length=200)
    locality = models.CharField(max_length=200)
    city = models.CharField(max_length=50)
    mobile = models.CharField(
        max_length=16,
        validators=[RegexValidator(r'^\+?[0-9]{7,15}$', 'Enter a valid phone number.')],
    )
    zipcode = models.CharField(max_length=10)
    state =  models.CharField(choices=STATE_CHOICES, max_length=100)
    def __str__(self):
        return self.name
    
class Cart(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'product'], name='unique_cart_user_product'),
        ]

    @property
    def total_cost(self):
        return self.quantity * self.product.discounted_price


class WishlistItem(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='wishlist_items'
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'product'], name='unique_wishlist_user_product'),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} - {self.product}'


class Order(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    payment_method = models.CharField(max_length=20, default='COD')
    delivery_name = models.CharField(max_length=200)
    delivery_address = models.TextField()
    delivery_mobile = models.CharField(max_length=20)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=40)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Order #{self.pk} - {self.user}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL)
    product_title = models.CharField(max_length=100)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    @property
    def total_cost(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f'{self.product_title} x {self.quantity}'


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Message from {self.name} ({self.email})'