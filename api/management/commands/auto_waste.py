from django.core.management.base import BaseCommand
from api.models import FoodLog, WasteLog
from django.utils import timezone
from datetime import date
from django.db.models import Q
 
class Command(BaseCommand):
    help = 'Automatically log expired and undonated food to WasteLog'
 
    def handle(self, *args, **kwargs):
        today = date.today()
        expired_foods = FoodLog.objects.exclude(status='Donated').filter(expiration_date__lt=today)
 
        for food in expired_foods:
            available_qty = food.available_quantity
            if available_qty > 0:
                WasteLog.objects.create(
                    user=food.user,
                    food_log=food,
                    quantity=available_qty,
                    reason="Expired"
                )
            # Update status to Expired if not already
            if food.status != 'Expired':
                food.status = 'Expired'
                food.save(update_fields=['status'])
 
        self.stdout.write(f"{expired_foods.count()} expired items logged to waste.")
