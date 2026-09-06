from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from decimal import Decimal
from store.models import Category, Product, Order, OrderItem
from store.cart import Cart


class StoreModelAndCartTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Electronics')
        self.product1 = Product.objects.create(
            name='Test Laptop',
            category=self.category,
            price=Decimal('999.99'),
            stock=10,
            description='A high-performance test laptop'
        )
        self.product2 = Product.objects.create(
            name='Test Mouse',
            category=self.category,
            price=Decimal('25.50'),
            stock=0,
            description='Wireless optical mouse'
        )
        self.user = User.objects.create_user(
            username='johndoe',
            email='john@example.com',
            password='Password123!'
        )

    def test_slug_auto_generation(self):
        self.assertEqual(self.category.slug, 'electronics')
        self.assertEqual(self.product1.slug, 'test-laptop')

    def test_product_stock_status(self):
        self.assertTrue(self.product1.is_in_stock)
        self.assertFalse(self.product2.is_in_stock)

    def test_product_list_view(self):
        response = self.client.get(reverse('store:product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Laptop')
        self.assertContains(response, 'In Stock')
        self.assertContains(response, 'Out of Stock')

    def test_product_detail_view(self):
        response = self.client.get(reverse('store:product_detail', kwargs={'slug': self.product1.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Laptop')
        self.assertContains(response, '999.99')
        self.assertContains(response, 'Add to Cart')

    def test_cart_operations(self):
        # Add product1 to cart
        add_response = self.client.post(reverse('store:cart_add', kwargs={'product_id': self.product1.id}), {'quantity': 2})
        self.assertEqual(add_response.status_code, 302)

        # View cart
        cart_response = self.client.get(reverse('store:cart_detail'))
        self.assertEqual(cart_response.status_code, 200)
        self.assertContains(cart_response, 'Test Laptop')
        self.assertContains(cart_response, '1999.98')

        # Update quantity
        update_response = self.client.post(reverse('store:cart_update', kwargs={'product_id': self.product1.id}), {'quantity': 3})
        self.assertEqual(update_response.status_code, 302)
        cart_response2 = self.client.get(reverse('store:cart_detail'))
        self.assertContains(cart_response2, '2999.97')

        # Remove from cart
        remove_response = self.client.post(reverse('store:cart_remove', kwargs={'product_id': self.product1.id}))
        self.assertEqual(remove_response.status_code, 302)
        cart_response3 = self.client.get(reverse('store:cart_detail'))
        self.assertContains(cart_response3, 'Your Cart is Currently Empty')

    def test_checkout_requires_login(self):
        # Add to cart first
        self.client.post(reverse('store:cart_add', kwargs={'product_id': self.product1.id}), {'quantity': 1})
        # Attempt checkout while logged out
        response = self.client.get(reverse('store:checkout'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('store:login'), response.url)

    def test_user_registration_and_instant_login(self):
        reg_data = {
            'username': 'newcustomer',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'newuser@example.com',
            'password1': 'SecretPass123!',
            'password2': 'SecretPass123!',
        }
        response = self.client.post(reverse('store:register'), reg_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)
        self.assertEqual(response.context['user'].username, 'newcustomer')

    def test_checkout_order_creation_and_stock_decrement(self):
        self.client.login(username='johndoe', password='Password123!')
        
        # Add to cart
        self.client.post(reverse('store:cart_add', kwargs={'product_id': self.product1.id}), {'quantity': 3})

        initial_stock = self.product1.stock  # 10
        checkout_data = {
            'full_name': 'John Doe',
            'address': '456 Elm St',
            'city': 'Metropolis',
            'postal_code': '12345'
        }
        response = self.client.post(reverse('store:checkout'), checkout_data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Check order exists
        order = Order.objects.filter(user=self.user).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.full_name, 'John Doe')
        self.assertEqual(order.items.count(), 1)

        # Check order item snapshot
        order_item = order.items.first()
        self.assertEqual(order_item.product_name, 'Test Laptop')
        self.assertEqual(order_item.price, Decimal('999.99'))
        self.assertEqual(order_item.quantity, 3)

        # Check stock decremented
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.stock, initial_stock - 3)

        # Check cart is cleared
        session_cart = self.client.session.get('cart')
        self.assertTrue(not session_cart or len(session_cart) == 0)

        # Check order history
        history_response = self.client.get(reverse('store:order_history'))
        self.assertEqual(history_response.status_code, 200)
        self.assertContains(history_response, order.order_id)
        self.assertContains(history_response, 'Test Laptop')

    def test_order_returns_lifecycle(self):
        self.client.login(username='johndoe', password='Password123!')
        order = Order.objects.create(
            user=self.user,
            full_name='John Doe',
            address='123 Main St',
            city='New York',
            postal_code='10001',
            status='delivered'
        )
        item = OrderItem.objects.create(
            order=order,
            product=self.product1,
            product_name=self.product1.name,
            price=self.product1.price,
            quantity=1
        )
        self.assertTrue(order.can_request_return)

        # GET return page
        get_response = self.client.get(reverse('store:request_return', kwargs={'order_id': order.id}))
        self.assertEqual(get_response.status_code, 200)
        self.assertContains(get_response, order.order_id)

        # POST return request
        post_response = self.client.post(reverse('store:request_return', kwargs={'order_id': order.id}), {
            'item': item.id,
            'reason': 'defective',
            'description': 'Item arrived damaged and does not power on.'
        })
        self.assertRedirects(post_response, reverse('store:returns_list'))

        # Check DB
        order.refresh_from_db()
        self.assertEqual(order.status, 'return_requested')
        ret = order.returns.first()
        self.assertIsNotNone(ret)
        self.assertTrue(ret.return_id.startswith('RET-'))
        self.assertEqual(ret.status, 'requested')
        self.assertEqual(ret.refund_amount, item.subtotal)

        # Check returns list view
        list_response = self.client.get(reverse('store:returns_list'))
        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, ret.return_id)

    def test_admin_and_customer_login_isolation(self):
        # 1. Regular customer attempting admin access
        self.client.login(username='johndoe', password='Password123!')
        admin_response = self.client.get('/admin/')
        # Django admin redirects non-staff users to admin login with next=/admin/
        self.assertEqual(admin_response.status_code, 302)
        self.assertIn('/admin/login/', admin_response.url)

        # 2. Staff user can access admin
        staff_user = User.objects.create_superuser('staffadmin', 'staff@test.com', 'AdminPass123!')
        self.client.login(username='staffadmin', password='AdminPass123!')
        admin_staff_response = self.client.get('/admin/')
        self.assertEqual(admin_staff_response.status_code, 200)
        self.assertContains(admin_staff_response, 'CodeAlpha Admin Portal')

    def test_cart_clear_idempotent_and_safe(self):
        session = self.client.session
        class MockRequest:
            def __init__(self, session):
                self.session = session

        req = MockRequest(session)
        cart = Cart(req)
        # Should clear without error even if empty
        cart.clear()
        self.assertTrue(cart.is_empty)
        self.assertEqual(len(cart), 0)

        # Add item then clear
        cart.add(self.product1, quantity=2)
        self.assertEqual(len(cart), 2)
        cart.clear()
        self.assertTrue(cart.is_empty)
        self.assertEqual(len(cart), 0)

    def test_cart_prunes_deleted_products_and_syncs_price(self):
        temp_product = Product.objects.create(
            name='Temp Gadget',
            price=Decimal('50.00'),
            stock=5
        )
        self.client.post(reverse('store:cart_add', kwargs={'product_id': temp_product.id}), {'quantity': 1})
        self.client.post(reverse('store:cart_add', kwargs={'product_id': self.product1.id}), {'quantity': 1})

        # Check both in cart
        resp = self.client.get(reverse('store:cart_detail'))
        self.assertContains(resp, 'Temp Gadget')
        self.assertContains(resp, 'Test Laptop')

        # Delete temp_product from database
        temp_product.delete()

        # Update product1 price
        self.product1.price = Decimal('899.99')
        self.product1.save()

        # View cart again - temp_product should be automatically purged and price updated
        resp2 = self.client.get(reverse('store:cart_detail'))
        self.assertNotContains(resp2, 'Temp Gadget')
        self.assertContains(resp2, '899.99')

    def test_open_redirect_protection(self):
        # 1. Login with unsafe external URL
        login_resp = self.client.post(reverse('store:login') + '?next=https://malicious-site.com/steal', {
            'username': 'johndoe',
            'password': 'Password123!',
        })
        self.assertRedirects(login_resp, reverse('store:product_list'))

        self.client.logout()

        # 2. Register with unsafe external URL
        reg_data = {
            'username': 'safecustomer',
            'first_name': 'Safe',
            'last_name': 'User',
            'email': 'safe@example.com',
            'password1': 'SecretPass123!',
            'password2': 'SecretPass123!',
        }
        reg_resp = self.client.post(reverse('store:register') + '?next=//attacker.com', reg_data)
        self.assertRedirects(reg_resp, reverse('store:product_list'))

    def test_admin_mark_rejected_action_restores_order_status(self):
        from store.admin import ReturnRequestAdmin
        from store.models import ReturnRequest
        from django.contrib.admin.sites import site

        order = Order.objects.create(
            user=self.user,
            full_name='John Doe',
            address='123 Main St',
            city='New York',
            postal_code='10001',
            status='return_requested'
        )
        ret = ReturnRequest.objects.create(
            order=order,
            user=self.user,
            reason='defective',
            description='Test return issue',
            status='requested'
        )

        admin_instance = ReturnRequestAdmin(ReturnRequest, site)
        request = self.client.request().wsgi_request
        request.user = User.objects.create_superuser('adminuser', 'admin@test.com', 'AdminPass123!')

        admin_instance.mark_rejected(request, ReturnRequest.objects.filter(id=ret.id))

        ret.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(ret.status, 'rejected')
        self.assertEqual(order.status, 'delivered')


