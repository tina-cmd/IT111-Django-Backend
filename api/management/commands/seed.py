from django.core.management.base import BaseCommand
from api.models import FoodCategory, DonationCenter

class Command(BaseCommand):
    help = 'Seed the database with food categories and donation centers around Butuan City'

    def handle(self, *args, **kwargs):
        # Define the food categories to seed
        categories = [
            "Fruits",
            "Vegetables",
            "Grains & Cereals",
            "Dairy Products",
            "Meats & Poultry",
            "Seafood",
            "Baked Goods",
            "Beverages",
            "Frozen Foods",
            "Canned Goods",
        ]

        # Create or update FoodCategory entries
        for category_name in categories:
            obj, created = FoodCategory.objects.get_or_create(name=category_name)
            if created:
                self.stdout.write(f'Created category: {category_name}')
            else:
                self.stdout.write(f'Category already exists: {category_name}')

        # List of Donation Centers around Butuan City (names and lat/long approximate)
        donation_centers = [
            {
                "name": "Butuan City Food Bank",
                "address": "P. Gomez Street, Butuan City",
                "latitude": 8.9472,
                "longitude": 125.5352,
                "contact_number": "085-817-1234",
                "email": "info@butuanfoodbank.org"
            },
            {
                "name": "Caraga Regional Food Center",
                "address": "J.C. Aquino Avenue, Butuan City",
                "latitude": 8.9575,
                "longitude": 125.5361,
                "contact_number": "085-812-2345",
                "email": "contact@caragafoodcenter.ph"
            },
            {
                "name": "Gaisano Community Kitchen",
                "address": "C.M. Recto Avenue, Butuan City",
                "latitude": 8.9490,
                "longitude": 125.5290,
                "contact_number": "085-816-9876",
                "email": "gaisano@communitykitchen.com"
            },
            {
                "name": "Barangay Lawigan Donation Center",
                "address": "Barangay Lawigan, Butuan City",
                "latitude": 8.9465,
                "longitude": 125.5200,
                "contact_number": "085-814-1598",
                "email": "lawigan@donationcenter.ph"
            },
            {
                "name": "Red Cross Butuan Chapter",
                "address": "Montilla Blvd, Butuan City",
                "latitude": 8.9540,
                "longitude": 125.5402,
                "contact_number": "085-813-7531",
                "email": "butuan@redcross.org.ph"
            },
            {
                "name": "Butuan City Salvation Army",
                "address": "J.C. Aquino Avenue, Butuan City",
                "latitude": 8.9550,
                "longitude": 125.5330,
                "contact_number": "085-819-4823",
                "email": "salvationarmy.butuan@gmail.com"
            }
        ]

        # Create or update DonationCenter entries
        for center in donation_centers:
            obj, created = DonationCenter.objects.update_or_create(
                name=center['name'],
                defaults={
                    'address': center['address'],
                    'latitude': center['latitude'],
                    'longitude': center['longitude'],
                    'contact_number': center['contact_number'],
                    'email': center['email']
                }
            )
            if created:
                self.stdout.write(f'Created donation center: {center["name"]}')
            else:
                self.stdout.write(f'Updated donation center: {center["name"]}')

        self.stdout.write(self.style.SUCCESS('Seeding of FoodCategory and DonationCenter complete!'))

