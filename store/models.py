from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
from decimal import Decimal
import secrets


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name) or "category"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or "product"
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def is_in_stock(self):
        return self.stock > 0

    def __str__(self):
        return self.name


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('return_requested', 'Return Requested'),
        ('returned', 'Returned'),
        ('cancelled', 'Cancelled'),
    ]

    order_id = models.CharField(max_length=32, unique=True, blank=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    full_name = models.CharField(max_length=150)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    tracking_number = models.CharField(max_length=64, blank=True, default='')
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_id:
            now_str = timezone.now().strftime('%Y%m%d')
            while True:
                candidate = f"ORD-{now_str}-{secrets.token_hex(3).upper()}"
                if not Order.objects.filter(order_id=candidate).exists():
                    self.order_id = candidate
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_id or f'Order #{self.id}'} - {self.full_name} ({self.get_status_display()})"

    @property
    def total_cost(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def grand_total(self):
        return self.total_cost + self.shipping_fee + self.tax_amount

    def get_total_cost(self):
        return self.total_cost

    @property
    def can_request_return(self):
        # Allow returns if order is shipped or delivered, and doesn't already have an active/completed return
        if self.status not in ('shipped', 'delivered'):
            return False
        return not self.returns.filter(status__in=['requested', 'approved', 'item_received', 'refunded']).exists()

    @property
    def active_return(self):
        return self.returns.order_by('-created_at').first()


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='order_items'
    )
    product_name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['id']

    @property
    def subtotal(self):
        if not self.price or not self.quantity:
            return Decimal('0.00')
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.product_name} in {self.order.order_id or f'Order #{self.order_id}'}"


class ReturnRequest(models.Model):
    REASON_CHOICES = [
        ('defective', 'Defective / Not Working'),
        ('damaged', 'Damaged in Transit'),
        ('wrong_item', 'Received Wrong Item'),
        ('not_as_described', 'Item Not as Described'),
        ('changed_mind', 'Changed Mind / No Longer Needed'),
        ('other', 'Other Reason'),
    ]

    STATUS_CHOICES = [
        ('requested', 'Return Requested'),
        ('approved', 'Return Approved'),
        ('rejected', 'Return Rejected'),
        ('item_received', 'Item Received at Warehouse'),
        ('refunded', 'Refund Processed'),
    ]

    return_id = models.CharField(max_length=32, unique=True, blank=True, db_index=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='returns')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='returns')
    item = models.ForeignKey(
        OrderItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='returns',
        help_text="Leave blank if returning the entire order"
    )
    reason = models.CharField(max_length=30, choices=REASON_CHOICES, default='defective')
    description = models.TextField(help_text="Please describe the issue or reason for return in detail")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='requested')
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    admin_notes = models.TextField(blank=True, help_text="Internal notes or return instructions by store staff")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.return_id:
            now_str = timezone.now().strftime('%Y%m%d')
            while True:
                candidate = f"RET-{now_str}-{secrets.token_hex(3).upper()}"
                if not ReturnRequest.objects.filter(return_id=candidate).exists():
                    self.return_id = candidate
                    break
        if not self.refund_amount or self.refund_amount == 0:
            if self.item:
                self.refund_amount = self.item.subtotal
            elif self.order:
                self.refund_amount = self.order.grand_total
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.return_id} ({self.get_status_display()}) for {self.order.order_id or f'Order #{self.order.id}'}"
