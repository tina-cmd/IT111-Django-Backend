from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'foodlogs', FoodLogViewSet)
router.register(r'categories', FoodCategoryViewSet)
router.register(r'donationcenters', DonationCenterViewSet)
router.register(r'donations', DonationRecordViewSet)
router.register(r'wastelogs', WasteLogViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterView.as_view()),
    path('login/', CustomAuthToken.as_view()),
    path('user/', UserDetailView.as_view()),
    path('user/stats/', UserStatsView.as_view(), name='user-stats'),
    path('logout/', LogoutView.as_view()),
    path('wastelogs/add/', WasteLogViewSet.as_view({'post': 'add_waste'}), name='add-waste'),
    # path('donations/bulk-native/', BulkDonationNativeView.as_view(), name='bulk-donation-native'),
    path('multi-donations/', MultiDonationView.as_view(), name='multi-donation'),
]
