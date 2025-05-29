from rest_framework import serializers
from django.contrib.auth.models import User
from .models import *
from datetime import date
from django.db import transaction

# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ['id', 'username', 'email', 'first_name', 'last_name']

class UserSerializer(serializers.ModelSerializer):
    prefers_dark_mode = serializers.BooleanField(source='profile.prefers_dark_mode')

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'prefers_dark_mode']
        read_only_fields = ['id']

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})
        prefers_dark_mode = profile_data.get('prefers_dark_mode', instance.profile.prefers_dark_mode)

        # Update user fields
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        
        # Update password if provided
        password = validated_data.get('password')
        if password:
            instance.set_password(password)
        
        instance.save()

        # Update profile
        instance.profile.prefers_dark_mode = prefers_dark_mode
        instance.profile.save()

        return instance

class FoodCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodCategory
        fields = '__all__'


class FoodLogSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=FoodCategory.objects.all(),
        allow_null=True,
        required=False
    )
    category_name = serializers.CharField(source='category.name', read_only=True)
    expiration_date = serializers.DateField(required=False, allow_null=True)
    donated_quantity = serializers.IntegerField(read_only=True)
    wasted_quantity = serializers.IntegerField(read_only=True)
    available_quantity = serializers.IntegerField(read_only=True)

    class Meta:
        model = FoodLog
        fields = ['id', 'food_name', 'quantity', 'category', 'category_name', 'date_logged', 'expiration_date', 'status', 'user', 'donated_quantity', 'wasted_quantity', 'available_quantity']
        read_only_fields = ['id', 'user', 'date_logged', 'status', 'category_name', 'donated_quantity', 'wasted_quantity', 'available_quantity']

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be a positive integer.")
        return value
    
class DonationCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = DonationCenter
        fields = '__all__'

class DonationRecordSerializer(serializers.ModelSerializer):
    center_name = serializers.CharField(source='center.name', read_only=True)
    food_log_name = serializers.CharField(source='food_log.food_name', read_only=True)
    food_log_quantity = serializers.IntegerField(source='food_log.quantity', read_only=True)
    user_username = serializers.CharField(source='user.first_name', read_only=True)

    user_id = serializers.IntegerField(source='user.id', read_only=True)
    
    class Meta:
        model = DonationRecord
        fields = ['id', 'date_donated', 'center', 'center_name', 'user', 'user_id', 'user_username', 'food_log', 'food_log_name', 'food_log_quantity', 'quantity']

class WasteLogSerializer(serializers.ModelSerializer):
    food_name = serializers.CharField(source='food_log.food_name', read_only=True)  # Use food_name from FoodLog
    food_log = serializers.PrimaryKeyRelatedField(queryset=FoodLog.objects.all(), write_only=True)

    class Meta:
        model = WasteLog
        fields = ['id', 'user', 'food_log', 'food_name', 'quantity', 'reason', 'date_logged']
        read_only_fields = ['id', 'date_logged']

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value

    def validate(self, data):
        food_log = data.get('food_log')
        quantity = data.get('quantity')

        if food_log is None or quantity is None:
            return data

        # If expired, allow any quantity
        if food_log.expiration_date and food_log.expiration_date < date.today():
            return data

        # Otherwise, quantity must be <= available quantity
        available_quantity = food_log.available_quantity
        if quantity > available_quantity:
            raise serializers.ValidationError("Waste quantity cannot exceed available food quantity.")

        return data

    def create(self, validated_data):
        waste_log = WasteLog.objects.create(**validated_data)
        return waste_log

class MultiDonationItemSerializer(serializers.Serializer):
    food_log = serializers.PrimaryKeyRelatedField(queryset=FoodLog.objects.all())
    quantity = serializers.IntegerField()

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value

class MultiDonationSerializer(serializers.Serializer):
    center = serializers.PrimaryKeyRelatedField(queryset=DonationCenter.objects.all())
    items = MultiDonationItemSerializer(many=True)

    def validate(self, data):
        items = data.get('items', [])
        errors = {}
        user = self.context['request'].user

        # Validate each item
        for idx, item in enumerate(items):
            food_log = item['food_log']
            quantity = item['quantity']
            available_quantity = food_log.available_quantity

            if food_log.user != user:
                errors[idx] = f"Food log id {food_log.id} does not belong to the authenticated user."
            if quantity > available_quantity:
                errors[idx] = f"Donation quantity for food_log id {food_log.id} cannot exceed available quantity ({available_quantity})."

        if errors:
            raise serializers.ValidationError(errors)
        return data

    @transaction.atomic
    def create(self, validated_data):
        user = self.context['request'].user
        center = validated_data['center']
        items = validated_data['items']
        
        donation_records = []
        for item in items:
            food_log = item['food_log']
            quantity = item['quantity']

            # Update FoodLog available quantity
            if quantity > food_log.available_quantity:
                raise serializers.ValidationError({
                    "detail": f"Insufficient quantity for food_log id {food_log.id}. Available: {food_log.available_quantity}"
                })
            
            donation_record = DonationRecord.objects.create(
                user=user,
                center=center,
                food_log=food_log,
                quantity=quantity
            )
            # Update the FoodLog status and available quantity (handled by save method)
            # food_log.quantity -= quantity
            food_log.save()
            donation_records.append(donation_record)
        
        return donation_records