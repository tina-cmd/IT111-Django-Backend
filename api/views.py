from rest_framework import viewsets, permissions
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

# Auth endpoints
class RegisterView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        data = request.data
        user = User.objects.create_user(
            username=data['username'],
            email=data.get('email'),
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name']
        )
        token, _ = Token.objects.get_or_create(user=user)
        return Response({ 'id': token.user.id, 'token': token.key, 'username': token.user.username, 'email': token.user.email, 'first_name': token.user.first_name })

class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        token = Token.objects.get(key=response.data['token'])
        return Response({ 'id': token.user.id, 'token': token.key, 'username': token.user.username, 'email': token.user.email, 'first_name': token.user.first_name })

class UserDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

class WasteLogViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = WasteLog.objects.all()
    serializer_class = WasteLogSerializer

    @action(detail=False, methods=['get'], url_path='my')
    def waste_logs_for_authenticated_user(self, request):
        # Filter the waste logs by the currently authenticated user
        waste_logs = self.queryset.filter(user=request.user)
        
        # Serialize the filtered waste logs
        serializer = self.get_serializer(waste_logs, many=True)
        
        # Return the serialized data in the response
        return Response(serializer.data)

    # Custom action to allow users to add waste logs
    @action(detail=False, methods=['post'], url_path='add')
    def add_waste(self, request):
        user = request.user
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BulkDonationNativeView(View):
    def post(self, request):
        # Verify authentication manually (since we're not using DRF permissions)
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Token '):
            return JsonResponse({"error": "Unauthorized"}, status=401)
        
        token = auth_header.split(' ')[1]
        try:
            user = User.objects.get(auth_token=token)
        except User.DoesNotExist:
            return JsonResponse({"error": "Invalid token"}, status=401)

        try:
            data = json.loads(request.body)
            center_id = data['center']
            items = data['items']
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({"error": "Invalid data format"}, status=400)

        try:
            center = DonationCenter.objects.get(id=center_id)
        except DonationCenter.DoesNotExist:
            return JsonResponse({"error": "Donation center not found"}, status=400)

        donation_records = []
        errors = []

        # Process items transactionally
        with transaction.atomic():
            for idx, item in enumerate(items):
                try:
                    food_log = FoodLog.objects.get(id=item['food_log'], user=user)
                    quantity = item['quantity']
                    
                    if quantity > food_log.available_quantity:
                        errors.append(f"Item {idx}: Quantity exceeds available")
                        continue
                    
                    donation = DonationRecord.objects.create(
                        user=user,
                        center=center,
                        food_log=food_log,
                        quantity=quantity
                    )
                    donation_records.append({
                        "id": donation.id,
                        "food_log": food_log.id,
                        "quantity": quantity
                    })
                except (KeyError, FoodLog.DoesNotExist) as e:
                    errors.append(f"Item {idx}: Invalid data - {str(e)}")

            if errors:
                transaction.set_rollback(True)  # Rollback all changes if any error
                return JsonResponse({"errors": errors}, status=400)

        return JsonResponse({"donations": donation_records}, status=201)
    
@method_decorator(csrf_exempt, name='dispatch')
class MultiDonationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = MultiDonationSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            try:
                donation_records = serializer.save()
                response_serializer = DonationRecordSerializer(donation_records, many=True)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)