from django.contrib import admin
from . models import Cart, Product , Customer

# Register your models here.
@admin.register(Product)
class ProductModelAdmin(admin.ModelAdmin):
    list_display=['id','title','discounted_price','category','product_image']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'name', 'locality', 'city', 'mobile', 'zipcode', 'state']
    search_fields = ['name', 'city', 'state']
    list_filter = ['state', 'city']

@admin.register(Cart)
class CartModelAdmin(admin.ModelAdmin):
    list_display=[ 'id','user', 'product', 'quantity']