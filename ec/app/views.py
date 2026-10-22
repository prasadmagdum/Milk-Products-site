from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F, Q
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .forms import ContactMessageForm, CustomerProfileForm, CustomerRegistrationFrom
from .models import Cart, Customer, Order, OrderItem, Product, WishlistItem

SHIPPING_COST = 40


def _cart_totals(cart):
    amount = sum(
        (Decimal(str(item.product.discounted_price)) * item.quantity for item in cart),
        Decimal('0.00'),
    ).quantize(Decimal('0.01'))
    shipping = Decimal(str(SHIPPING_COST)) if cart else Decimal('0.00')
    return cart, amount, shipping, amount + shipping


def _cart_summary(user):
    cart = list(Cart.objects.filter(user=user).select_related('product'))
    return _cart_totals(cart)


def home(request):
    return render(request, "app/home.html")


def about(request):
    return render(request, "app/about.html")


def contact(request):
    if request.method == 'POST':
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Thanks for contacting us. Your message has been received.")
            return redirect('contact')
    else:
        form = ContactMessageForm()
    return render(request, "app/contact.html", {'form': form})


def search(request):
    query = request.GET.get('q', '').strip()
    products = Product.objects.none()
    if query:
        products = Product.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )
    return render(request, 'app/search.html', {'products': products, 'query': query})


class categoryView(View):
    def get(self, request, val):
        product = Product.objects.filter(category=val)
        title = product.values('title').distinct()
        return render(request, "app/category.html", {'product': product, 'title': title})


class categoryTitle(View):
    def get(self, request, val):
        matching_product = get_object_or_404(Product, title__iexact=val)
        product = Product.objects.filter(
            category=matching_product.category, title__iexact=matching_product.title
        )
        title = Product.objects.filter(category=matching_product.category).values('title').distinct()
        return render(request, "app/category.html", {'product': product, 'title': title})


class ProductDetail(View):
    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        return render(request, "app/productdetail.html", {'product': product})


class CustomerRegistrationView(View):
    def get(self, request):
        form = CustomerRegistrationFrom()
        return render(request, 'app/customerregistration.html', {'form': form})

    def post(self, request):
        form = CustomerRegistrationFrom(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your account was created successfully. You can now log in.")
            return redirect('login')
        return render(request, 'app/customerregistration.html', {'form': form})


@method_decorator(login_required, name='dispatch')
class ProfileView(View):
    def get(self, request):
        form = CustomerProfileForm()
        return render(request, 'app/profile.html', {'form': form})

    def post(self, request):
        form = CustomerProfileForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.user = request.user
            customer.save()
            messages.success(request, "Your address was saved successfully.")
            return redirect('address')
        return render(request, 'app/profile.html', {'form': form})


@login_required
def address(request):
    add = Customer.objects.filter(user=request.user)
    return render(request, 'app/address.html', {'add': add})


@method_decorator(login_required, name='dispatch')
class updateAddress(View):
    def get(self, request, pk):
        customer = get_object_or_404(Customer, pk=pk, user=request.user)
        form = CustomerProfileForm(instance=customer)
        return render(request, 'app/updateAddress.html', {'form': form})

    def post(self, request, pk):
        customer = get_object_or_404(Customer, pk=pk, user=request.user)
        form = CustomerProfileForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, "Your address was updated successfully.")
            return redirect('address')
        return render(request, 'app/updateAddress.html', {'form': form})


@login_required
@require_POST
def add_to_cart(request):
    product_id = request.POST.get('prod_id', '')
    if not product_id.isdecimal():
        return HttpResponseBadRequest('Invalid product.')
    product = get_object_or_404(Product, pk=product_id)
    cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)
    if not created:
        Cart.objects.filter(pk=cart_item.pk).update(quantity=F('quantity') + 1)
    messages.success(request, f'{product.title} was added to your cart.')
    next_url = request.POST.get('next', '')
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(next_url)
    return redirect('showcart')


@login_required
@ensure_csrf_cookie
def show_cart(request):
    cart, amount, shipping, totalamount = _cart_summary(request.user)
    return render(request, 'app/addtocart.html', {
        'cart': cart,
        'amount': amount,
        'shipping': shipping,
        'totalamount': totalamount,
    })


@method_decorator(login_required, name='dispatch')
class checkout(View):
    def get(self, request):
        cart_items, amount, shipping, totalamount = _cart_summary(request.user)
        if not cart_items:
            messages.info(request, "Your cart is empty.")
            return redirect('showcart')
        add = Customer.objects.filter(user=request.user)
        return render(request, 'app/checkout.html', {
            'add': add,
            'cart_items': cart_items,
            'amount': amount,
            'shipping': shipping,
            'totalamount': totalamount,
        })

    def post(self, request):
        customer_id = request.POST.get('custid', '')
        if not customer_id.isdecimal():
            messages.error(request, "Please select a valid delivery address.")
            return redirect('checkout')
        with transaction.atomic():
            cart_items = list(
                Cart.objects.filter(user=request.user)
                .select_related('product')
                .select_for_update()
            )
            if not cart_items:
                messages.error(request, "Your cart is empty.")
                return redirect('showcart')
            _, amount, shipping, totalamount = _cart_totals(cart_items)
            customer = get_object_or_404(
                Customer, pk=customer_id, user=request.user
            )
            order = Order.objects.create(
                user=request.user,
                delivery_name=customer.name,
                delivery_address=(
                    f'{customer.locality}, {customer.city}, {customer.state} - {customer.zipcode}'
                ),
                delivery_mobile=str(customer.mobile),
                shipping_cost=Decimal(str(shipping)),
                total_amount=Decimal(str(totalamount)),
                payment_method='COD',
            )
            OrderItem.objects.bulk_create([
                OrderItem(
                    order=order,
                    product=item.product,
                    product_title=item.product.title,
                    unit_price=Decimal(str(item.product.discounted_price)),
                    quantity=item.quantity,
                )
                for item in cart_items
            ])
            Cart.objects.filter(user=request.user).delete()

        messages.success(request, f'Order #{order.pk} was placed successfully. Payment is due on delivery.')
        return redirect('order-detail', pk=order.pk)


@login_required
def orders(request):
    order_list = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'app/orders.html', {'orders': order_list})


@login_required
def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.prefetch_related('items'), pk=pk, user=request.user
    )
    return render(request, 'app/order_detail.html', {'order': order})


@login_required
def wishlist(request):
    items = WishlistItem.objects.filter(user=request.user).select_related('product')
    return render(request, 'app/wishlist.html', {'items': items})


@login_required
@require_POST
def add_to_wishlist(request):
    product_id = request.POST.get('prod_id', '')
    if not product_id.isdecimal():
        return HttpResponseBadRequest('Invalid product.')
    product = get_object_or_404(Product, pk=product_id)
    WishlistItem.objects.get_or_create(user=request.user, product=product)
    messages.success(request, f'{product.title} was saved to your wishlist.')
    return redirect('wishlist')


@login_required
@require_POST
def remove_from_wishlist(request):
    item_id = request.POST.get('item_id', '')
    if not item_id.isdecimal():
        return HttpResponseBadRequest('Invalid wishlist item.')
    WishlistItem.objects.filter(pk=item_id, user=request.user).delete()
    return redirect('wishlist')


def _cart_response(user, quantity=None):
    _, amount, _, totalamount = _cart_summary(user)
    data = {'amount': amount, 'totalamount': totalamount}
    if quantity is not None:
        data['quantity'] = quantity
    return JsonResponse(data)


@login_required
@require_POST
def plus_cart(request):
    product_id = request.POST.get('prod_id', '')
    if not product_id.isdecimal():
        return JsonResponse({'error': 'Invalid product.'}, status=400)
    cart_item = get_object_or_404(
        Cart, product_id=product_id, user=request.user
    )
    Cart.objects.filter(pk=cart_item.pk).update(quantity=F('quantity') + 1)
    cart_item.refresh_from_db(fields=['quantity'])
    return _cart_response(request.user, cart_item.quantity)


@login_required
@require_POST
def minus_cart(request):
    product_id = request.POST.get('prod_id', '')
    if not product_id.isdecimal():
        return JsonResponse({'error': 'Invalid product.'}, status=400)
    cart_item = get_object_or_404(
        Cart, product_id=product_id, user=request.user
    )
    Cart.objects.filter(pk=cart_item.pk, quantity__gt=1).update(
        quantity=F('quantity') - 1
    )
    cart_item.refresh_from_db(fields=['quantity'])
    return _cart_response(request.user, cart_item.quantity)


@login_required
@require_POST
def remove_cart(request):
    product_id = request.POST.get('prod_id', '')
    if not product_id.isdecimal():
        return JsonResponse({'error': 'Invalid product.'}, status=400)
    Cart.objects.filter(product_id=product_id, user=request.user).delete()
    return _cart_response(request.user)
