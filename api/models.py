from django.db import models
from django.contrib.auth.models import User
from datetime import date
from django.db.models import Sum
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    prefers_dark_mode = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s profile"

# Ensure a UserProfile is created for each new user
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class FoodCategory(models.Model):
    name = models.CharField(max_length=100)

class FoodLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    food_name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField()
    category = models.ForeignKey(FoodCategory, on_delete=models.SET_NULL, null=True)
    date_logged = models.DateTimeField(auto_now_add=True)
    expiration_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, default='Available')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.expiration_date and self.expiration_date < date.today():
            new_status = 'Expired'
        elif self.available_quantity == 0:
            new_status = 'Donated'
        else:
            new_status = 'Available'
        if self.status != new_status:
            self.status = new_status
            super().save(update_fields=['status'])

    @property
    def donated_quantity(self):
        donated = DonationRecord.objects.filter(food_log=self).aggregate(total=Sum('quantity'))
        return donated['total'] or 0

    @property
    def wasted_quantity(self):
        wasted = WasteLog.objects.filter(food_log=self).aggregate(total=Sum('quantity'))
        return wasted['total'] or 0

    @property
    def available_quantity(self):
        return self.quantity - self.donated_quantity - self.wasted_quantity

class DonationCenter(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    contact_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

class DonationRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    center = models.ForeignKey(DonationCenter, on_delete=models.CASCADE)
    food_log = models.ForeignKey(FoodLog, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    date_donated = models.DateTimeField(auto_now_add=True)

class WasteLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    food_log = models.ForeignKey(FoodLog, on_delete=models.CASCADE, null=True, blank=True)  # Link to FoodLog
    quantity = models.PositiveIntegerField()
    reason = models.CharField(max_length=255, default="Expired")
    date_logged = models.DateTimeField(auto_now_add=True)

    @property
    def food_name(self):
        return self.food_log.food_name  # Access food_name from the associated FoodLog instance


@receiver(post_save, sender='api.DonationRecord')
@receiver(post_delete, sender='api.DonationRecord')
def update_foodlog_status_on_donation_change(sender, instance, **kwargs):
    food_log = instance.food_log
    food_log.save()

@receiver(post_save, sender='api.WasteLog')
@receiver(post_delete, sender='api.WasteLog')
def update_foodlog_status_on_waste_change(sender, instance, **kwargs):
    food_log = instance.food_log
    if food_log:
        food_log.save()
