from decimal import Decimal
from urllib.parse import urlsplit

from django.core import mail
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Cart, ContactMessage, Customer, Order, OrderItem, Product, WishlistItem


class ShopFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='buyer', password='test-password-123')
        self.other_user = User.objects.create_user(username='other', password='test-password-123')
        self.product = Product.objects.create(
            title='Fresh Milk',
            selling_price=120,
            discounted_price=100,
            description='Fresh local milk',
            category='ML',
        )
        self.address = Customer.objects.create(
            user=self.user,
            name='Buyer',
            locality='Main Road',
            city='Kolhapur',
            mobile='01234567890',
            zipcode='0416001',
            state='MH',
        )
        self.other_address = Customer.objects.create(
            user=self.other_user,
            name='Other',
            locality='Other Road',
            city='Kolhapur',
            mobile='09876543210',
            zipcode='0416001',
            state='MH',
        )

    def test_products_are_browsable_without_login(self):
        self.assertEqual(self.client.get(reverse('home')).status_code, 200)
        self.assertEqual(self.client.get(reverse('category', args=['ML'])).status_code, 200)
        self.assertEqual(self.client.get(reverse('productdetail', args=[self.product.pk])).status_code, 200)
        response = self.client.get(reverse('search'), {'q': 'fresh'})
        self.assertContains(response, 'Fresh Milk')
        self.assertEqual(
            self.client.get(reverse('category-title', args=['not-a-product'])).status_code,
            404,
        )

    def test_guest_cart_actions_require_login_and_post(self):
        response = self.client.get(reverse('showcart'))
        self.assertRedirects(response, f'{reverse("login")}?next={reverse("showcart")}')
        response = self.client.post(reverse('add-to-cart'), {'prod_id': self.product.pk})
        self.assertRedirects(response, f'{reverse("login")}?next={reverse("add-to-cart")}')
        self.assertFalse(Cart.objects.exists())

    def test_cart_add_quantity_and_remove(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('add-to-cart'), {'prod_id': self.product.pk})
        self.assertRedirects(response, reverse('showcart'))
        cart_item = Cart.objects.get(user=self.user, product=self.product)
        self.assertEqual(cart_item.quantity, 1)
        self.client.post(reverse('add-to-cart'), {'prod_id': self.product.pk})
        cart_item.refresh_from_db()
        self.assertEqual(cart_item.quantity, 2)
        self.assertEqual(Cart.objects.filter(user=self.user, product=self.product).count(), 1)

        response = self.client.get(reverse('pluscart'), {'prod_id': self.product.pk})
        self.assertEqual(response.status_code, 405)
        response = self.client.post(reverse('pluscart'), {'prod_id': self.product.pk})
        self.assertEqual(response.json(), {'quantity': 3, 'amount': '300.00', 'totalamount': '340.00'})
        response = self.client.post(reverse('minuscart'), {'prod_id': self.product.pk})
        self.assertEqual(response.json()['quantity'], 2)
        self.client.post(reverse('removecart'), {'prod_id': self.product.pk})
        self.assertFalse(Cart.objects.filter(user=self.user).exists())

    def test_cart_is_private_to_each_customer(self):
        self.client.force_login(self.user)
        Cart.objects.create(user=self.user, product=self.product)
        Cart.objects.create(user=self.other_user, product=self.product)
        self.client.post(reverse('removecart'), {'prod_id': self.product.pk})
        self.assertFalse(Cart.objects.filter(user=self.user).exists())
        self.assertTrue(Cart.objects.filter(user=self.other_user).exists())

    def test_cart_rejects_invalid_product_id(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('add-to-cart'), {'prod_id': 'invalid'})
        self.assertEqual(response.status_code, 400)
        response = self.client.post(reverse('pluscart'), {'prod_id': 'invalid'})
        self.assertEqual(response.status_code, 400)

    def test_wishlist_is_private_and_duplicate_adds_are_idempotent(self):
        response = self.client.get(reverse('wishlist'))
        self.assertRedirects(response, f'{reverse("login")}?next={reverse("wishlist")}')

        self.client.force_login(self.user)
        response = self.client.post(reverse('add-to-wishlist'), {'prod_id': self.product.pk})
        self.assertRedirects(response, reverse('wishlist'))
        self.client.post(reverse('add-to-wishlist'), {'prod_id': self.product.pk})
        self.assertEqual(WishlistItem.objects.filter(user=self.user).count(), 1)

        item = WishlistItem.objects.get(user=self.user, product=self.product)
        self.client.force_login(self.other_user)
        self.client.post(reverse('remove-from-wishlist'), {'item_id': item.pk})
        self.assertTrue(WishlistItem.objects.filter(pk=item.pk).exists())

        self.client.force_login(self.user)
        self.client.post(reverse('remove-from-wishlist'), {'item_id': item.pk})
        self.assertFalse(WishlistItem.objects.filter(pk=item.pk).exists())

    def test_checkout_creates_cod_order_and_clears_cart(self):
        self.client.force_login(self.user)
        cart_item = Cart.objects.create(user=self.user, product=self.product, quantity=2)

        response = self.client.post(reverse('checkout'), {'custid': self.address.pk})
        order = Order.objects.get(user=self.user)
        self.assertRedirects(response, reverse('order-detail', args=[order.pk]))
        self.assertEqual(order.payment_method, 'COD')
        self.assertEqual(order.status, 'PENDING')
        self.assertEqual(order.total_amount, Decimal('240.00'))
        self.assertEqual(order.delivery_name, self.address.name)
        self.assertEqual(list(order.items.values_list('product_title', 'quantity', 'unit_price')),
                         [('Fresh Milk', 2, Decimal('100.00'))])
        self.assertFalse(Cart.objects.filter(pk=cart_item.pk).exists())
        self.assertContains(self.client.get(reverse('orders')), f'Order #{order.pk}')

    def test_checkout_cannot_use_another_users_address(self):
        self.client.force_login(self.user)
        cart_item = Cart.objects.create(user=self.user, product=self.product)
        response = self.client.post(reverse('checkout'), {'custid': self.other_address.pk})
        self.assertEqual(response.status_code, 404)
        self.assertFalse(Order.objects.exists())
        self.assertTrue(Cart.objects.filter(pk=cart_item.pk).exists())

    def test_order_detail_is_private(self):
        order = Order.objects.create(
            user=self.user,
            delivery_name='Buyer',
            delivery_address='Main Road, Kolhapur',
            delivery_mobile='1234567890',
            total_amount=Decimal('140.00'),
        )
        self.client.force_login(self.other_user)
        self.assertEqual(self.client.get(reverse('order-detail', args=[order.pk])).status_code, 404)

    def test_address_update_cannot_modify_another_users_address(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('updateAddress', args=[self.other_address.pk]),
            {'name': 'Changed', 'locality': 'Changed', 'city': 'Kolhapur',
             'mobile': '01234567890', 'zipcode': '0416001', 'state': 'MH'},
        )
        self.assertEqual(response.status_code, 404)
        self.other_address.refresh_from_db()
        self.assertEqual(self.other_address.name, 'Other')

    def test_customer_can_update_own_address(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('updateAddress', args=[self.address.pk]),
            {'name': 'Buyer Updated', 'locality': 'New Road', 'city': 'Kolhapur',
             'mobile': '00123456789', 'zipcode': '0416001', 'state': 'MH'},
        )
        self.assertRedirects(response, reverse('address'))
        self.address.refresh_from_db()
        self.assertEqual(self.address.name, 'Buyer Updated')
        self.assertEqual(self.address.mobile, '00123456789')

    def test_address_delete_is_post_only_and_private(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('delete-address', args=[self.address.pk])).status_code, 405)

        response = self.client.post(reverse('delete-address', args=[self.other_address.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Customer.objects.filter(pk=self.other_address.pk).exists())

        response = self.client.post(reverse('delete-address', args=[self.address.pk]))
        self.assertRedirects(response, reverse('address'))
        self.assertFalse(Customer.objects.filter(pk=self.address.pk).exists())
        self.assertContains(self.client.get(reverse('address')), "You haven't saved a delivery address yet.")

    def test_contact_form_saves_valid_message(self):
        response = self.client.post(reverse('contact'), {
            'name': 'Visitor',
            'email': 'visitor@example.com',
            'message': 'Please call me.',
        })
        self.assertRedirects(response, reverse('contact'))
        self.assertEqual(ContactMessage.objects.get().email, 'visitor@example.com')
        response = self.client.post(reverse('contact'), {'name': '', 'email': 'not-an-email', 'message': ''})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 1)

    def test_registration_creates_user_and_redirects_to_login(self):
        response = self.client.post(reverse('customerregistrationview'), {
            'username': 'newbuyer',
            'email': 'newbuyer@example.com',
            'password1': 'R4ndom!Pass-2026',
            'password2': 'R4ndom!Pass-2026',
        })
        self.assertRedirects(response, reverse('login'))
        self.assertTrue(User.objects.filter(username='newbuyer').exists())

    def test_profile_saves_address_and_preserves_leading_zeroes(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('profile'), {
            'name': 'Buyer',
            'locality': 'Main Road',
            'city': 'Kolhapur',
            'mobile': '00123456789',
            'zipcode': '0416001',
            'state': 'MH',
        })
        self.assertRedirects(response, reverse('address'))
        address = Customer.objects.get(user=self.user, mobile='00123456789')
        self.assertEqual(address.zipcode, '0416001')

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_password_reset_renders_and_sends_reset_email(self):
        self.user.email = 'buyer@example.com'
        self.user.save(update_fields=['email'])
        response = self.client.post(reverse('password_reset'), {'email': self.user.email})
        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('/password-reset-confirm/', mail.outbox[0].body)

        reset_url = next(
            line for line in mail.outbox[0].body.splitlines()
            if '/password-reset-confirm/' in line
        )
        reset_path = urlsplit(reset_url).path
        response = self.client.get(reset_path, follow=True)
        self.assertContains(response, 'Set new password')
        reset_path = response.request['PATH_INFO']

        new_password = 'Different!Pass-2026'
        response = self.client.post(reset_path, {
            'new_password1': new_password,
            'new_password2': new_password,
        })
        self.assertRedirects(response, reverse('password_reset_complete'))
        self.assertTrue(self.client.login(username='buyer', password=new_password))

    def test_invalid_password_reset_token_has_recovery_action(self):
        response = self.client.get(
            reverse('password_reset_confirm', args=['invalid-uid', 'invalid-token'])
        )
        self.assertContains(response, 'Request a new reset link')
        self.assertNotContains(response, 'Set new password')

    def test_authenticated_customer_can_change_password(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('passwordchange'), {
            'old_password': 'test-password-123',
            'new_password1': 'New!Secure-Pass-2026',
            'new_password2': 'New!Secure-Pass-2026',
        })
        self.assertRedirects(response, reverse('passwordchangedone'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('New!Secure-Pass-2026'))

    def test_login_page_contains_valid_registration_link_markup(self):
        response = self.client.get(reverse('login'))
        self.assertContains(response, 'class="text-danger">Create an Account</a>')
