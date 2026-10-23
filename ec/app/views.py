from decimal import Decimal

from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from django.http import Http404, HttpResponseBadRequest, JsonResponse
from django.db import transaction
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.conf import settings
from .forms import CheckoutAddressForm, ContactForm, CustomerProfileForm, CustomerRegistrationFrom
from django.contrib import messages
from .models import Cart, ContactMessage, Customer, Order, OrderItem, Product, SHIPPING_COST, WishlistItem


def _cart_totals(cart_items):
    amount = sum(
        (item.quantity * item.product.discounted_price for item in cart_items),
        start=Decimal('0.00'),
    )
    return amount, amount + SHIPPING_COST if cart_items else Decimal('0.00')

# Create your views here.
def home(request):
    return render(request,"app/home.html")

def about(request):
    return render(request,"app/about.html")

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact_message = ContactMessage.objects.create(**form.cleaned_data)
            EmailMessage(
                subject=f"Contact form message #{contact_message.pk}",
                body=f"From: {contact_message.name} <{contact_message.email}>\n\n{contact_message.message}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[settings.CONTACT_RECIPIENT_EMAIL],
                reply_to=[contact_message.email],
            ).send(fail_silently=False)
            messages.success(request, "Thank you for contacting us. Your message has been sent.")
            return redirect('contact')
    else:
        form = ContactForm()
    return render(request, "app/contact.html", {'form': form})


def product_search(request):
    query = request.GET.get('q', '').strip()
    product = Product.objects.filter(
        Q(title__icontains=query) | Q(description__icontains=query)
    ) if query else Product.objects.none()
    return render(request, "app/category.html", {
        'product': product,
        'title': [],
        'page_title': 'Search results',
        'query': query,
    })

class categoryView(View):
    def get(self,request,val):
        categories = dict(Product._meta.get_field('category').choices)
        if val not in categories:
            raise Http404("Product category not found")
        product = Product.objects.filter(category=val)
        title = product.values('title').distinct().order_by('title')
        return render(request, "app/category.html", {
            'product': product,
            'title': title,
            'page_title': categories[val],
            'category_code': val,
        })
    

class categoryTitle(View):
    def get(self,request,val):
        products = Product.objects.filter(title=val)
        category_code = request.GET.get('category')
        categories = dict(Product._meta.get_field('category').choices)
        if category_code:
            if category_code not in categories:
                raise Http404("Product category not found")
            products = products.filter(category=category_code)

        selected_product = products.order_by('pk').first()
        if selected_product is None:
            raise Http404("Product title not found")
        category_code = selected_product.category
        product = products.filter(category=category_code)
        title = Product.objects.filter(category=category_code).values('title').distinct().order_by('title')
        return render(request, "app/category.html", {
            'product': product,
            'title': title,
            'page_title': categories[category_code],
            'category_code': category_code,
        })
    
class ProductDetail(View):
    def get (self,request,pk):
        product = get_object_or_404(Product, pk=pk)
        in_wishlist = request.user.is_authenticated and WishlistItem.objects.filter(
            user=request.user,
            product=product,
        ).exists()
        return render(request, "app/productdetail.html", {
            'product': product,
            'in_wishlist': in_wishlist,
        })
    
class CustomerRegistrationView(View):
    def get(self,request):
        form = CustomerRegistrationFrom()
        return render(request, 'app/customerregistration.html',locals() )
    def post(self, request):
        form = CustomerRegistrationFrom(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registration successful. Please log in.")
            return redirect('login')
        return render(request, 'app/customerregistration.html',locals())

@method_decorator(login_required, name='dispatch')
class ProfileView(View):
    def get(self,request):
        form = CustomerProfileForm()
        return render (request , 'app/profile.html', locals())
    
    def post(self , request):
        form=CustomerProfileForm(request.POST)
        if form.is_valid():
            user = request.user
            Customer.objects.create(user=user, **form.cleaned_data)
            messages.success(request, "Address saved successfully.")
            return redirect('address')
        return render(request, 'app/profile.html', locals())

@login_required
def address(request):
    add = Customer.objects.filter(user=request.user)
    return render(request, 'app/address.html', locals())

@login_required
@require_POST
def delete_address(request, pk):
    customer = get_object_or_404(Customer, pk=pk, user=request.user)
    customer.delete()
    messages.success(request, "The delivery address was deleted.")
    return redirect('address')


@method_decorator(login_required, name='dispatch')
class updateAddress(View):
    def get(self, request,pk):
        add = get_object_or_404(Customer, pk=pk, user=request.user)
        form=CustomerProfileForm(instance=add)
        return render(request,'app/updateAddress.html',locals())
    def post(self, request ,pk ):
        add = get_object_or_404(Customer, pk=pk, user=request.user)
        form=CustomerProfileForm(request.POST, instance=add)
        if form.is_valid():
            form.save()
            messages.success(request, "Address updated successfully.")
            return redirect("address")
        return render(request, 'app/updateAddress.html', locals())

@login_required
@require_POST
def add_to_cart(request):
    product = get_object_or_404(Product, pk=request.POST.get('prod_id'))
    cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save(update_fields=['quantity'])
    return redirect("showcart")

@login_required
def show_cart(request):
    cart = Cart.objects.filter(user=request.user).select_related('product')
    amount, totalamount = _cart_totals(cart)
    return render(request, 'app/addtocart.html', {
        'cart': cart,
        'amount': amount,
        'totalamount': totalamount,
        'shipping_cost': SHIPPING_COST if cart else 0,
    })

@method_decorator(login_required, name='dispatch')
class checkout(View):
    def get(self, request):
        cart_items = list(Cart.objects.filter(user=request.user).select_related('product'))
        if not cart_items:
            messages.info(request, "Your cart is empty.")
            return redirect('showcart')
        add = Customer.objects.filter(user=request.user)
        amount, totalamount = _cart_totals(cart_items)
        if not add.exists():
            messages.info(request, "Add a shipping address before checkout.")
            return redirect('profile')
        return render(request, 'app/checkout.html', {
            'add': add,
            'cart_items': cart_items,
            'amount': amount,
            'shipping_cost': SHIPPING_COST,
            'totalamount': totalamount,
        })

    def post(self, request):
        form = CheckoutAddressForm(request.POST, user=request.user)
        if not form.is_valid():
            messages.error(request, "Select a valid shipping address to continue.")
            return redirect('checkout')
        address = form.cleaned_data['custid']

        with transaction.atomic():
            cart_items = list(
                Cart.objects.filter(user=request.user).select_related('product').select_for_update()
            )
            if not cart_items:
                messages.info(request, "Your cart is empty.")
                return redirect('showcart')
            amount, totalamount = _cart_totals(cart_items)
            order = Order.objects.create(
                user=request.user,
                delivery_name=address.name,
                delivery_address=f'{address.locality}, {address.city}, {address.get_state_display()} {address.zipcode}',
                delivery_mobile=address.mobile,
                shipping_cost=SHIPPING_COST,
                total_amount=totalamount,
                payment_method=Order.PAYMENT_COD,
            )
            OrderItem.objects.bulk_create([
                OrderItem(
                    order=order,
                    product=item.product,
                    product_title=item.product.title,
                    unit_price=item.product.discounted_price,
                    quantity=item.quantity,
                )
                for item in cart_items
            ])
            Cart.objects.filter(user=request.user).delete()

        messages.success(request, f"Order #{order.pk} was placed. Payment is pending.")
        return redirect('orders')

@login_required
def orders(request):
    order_list = Order.objects.filter(user=request.user).prefetch_related('items')
    return render(request, 'app/orders.html', {'orders': order_list})

@login_required
def wishlist(request):
    items = WishlistItem.objects.filter(user=request.user).select_related('product')
    return render(request, 'app/wishlist.html', {'wishlist_items': items})

@login_required
@require_POST
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    WishlistItem.objects.get_or_create(user=request.user, product=product)
    messages.success(request, f'{product.title} was added to your wishlist.')
    return redirect('productdetail', pk=product.pk)

@login_required
@require_POST
def remove_from_wishlist(request, product_id):
    item = get_object_or_404(WishlistItem, user=request.user, product_id=product_id)
    item.delete()
    messages.success(request, 'Product removed from your wishlist.')
    return redirect('wishlist')

@login_required
@require_POST
def plus_cart(request):
    product_id = request.POST.get('prod_id')
    if not product_id:
        return HttpResponseBadRequest("Missing product id.")
    cart_item = get_object_or_404(Cart, product_id=product_id, user=request.user)
    cart_item.quantity += 1
    cart_item.save(update_fields=['quantity'])
    return _cart_response(request.user, cart_item)

@login_required
@require_POST
def minus_cart(request):
    product_id = request.POST.get('prod_id')
    if not product_id:
        return HttpResponseBadRequest("Missing product id.")
    cart_item = get_object_or_404(Cart, product_id=product_id, user=request.user)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save(update_fields=['quantity'])
    return _cart_response(request.user, cart_item)

@login_required
@require_POST
def remove_cart(request):
    product_id = request.POST.get('prod_id')
    if not product_id:
        return HttpResponseBadRequest("Missing product id.")
    get_object_or_404(Cart, product_id=product_id, user=request.user).delete()
    return _cart_response(request.user)


def _cart_response(user, cart_item=None):
    cart = Cart.objects.filter(user=user).select_related('product')
    amount, totalamount = _cart_totals(cart)
    data = {'amount': amount, 'totalamount': totalamount}
    if cart_item is not None:
        data['quantity'] = cart_item.quantity
    return JsonResponse(data)