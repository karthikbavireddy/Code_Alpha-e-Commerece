import os
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from django.core.files.base import ContentFile
from store.models import Category, Product, Order, OrderItem, ReturnRequest
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont


class Command(BaseCommand):
    help = 'Seeds initial demo categories, realistic products with images, and demo accounts'

    def create_product_image(self, title, color_bg, color_text):
        """Generates a clean product graphic using Pillow."""
        img = Image.new('RGB', (600, 450), color=color_bg)
        draw = ImageDraw.Draw(img)

        # Draw a stylish accent card shape in the center
        draw.rounded_rectangle([60, 45, 540, 405], radius=24, fill=(255, 255, 255, 40), outline=(255, 255, 255, 80), width=3)

        # Draw text
        words = title.split()
        line1 = " ".join(words[:2]) if len(words) >= 2 else title
        line2 = " ".join(words[2:]) if len(words) > 2 else ""

        # Using default font
        draw.text((300, 200), line1, fill=color_text, anchor="mm")
        if line2:
            draw.text((300, 240), line2, fill=color_text, anchor="mm")

        # Watermark
        draw.text((300, 370), "CodeAlpha Collection", fill=color_text, anchor="mm")

        output = BytesIO()
        img.save(output, format='JPEG', quality=90)
        return output.getvalue()

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding database with demo data..."))

        # 1. Create Demo Users
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser('admin', 'admin@codealpha.com', 'admin123')
            self.stdout.write(self.style.SUCCESS("Created Superuser: admin / admin123"))

        if not User.objects.filter(username='customer').exists():
            customer = User.objects.create_user('customer', 'customer@example.com', 'customer123')
            customer.first_name = "Alex"
            customer.last_name = "Morgan"
            customer.save()
            self.stdout.write(self.style.SUCCESS("Created Sample Customer: customer / customer123"))

        # 2. Categories
        categories_data = [
            {'name': 'Audio & Headphones', 'slug': 'audio-headphones'},
            {'name': 'Smart Tech & Wearables', 'slug': 'smart-tech-wearables'},
            {'name': 'Workspace & Desk Setup', 'slug': 'workspace-desk'},
            {'name': 'Everyday Carry & Accessories', 'slug': 'everyday-carry'},
        ]

        categories = {}
        for cat_info in categories_data:
            cat, _ = Category.objects.get_or_create(slug=cat_info['slug'], defaults={'name': cat_info['name']})
            categories[cat_info['slug']] = cat

        self.stdout.write(self.style.SUCCESS(f"Verified {len(categories)} categories."))

        # 3. Products
        products_data = [
            {
                'name': 'AeroSound Pro Wireless Headphones',
                'category': categories['audio-headphones'],
                'price': Decimal('249.99'),
                'stock': 25,
                'description': 'Premium active noise-cancelling wireless headphones with 40-hour battery life, high-resolution audio codecs, and plush memory foam earcups.',
                'color_bg': (30, 41, 59),
                'color_text': (248, 250, 252),
            },
            {
                'name': 'SonicPulse Studio Earbuds',
                'category': categories['audio-headphones'],
                'price': Decimal('129.50'),
                'stock': 40,
                'description': 'Compact true wireless earbuds with transparent spatial audio, IPX7 sweat resistance, and seamless device switching.',
                'color_bg': (79, 70, 229),
                'color_text': (255, 255, 255),
            },
            {
                'name': 'Vintage Walnut Bluetooth Speaker',
                'category': categories['audio-headphones'],
                'price': Decimal('189.00'),
                'stock': 0,  # Out of stock demo
                'description': 'Handcrafted walnut wood portable speaker featuring deep rich bass, analog dials, and 24-hour battery playback.',
                'color_bg': (120, 53, 15),
                'color_text': (254, 243, 199),
            },
            {
                'name': 'Nova Ultra Smartwatch Series 5',
                'category': categories['smart-tech-wearables'],
                'price': Decimal('329.00'),
                'stock': 18,
                'description': 'Aerospace titanium frame with Sapphire AMOLED display, ECG monitoring, sleep coach, and water resistance up to 50 meters.',
                'color_bg': (15, 23, 42),
                'color_text': (56, 189, 248),
            },
            {
                'name': 'PulseFit Health & Fitness Band',
                'category': categories['smart-tech-wearables'],
                'price': Decimal('89.99'),
                'stock': 50,
                'description': 'Ultralight fitness tracker with 24/7 heart rate monitoring, SPO2 tracking, 30+ sport modes, and 14-day battery longevity.',
                'color_bg': (13, 148, 136),
                'color_text': (255, 255, 255),
            },
            {
                'name': 'ErgoLift Aluminum Laptop Stand',
                'category': categories['workspace-desk'],
                'price': Decimal('54.95'),
                'stock': 35,
                'description': 'Precision CNC-machined aluminum riser with 360-degree rotation, dual heat ventilation slots, and silicone anti-slip grips.',
                'color_bg': (51, 65, 85),
                'color_text': (226, 232, 240),
            },
            {
                'name': 'Apex Mechanical Wireless Keyboard',
                'category': categories['workspace-desk'],
                'price': Decimal('149.00'),
                'stock': 15,
                'description': 'Custom hot-swappable mechanical switches, gasket-mounted sound dampening, RGB backlighting, and Bluetooth 5.2 connectivity.',
                'color_bg': (17, 24, 39),
                'color_text': (168, 85, 247),
            },
            {
                'name': 'OmniPad Felt & Leather Desk Mat',
                'category': categories['workspace-desk'],
                'price': Decimal('38.00'),
                'stock': 60,
                'description': 'Dual-sided executive desk pad crafted from vegan saddle leather and recycled merino wool felt for effortless mouse tracking.',
                'color_bg': (68, 64, 60),
                'color_text': (245, 245, 244),
            },
            {
                'name': 'Titanium Minimalist Cardholder Wallet',
                'category': categories['everyday-carry'],
                'price': Decimal('65.00'),
                'stock': 30,
                'description': 'RFID-blocking slim titanium cardholder with elastic cash strap holding up to 12 cards without adding bulk to your pocket.',
                'color_bg': (30, 58, 138),
                'color_text': (219, 234, 254),
            },
            {
                'name': 'HydroVault Insulated Thermal Flask',
                'category': categories['everyday-carry'],
                'price': Decimal('42.50'),
                'stock': 45,
                'description': 'Vacuum insulated 18/8 food-grade stainless steel bottle maintaining liquids ice-cold for 24 hours or steaming hot for 12 hours.',
                'color_bg': (6, 95, 70),
                'color_text': (209, 250, 229),
            },
        ]

        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'products'), exist_ok=True)

        for p_data in products_data:
            product, created = Product.objects.get_or_create(
                name=p_data['name'],
                defaults={
                    'category': p_data['category'],
                    'price': p_data['price'],
                    'stock': p_data['stock'],
                    'description': p_data['description'],
                }
            )

            # Generate and attach image if not present
            if not product.image:
                img_bytes = self.create_product_image(
                    product.name,
                    p_data['color_bg'],
                    p_data['color_text']
                )
                filename = f"{product.slug}.jpg"
                product.image.save(filename, ContentFile(img_bytes), save=True)

            self.stdout.write(self.style.SUCCESS(f"Saved product: {product.name} (Stock: {product.stock}, Price: ${product.price})"))

        # 4. Seed Demo Orders & Returns for Customer
        customer = User.objects.filter(username='customer').first()
        if customer and not Order.objects.filter(user=customer).exists():
            prod_earbuds = Product.objects.filter(slug='sonicpulse-studio-earbuds').first() or Product.objects.first()
            prod_watch = Product.objects.filter(slug='nova-ultra-smartwatch-series-5').first() or Product.objects.last()

            # Delivered Order 1 (eligible for return)
            order1 = Order.objects.create(
                user=customer,
                full_name="Alex Morgan",
                address="742 Evergreen Terrace",
                city="Springfield",
                postal_code="97477",
                tracking_number="TRK-2026-USPS-8849",
                status='delivered',
                notes="Leave on front porch behind flower pot"
            )
            OrderItem.objects.create(
                order=order1,
                product=prod_earbuds,
                product_name=prod_earbuds.name,
                price=prod_earbuds.price,
                quantity=1
            )
            self.stdout.write(self.style.SUCCESS(f"Created Delivered Order: {order1.order_id} for customer"))

            # Order 2 with an active Return Request
            order2 = Order.objects.create(
                user=customer,
                full_name="Alex Morgan",
                address="742 Evergreen Terrace",
                city="Springfield",
                postal_code="97477",
                tracking_number="TRK-2026-FEDEX-9921",
                status='return_requested',
                notes="Package delivered successfully"
            )
            item2 = OrderItem.objects.create(
                order=order2,
                product=prod_watch,
                product_name=prod_watch.name,
                price=prod_watch.price,
                quantity=1
            )
            ret = ReturnRequest.objects.create(
                order=order2,
                user=customer,
                item=item2,
                reason='defective',
                description="The display screen does not turn on after charging for 4 hours.",
                status='requested',
                refund_amount=item2.subtotal,
                admin_notes="Fulfillment team will review warranty replacement or full refund."
            )
            self.stdout.write(self.style.SUCCESS(f"Created Order with Return Request: {order2.order_id} (Return: {ret.return_id})"))

        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))

