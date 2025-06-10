from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    VehicleViewSet,
    VehicleTypeViewSet,
    TripViewSet,
    MaintenanceViewSet,
    FuelTransactionViewSet,
    FuelStationViewSet, # Added FuelStationViewSet
    UserViewSet,
    CustomAuthToken
)

router = DefaultRouter()
router.register(r'vehicles', VehicleViewSet, basename='vehicle')
router.register(r'vehicle-types', VehicleTypeViewSet, basename='vehicletype')
router.register(r'trips', TripViewSet, basename='trip')
router.register(r'maintenance', MaintenanceViewSet, basename='maintenance')
router.register(r'fuel-transactions', FuelTransactionViewSet, basename='fueltransaction')
router.register(r'fuel-stations', FuelStationViewSet, basename='fuelstation') # Added FuelStationViewSet
router.register(r'users', UserViewSet, basename='user')


urlpatterns = [
    path('', include(router.urls)),
    path('login/', CustomAuthToken.as_view(), name='api_login'),
    # path('logout/', LogoutView.as_view(), name='api_logout'), # Example: ensure a proper DRF logout view if needed
]
