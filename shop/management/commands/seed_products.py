from django.core.management.base import BaseCommand
from shop.models import Product

class Command(BaseCommand):
    help = 'Seed database with handmade jewelry products'

    def handle(self, *args, **options):
        products_data = [
            {
                'name': 'Pearl Necklace with Red Stones',
                'price': 2500,
                'description': 'Beautiful handmade pearl necklace featuring lustrous pearls adorned with vibrant red gemstones. Perfect for special occasions and everyday elegance. Each piece is crafted with meticulous attention to detail.',
                'is_active': True,
            },
            {
                'name': 'Elegant Pearl Choker',
                'price': 1800,
                'description': 'Sophisticated pearl choker necklace with red accent stones. This classic design complements both traditional and modern outfits. Handcrafted with premium materials.',
                'is_active': True,
            },
            {
                'name': 'Ruby Pearl Pendant',
                'price': 3200,
                'description': 'Exquisite pendant featuring a central pearl surrounded by ruby gemstones. A statement piece that adds glamour to any wardrobe. Traditionally handmade in Singrauli.',
                'is_active': True,
            },
            {
                'name': 'Layered Pearl Necklace',
                'price': 2200,
                'description': 'Stunning multi-layered necklace with pearls and red gemstone accents. Create a sophisticated look with beautiful depth and dimension. Ideal for festivals and celebrations.',
                'is_active': True,
            },
            {
                'name': 'Classic Pearl Strand',
                'price': 1500,
                'description': 'Timeless pearl strand necklace with carefully selected red stone embellishments. A versatile piece that works with any style. Handmade with care and precision.',
                'is_active': True,
            },
            {
                'name': 'Ornate Pearl Necklace',
                'price': 3800,
                'description': 'Premium handcrafted necklace featuring large pearls and intricate red stone work. Perfect for weddings, festivals, and formal events. Each pearl is individually selected for quality.',
                'is_active': True,
            },
        ]

        for product_data in products_data:
            product, created = Product.objects.get_or_create(
                name=product_data['name'],
                defaults={
                    'price': product_data['price'],
                    'description': product_data['description'],
                    'is_active': product_data['is_active'],
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created product: {product.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠ Product already exists: {product.name}')
                )

        self.stdout.write(self.style.SUCCESS('\n✓ Product seeding completed!'))
