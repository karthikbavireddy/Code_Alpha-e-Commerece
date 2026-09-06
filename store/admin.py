from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, Order, OrderItem, ReturnRequest

# Customize Admin Site Branding
admin.site.site_header = 'CodeAlpha Store & Orders Administration'
admin.site.site_title = 'CodeAlpha Admin Portal'
admin.site.index_title = 'Store Administration, Orders & Returns Fulfillment'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'is_in_stock_display', 'created_at')
    list_filter = ('category', 'created_at')
    list_editable = ('price', 'stock')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

    @admin.display(description='In Stock', boolean=True)
    def is_in_stock_display(self, obj):
        return obj.is_in_stock


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'price', 'quantity', 'item_subtotal')

    @admin.display(description='Subtotal ($)')
    def item_subtotal(self, obj):
        if not obj or not obj.pk or not obj.price:
            return "$0.00"
        return f"${obj.subtotal:.2f}"


class ReturnRequestInline(admin.TabularInline):
    model = ReturnRequest
    extra = 0
    readonly_fields = ('return_id', 'user', 'reason', 'refund_amount', 'status', 'created_at')
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'user', 'full_name', 'status_badge', 'tracking_number', 'order_total', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order_id', 'tracking_number', 'full_name', 'user__username', 'address', 'city', 'postal_code')
    readonly_fields = ('order_id', 'created_at', 'updated_at', 'order_total', 'grand_total_display')
    inlines = [OrderItemInline, ReturnRequestInline]
    fieldsets = (
        ('Order Identification', {
            'fields': ('order_id', 'tracking_number', 'user', 'status')
        }),
        ('Shipping Information', {
            'fields': ('full_name', 'address', 'city', 'postal_code', 'notes')
        }),
        ('Billing & Totals', {
            'fields': ('order_total', 'shipping_fee', 'tax_amount', 'grand_total_display')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'pending': '#d97706',
            'processing': '#2563eb',
            'shipped': '#4f46e5',
            'delivered': '#16a34a',
            'return_requested': '#ea580c',
            'returned': '#dc2626',
            'cancelled': '#64748b',
        }
        color = colors.get(obj.status, '#64748b')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: 600; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )

    @admin.display(description='Items Subtotal ($)')
    def order_total(self, obj):
        return f"${obj.total_cost:.2f}"

    @admin.display(description='Grand Total ($)')
    def grand_total_display(self, obj):
        return f"${obj.grand_total:.2f}"


@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = ('return_id', 'order_link', 'user', 'reason', 'status_badge', 'refund_amount', 'created_at')
    list_filter = ('status', 'reason', 'created_at')
    search_fields = ('return_id', 'order__order_id', 'user__username', 'description')
    readonly_fields = ('return_id', 'order', 'user', 'item', 'created_at', 'updated_at')
    actions = ['mark_approved', 'mark_rejected', 'mark_refunded']

    @admin.display(description='Order')
    def order_link(self, obj):
        return obj.order.order_id

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'requested': '#ea580c',
            'approved': '#2563eb',
            'rejected': '#dc2626',
            'item_received': '#7c3aed',
            'refunded': '#16a34a',
        }
        color = colors.get(obj.status, '#64748b')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: 600; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )

    @admin.action(description='Approve selected return requests')
    def mark_approved(self, request, queryset):
        count = queryset.update(status='approved')
        self.message_user(request, f"{count} return request(s) successfully marked as Approved.")

    @admin.action(description='Reject selected return requests')
    def mark_rejected(self, request, queryset):
        for ret in queryset:
            ret.status = 'rejected'
            ret.save(update_fields=['status'])
            if ret.order.status == 'return_requested':
                ret.order.status = 'delivered'
                ret.order.save(update_fields=['status'])
        self.message_user(request, f"{queryset.count()} return request(s) marked as Rejected and order status restored.")

    @admin.action(description='Mark selected return requests as Refunded')
    def mark_refunded(self, request, queryset):
        for ret in queryset:
            ret.status = 'refunded'
            ret.save()
            # Update parent order
            ret.order.status = 'returned'
            ret.order.save(update_fields=['status'])
        self.message_user(request, f"{queryset.count()} return request(s) marked as Refunded and order(s) updated.")
