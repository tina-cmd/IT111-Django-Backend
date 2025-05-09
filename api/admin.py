from django.contrib import admin
from .models import FoodCategory, FoodLog, DonationCenter, DonationRecord

admin.site.register(FoodCategory)
admin.site.register(FoodLog)
admin.site.register(DonationCenter)
admin.site.register(DonationRecord)

# Register your models here.
