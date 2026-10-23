from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from decimal import Decimal
from urllib.parse import urlsplit

from .models import Cart, ContactMessage, Customer, Order, OrderItem, Product, WishlistItem


class StoreFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='Strong-password-123',
        )
        self.other_user = User.objects.create_user(username='other', password='Strong-password-123')
        self.product = Product.objects.create(
            title='Fresh Milk',
            selling_price=Decimal('60.00'),
            discounted_price=Decimal('50.00'),
            description='Fresh dairy milk',
            category='ML',
            product_image='product/fresh-milk.png',
        )
        self.address = Customer.objects.create(
            user=self.user,
            name='Customer',
            locality='Main Road',
            city='Kolhapur',
            mobile='1234567890',
            zipcode='416001',
            state='MH',
        )

    def test_catalog_and_search_are_available_without_login(self):
        self.assertEqual(self.client.get(reverse('home')).status_code, 200)
        self.assertEqual(self.client.get(reverse('category', args=['ML'])).status_code, 200)
        self.assertEqual(self.client.get(reverse('productdetail', args=[self.product.pk])).status_code, 200)
        response = self.client.get(reverse('product-search'), {'q': 'milk'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Fresh Milk')

    def test_unknown_category_and_product_return_404(self):
        self.assertEqual(self.client.get(reverse('category', args=['XX'])).status_code, 404)
        self.assertEqual(self.client.get(reverse('productdetail', args=[999])).status_code, 404)

    def test_cart_mutations_require_authentication_and_post(self):
        add_url = reverse('add-to-cart')
        self.assertEqual(self.client.post(add_url, {'prod_id': self.product.pk}).status_code, 302)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(add_url, {'prod_id': self.product.pk}).status_code, 405)
        self.client.post(add_url, {'prod_id': self.product.pk})
        self.client.post(add_url, {'prod_id': self.product.pk})
        self.assertEqual(Cart.objects.get(user=self.user, product=self.product).quantity, 2)

        response = self.client.post(reverse('minuscart'), {'prod_id': self.product.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['quantity'], 1)
        response = self.client.post(reverse('removecart'), {'prod_id': self.product.pk})
        self.assertEqual(response.json()['totalamount'], '0.00')
        self.assertFalse(Cart.objects.filter(user=self.user).exists())

    def test_checkout_creates_order_from_server_cart_and_clears_cart(self):
        self.client.force_login(self.user)
        Cart.objects.create(user=self.user, product=self.product, quantity=2)

        response = self.client.post(reverse('checkout'), {
            'custid': self.address.pk,
            'totamount': '0',
        })

        self.assertRedirects(response, reverse('orders'))
        order = Order.objects.get(user=self.user)
        self.assertEqual(order.subtotal, Decimal('100.00'))
        self.assertEqual(order.shipping_cost, Decimal('40.00'))
        self.assertEqual(order.total_amount, Decimal('140.00'))
        self.assertEqual(order.status, Order.STATUS_PENDING)
        self.assertEqual(order.payment_method, Order.PAYMENT_COD)
        self.assertIn('Kolhapur', order.delivery_address)
        self.assertEqual(order.delivery_mobile, self.address.mobile)
        self.assertEqual(OrderItem.objects.get(order=order).quantity, 2)
        self.assertFalse(Cart.objects.filter(user=self.user).exists())

    def test_checkout_rejects_another_users_address(self):
        self.client.force_login(self.user)
        Cart.objects.create(user=self.user, product=self.product)
        other_address = Customer.objects.create(
            user=self.other_user,
            name='Other Customer',
            locality='Other Road',
            city='Pune',
            mobile='1234567890',
            zipcode='411001',
            state='MH',
        )
        response = self.client.post(reverse('checkout'), {'custid': other_address.pk})
        self.assertRedirects(response, reverse('checkout'))
        self.assertFalse(Order.objects.exists())
        self.assertTrue(Cart.objects.filter(user=self.user).exists())

    def test_address_cannot_be_read_or_updated_by_another_user(self):
        self.client.force_login(self.other_user)
        self.assertEqual(self.client.get(reverse('updateAddress', args=[self.address.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse('address')).status_code, 200)
        self.assertNotContains(self.client.get(reverse('address')), 'Main Road')

    def test_profile_and_address_update_save_customer_addresses(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('profile'), {
            'name': 'Second Address',
            'locality': 'Market Road',
            'city': 'Kolhapur',
            'mobile': '1234567890',
            'zipcode': '416002',
            'state': 'MH',
        })
        self.assertRedirects(response, reverse('address'))
        self.assertEqual(Customer.objects.filter(user=self.user).count(), 2)

        response = self.client.post(reverse('updateAddress', args=[self.address.pk]), {
            'name': 'Updated Customer',
            'locality': 'Main Road',
            'city': 'Kolhapur',
            'mobile': '1234567890',
            'zipcode': '416001',
            'state': 'MH',
        })
        self.assertRedirects(response, reverse('address'))
        self.address.refresh_from_db()
        self.assertEqual(self.address.name, 'Updated Customer')

    def test_address_form_preserves_leading_zeroes(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('profile'), {
            'name': 'Customer',
            'locality': 'Market Road',
            'city': 'Kolhapur',
            'mobile': '0987654321',
            'zipcode': '0416001',
            'state': 'MH',
        })
        self.assertRedirects(response, reverse('address'))
        address = Customer.objects.get(user=self.user, locality='Market Road')
        self.assertEqual(address.mobile, '0987654321')
        self.assertEqual(address.zipcode, '0416001')

    def test_contact_form_sends_valid_message(self):
        response = self.client.post(reverse('contact'), {
            'name': 'Visitor',
            'email': 'visitor@example.com',
            'message': 'Please tell me about your dairy products.',
        })
        self.assertRedirects(response, reverse('contact'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('dairy products', mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].reply_to, ['visitor@example.com'])
        self.assertEqual(ContactMessage.objects.get().email, 'visitor@example.com')

    def test_wishlist_add_and_remove_are_user_scoped(self):
        self.client.force_login(self.user)
        add_url = reverse('wishlist-add', args=[self.product.pk])
        self.assertEqual(self.client.get(add_url).status_code, 405)
        self.assertRedirects(self.client.post(add_url), reverse('productdetail', args=[self.product.pk]))
        self.assertEqual(WishlistItem.objects.filter(user=self.user, product=self.product).count(), 1)
        self.assertContains(self.client.get(reverse('wishlist')), self.product.title)
        self.assertContains(self.client.get(reverse('productdetail', args=[self.product.pk])), 'Remove from Wishlist')
        self.assertRedirects(
            self.client.post(reverse('wishlist-remove', args=[self.product.pk])),
            reverse('wishlist'),
        )
        self.assertFalse(WishlistItem.objects.filter(user=self.user).exists())

    def test_password_reset_emails_a_working_reset_link(self):
        response = self.client.post(reverse('password_reset'), {'email': self.user.email})
        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        reset_url = next(
            line for line in mail.outbox[0].body.splitlines()
            if '/password-reset-confirm/' in line
        )
        reset_path = urlsplit(reset_url).path
        response = self.client.get(reset_path, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Password Confirm')

    def test_registration_creates_user_and_redirects_to_login(self):
        response = self.client.post(reverse('customerregistrationview'), {
            'username': 'new-customer',
            'email': 'new@example.com',
            'password1': 'Strong-password-456',
            'password2': 'Strong-password-456',
        })
        self.assertRedirects(response, reverse('login'))
        self.assertTrue(User.objects.filter(username='new-customer').exists())

    def test_logout_requires_post_and_logs_user_out(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 405)
        response = self.client.post(reverse('logout'))
        self.assertRedirects(response, reverse('login'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_password_change_updates_password_and_keeps_session(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('passwordchange'), {
            'old_password': 'Strong-password-123',
            'new_password1': 'Different-strong-456',
            'new_password2': 'Different-strong-456',
        })
        self.assertRedirects(response, reverse('passwordchangedone'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('Different-strong-456'))
        self.assertEqual(self.client.get(reverse('profile')).status_code, 200)
