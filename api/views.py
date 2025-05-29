from rest_framework import viewsets, permissions, generics
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from .models import *
from .serializers import *
from rest_framework.decorators import action
from rest_framework import status
from rest_framework import viewsets, mixins, permissions
import json
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models import Count
from itertools import chain

class UserDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        request.user.delete()
        return Response({"message": "User account deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

class UserStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        # Total counts
        total_food_logs = FoodLog.objects.filter(user=user).count()
        total_waste_logs = WasteLog.objects.filter(user=user).count()
        total_donations = DonationRecord.objects.filter(user=user).count()

        # Recent activities (last 5 combined)
        food_logs = FoodLog.objects.filter(user=user).order_by('-date_logged')[:5]
        waste_logs = WasteLog.objects.filter(user=user).order_by('-date_logged')[:5]
        donations = DonationRecord.objects.filter(user=user).order_by('-date_donated')[:5]

        activities = []
        for item in food_logs:
            activities.append({
                "type": "food_log",
                "description": f"Logged {item.food_name}",
                "date": item.date_logged
            })
        for item in waste_logs:
            activities.append({
                "type": "waste_log",
                "description": f"Wasted {item.quantity} of {item.food_name}",
                "date": item.date_logged
            })
        for item in donations:
            activities.append({
                "type": "donation",
                "description": f"Donated {item.quantity} of {item.food_log.food_name} to {item.center.name}",
                "date": item.date_donated
            })

        # Sort by date and take the top 5
        activities = sorted(activities, key=lambda x: x["date"], reverse=True)[:5]

        return Response({
            "total_food_logs": total_food_logs,
            "total_waste_logs": total_waste_logs,
            "total_donations": total_donations,
            "recent_activities": activities
        })

# ... (rest of your existing views remain unchanged)

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        token = request.headers.get('Authorization').split(' ')[1]  # 'Token <your_token>'
        
        # Try to find and delete the token
        try:
            token_obj = Token.objects.get(key=token)
            token_obj.delete()  # Invalidate token
            return Response({"message": "Successfully logged out."}, status=200)
        except Token.DoesNotExist:
            return Response({"message": "Token not found."}, status=400)

class FoodLogViewSet(viewsets.ModelViewSet):
    queryset = FoodLog.objects.all()
    serializer_class = FoodLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        try:
            serializer.save(user=self.request.user)
        except Exception as e:
            raise serializers.ValidationError({"detail": f"Failed to create food log: {str(e)}"})

    @action(detail=False, methods=['get'], url_path='my')
    def my_logs(self, request):
        logs = self.queryset.filter(user=request.user)
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)

class FoodCategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = FoodCategory.objects.all()
    serializer_class = FoodCategorySerializer

class DonationCenterViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = DonationCenter.objects.all()
    serializer_class = DonationCenterSerializer

class DonationRecordViewSet(viewsets.ModelViewSet):
    queryset = DonationRecord.objects.all()
    serializer_class = DonationRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
    @action(detail=False, methods=['get'], url_path='my')
    def my_logs(self, request):
        logs = self.queryset.filter(user=request.user)
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)

