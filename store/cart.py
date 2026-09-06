from decimal import Decimal
from django.conf import settings
from .models import Product

CART_SESSION_ID = 'cart'

class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(CART_SESSION_ID)
        if not cart:
            cart = self.session[CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, quantity=1, override_quantity=False):
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.price),
            }

        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity

        # Stock cap: ensure cart quantity does not exceed product stock
        if self.cart[product_id]['quantity'] > product.stock:
            self.cart[product_id]['quantity'] = product.stock

        if self.cart[product_id]['quantity'] <= 0:
            self.remove(product)
        else:
            self.save()

    def update_quantity(self, product_id, quantity):
        product_id = str(product_id)
        if product_id in self.cart:
            try:
                product = Product.objects.get(id=int(product_id))
                qty = int(quantity)
                target_qty = min(qty, product.stock)
                if target_qty <= 0:
                    del self.cart[product_id]
                else:
                    self.cart[product_id]['quantity'] = target_qty
                    self.cart[product_id]['price'] = str(product.price)
                self.save()
            except (Product.DoesNotExist, ValueError):
                pass

    def save(self):
        self.session.modified = True

    def remove(self, product):
        product_id = str(product.id) if hasattr(product, 'id') else str(product)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def clear(self):
        if CART_SESSION_ID in self.session:
            del self.session[CART_SESSION_ID]
        self.cart = {}
        self.save()

    def __iter__(self):
        product_ids = list(self.cart.keys())
        products = Product.objects.filter(id__in=product_ids)
        product_map = {str(p.id): p for p in products}

        # Automatically purge any deleted/orphaned products from session cart
        stale_ids = [pid for pid in product_ids if pid not in product_map]
        if stale_ids:
            for pid in stale_ids:
                if pid in self.cart:
                    del self.cart[pid]
            self.save()

        for product_id, item_data in list(self.cart.items()):
            product = product_map.get(product_id)
            if product:
                # Sync live price
                price = product.price
                item_data['price'] = str(price)
                quantity = min(item_data['quantity'], product.stock)
                if quantity <= 0:
                    del self.cart[product_id]
                    self.save()
                    continue
                yield {
                    'product': product,
                    'price': price,
                    'quantity': quantity,
                    'subtotal': price * quantity,
                }


    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        total = Decimal('0.00')
        for item in self:
            total += item['subtotal']
        return total

    @property
    def is_empty(self):
        return len(self.cart) == 0
