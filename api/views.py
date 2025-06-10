from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.contrib.auth import get_user_model, authenticate
from django.core.exceptions import ValidationError
from django.db.models import Q

from .serializers import (
    VehicleSerializer,
    VehicleTypeSerializer,
    TripSerializer,
    MaintenanceSerializer,
    FuelTransactionSerializer,
    FuelStationSerializer, # Added FuelStationSerializer
    UserSerializer
)
from .permissions import (
    IsAdminOrReadOnly,
    IsOwnerOrAdmin,
    IsDriverOrAdmin,
    IsVehicleAssignedToUser,
    IsManagerOrAdmin,
    IsActiveUser,
    CanStartTrip
)

from vehicles.models import Vehicle, VehicleType
from trips.models import Trip
from maintenance.models import Maintenance
from fuel.models import FuelTransaction, FuelStation # Added FuelStation

User = get_user_model()

class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({
                'detail': 'Username and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=username, password=password)

        if user and user.is_active:
            token, created = Token.objects.get_or_create(user=user)
            user_serializer = UserSerializer(user)
            return Response({
                'token': token.key,
                'user': user_serializer.data
            })
        else:
            return Response({
                'detail': 'Invalid credentials or inactive account'
            }, status=status.HTTP_401_UNAUTHORIZED)

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for users.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsActiveUser]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    filterset_fields = ['user_type']

    def get_queryset(self):
        """
        Restrict users to seeing only themselves unless they're staff.
        """
        user = self.request.user
        if user.is_staff or (hasattr(user, 'user_type') and user.user_type in ['admin', 'manager', 'vehicle_manager']):
            return User.objects.all()
        return User.objects.filter(id=user.id)

    def get_permissions(self):
        """
        Different permissions for different actions.
        """
        if self.action == 'me':
            return [IsActiveUser()]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsManagerOrAdmin()]
        return [IsActiveUser()]

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Return the current user's details.
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

class VehicleTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint for vehicle types.
    """
    queryset = VehicleType.objects.all()
    serializer_class = VehicleTypeSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsActiveUser, IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'category']

class VehicleViewSet(viewsets.ModelViewSet):
    """
    API endpoint for vehicles.
    """
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsActiveUser]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['make', 'model', 'license_plate', 'vin']
    filterset_fields = ['status', 'vehicle_type', 'fuel_type', 'company_owned', 'usage_type']

    def get_permissions(self):
        """
        Custom permissions based on action.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsActiveUser(), IsAdminOrReadOnly()]
        return [IsActiveUser()]

    def get_queryset(self):
        """
        Filter vehicles based on user role and assignment.
        Admins/Managers see all vehicles.
        Drivers see vehicles assigned to them OR any vehicle that is 'available'.
        """
        user = self.request.user
        if user.is_staff or (hasattr(user, 'user_type') and user.user_type in ['admin', 'manager', 'vehicle_manager']):
            return Vehicle.objects.all()
        else:
            # Drivers see vehicles assigned to them by full name OR any 'available' vehicle
            # Ensure user.get_full_name() is a reliable field for assignment comparison.
            # If assigned_driver stores user ID, then Q(assigned_driver=user) or Q(assigned_driver_id=user.id)
            return Vehicle.objects.filter(
                Q(assigned_driver__iexact=user.get_full_name()) | Q(status='available') # Assuming assigned_driver is a CharField storing name
            ).distinct()


    @action(detail=True, methods=['get'])
    def trips(self, request, pk=None):
        """
        Return all trips for this vehicle.
        """
        vehicle = self.get_object()
        trips_qs = Trip.objects.filter(vehicle=vehicle) # Renamed to avoid conflict

        user = request.user
        if not (user.is_staff or (hasattr(user, 'user_type') and user.user_type in ['admin', 'manager', 'vehicle_manager'])):
            trips_qs = trips_qs.filter(driver=user)

        page = self.paginate_queryset(trips_qs)
        if page is not None:
            serializer = TripSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = TripSerializer(trips_qs, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def maintenance(self, request, pk=None):
        """
        Return all maintenance records for this vehicle.
        """
        vehicle = self.get_object()
        maintenance_records = Maintenance.objects.filter(vehicle=vehicle)
        page = self.paginate_queryset(maintenance_records)
        if page is not None:
            serializer = MaintenanceSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = MaintenanceSerializer(maintenance_records, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def fuel(self, request, pk=None):
        """
        Return all fuel transactions for this vehicle.
        """
        vehicle = self.get_object()
        fuel_transactions_qs = FuelTransaction.objects.filter(vehicle=vehicle) # Renamed

        user = request.user
        if not (user.is_staff or (hasattr(user, 'user_type') and user.user_type in ['admin', 'manager', 'vehicle_manager'])):
            fuel_transactions_qs = fuel_transactions_qs.filter(driver=user)

        page = self.paginate_queryset(fuel_transactions_qs)
        if page is not None:
            serializer = FuelTransactionSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = FuelTransactionSerializer(fuel_transactions_qs, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def active_trip(self, request, pk=None):
        """
        Return the active trip for this vehicle, if any.
        """
        vehicle = self.get_object()
        try:
            trip = None
            if hasattr(vehicle, 'get_active_trip'):
                 trip = vehicle.get_active_trip()
            else: # Fallback if method doesn't exist
                trip = Trip.objects.filter(vehicle=vehicle, status__iexact='ongoing').first()

            if trip:
                user = request.user
                if not (user.is_staff or (hasattr(user, 'user_type') and user.user_type in ['admin', 'manager', 'vehicle_manager'])):
                    if trip.driver != user:
                        return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

                serializer = TripSerializer(trip, context={'request': request})
                return Response(serializer.data)
            return Response({"detail": "No active trip found for this vehicle."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TripViewSet(viewsets.ModelViewSet):
    """
    API endpoint for trips.
    """
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsActiveUser]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['origin', 'destination', 'purpose', 'vehicle__license_plate', 'driver__username']
    filterset_fields = ['status', 'vehicle', 'driver']

    def get_queryset(self):
        """
        Restrict trips to those related to the current user unless they're staff.
        """
        user = self.request.user
        if user.is_staff or (hasattr(user, 'user_type') and user.user_type in ['admin', 'manager', 'vehicle_manager']):
            return Trip.objects.all()
        return Trip.objects.filter(driver=user)

    def get_permissions(self):
        """
        Custom permissions based on action.
        """
        if self.action == 'create':
            return [IsActiveUser(), CanStartTrip()]
        elif self.action in ['update', 'partial_update', 'destroy', 'end_trip', 'cancel_trip']:
            return [IsActiveUser(), IsOwnerOrAdmin()]
        return [IsActiveUser()]

    def perform_create(self, serializer):
        """
        Set the driver to the current user if not provided.
        Update vehicle status to 'in_use' and set current_odometer.
        """
        if 'driver' not in serializer.validated_data and hasattr(self.request.user, 'id'):
            serializer.validated_data['driver'] = self.request.user
        
        trip = serializer.save()

        # Update vehicle status and odometer
        vehicle = trip.vehicle
        if hasattr(vehicle, 'status'):
            vehicle.status = 'in_use'
        if hasattr(vehicle, 'current_odometer') and trip.start_odometer is not None:
            # Only update if new odometer is greater or it's the first reading
            if vehicle.current_odometer is None or trip.start_odometer > vehicle.current_odometer:
                 vehicle.current_odometer = trip.start_odometer
        vehicle.save()


    @action(detail=True, methods=['post'])
    def end_trip(self, request, pk=None):
        """
        End an ongoing trip.
        """
        trip = self.get_object()

        if trip.status.lower() != 'ongoing': # Case-insensitive status check
            return Response(
                {"detail": "Only ongoing trips can be ended."},
                status=status.HTTP_400_BAD_REQUEST
            )

        end_odometer_str = request.data.get('end_odometer')
        notes = request.data.get('notes', '')

        if not end_odometer_str:
            return Response(
                {"detail": "End odometer reading is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            end_odometer = int(end_odometer_str)
            if trip.start_odometer is not None and end_odometer <= trip.start_odometer:
                return Response(
                    {"detail": f"End odometer ({end_odometer}) must be greater than start odometer ({trip.start_odometer})."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            trip.end_odometer = end_odometer
            trip.end_time = timezone.now()
            trip.notes = notes
            trip.status = 'completed'
            trip.save()

            if hasattr(trip.vehicle, 'status'):
                trip.vehicle.status = 'available'
            if hasattr(trip.vehicle, 'current_odometer'):
                trip.vehicle.current_odometer = end_odometer
            trip.vehicle.save()

            serializer = self.get_serializer(trip)
            return Response(serializer.data)

        except ValueError:
            return Response(
                {"detail": "End odometer must be a valid number."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def cancel_trip(self, request, pk=None):
        """
        Cancel an ongoing trip.
        """
        trip = self.get_object()

        if trip.status.lower() != 'ongoing': # Case-insensitive
            return Response(
                {"detail": "Only ongoing trips can be cancelled."},
                status=status.HTTP_400_BAD_REQUEST
            )

        reason = request.data.get('reason', 'Trip cancelled by user')

        try:
            trip.status = 'cancelled'
            trip.end_time = timezone.now() # Or keep null if cancellation means it never effectively ended
            trip.notes = f"Cancelled: {reason}. {trip.notes or ''}".strip()
            trip.save()

            if hasattr(trip.vehicle, 'status'):
                trip.vehicle.status = 'available'
            trip.vehicle.save()

            serializer = self.get_serializer(trip)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )

class MaintenanceViewSet(viewsets.ModelViewSet):
    """
    API endpoint for maintenance records.
    """
    queryset = Maintenance.objects.all()
    serializer_class = MaintenanceSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsActiveUser]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['description', 'provider__name', 'notes', 'vehicle__license_plate']
    filterset_fields = ['status', 'vehicle', 'maintenance_type']

    def get_permissions(self):
        """
        Custom permissions based on action.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsActiveUser(), IsManagerOrAdmin()] # Changed from IsAdminOrReadOnly
        return [IsActiveUser()]

    def perform_create(self, serializer):
        """
        Set reported_by to the current user if not provided.
        """
        if 'reported_by' not in serializer.validated_data and hasattr(self.request.user, 'id'):
            serializer.save(reported_by=self.request.user)
        else:
            serializer.save()

class FuelStationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for fuel stations.
    """
    queryset = FuelStation.objects.all()
    serializer_class = FuelStationSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['name', 'address']
    filterset_fields = ['station_type']

    def get_permissions(self):
        """
        Custom permissions for fuel station actions.
        - All active users can list/retrieve.
        - Only Managers/Admins can create, update, or delete stations.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsActiveUser(), IsManagerOrAdmin()]
        return [IsActiveUser()]

class FuelTransactionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for fuel transactions.
    """
    queryset = FuelTransaction.objects.all()
    serializer_class = FuelTransactionSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['vehicle__license_plate', 'driver__username', 'fuel_station__name', 'notes']
    filterset_fields = ['vehicle', 'driver', 'fuel_type', 'fuel_station']

    def get_queryset(self):
        """
        Restrict fuel transactions to those related to the current user unless they're staff.
        """
        user = self.request.user
        if user.is_staff or (hasattr(user, 'user_type') and user.user_type in ['admin', 'manager', 'vehicle_manager']):
            return FuelTransaction.objects.all()
        return FuelTransaction.objects.filter(driver=user)

    def get_permissions(self):
        """
        Custom permissions based on action.
        - All authenticated users can create fuel transactions.
        - Only owner or admin can update/delete.
        """
        if self.action == 'create':
            return [IsActiveUser()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsActiveUser(), IsOwnerOrAdmin()]
        return [IsActiveUser()] # For list, retrieve

    def perform_create(self, serializer):
        """
        Set the driver to the current user if not provided.
        Update vehicle's current odometer if this transaction's reading is higher.
        """
        driver = serializer.validated_data.get('driver')
        if not driver and hasattr(self.request.user, 'id'):
            driver = self.request.user
        
        transaction = serializer.save(driver=driver)

        # Update vehicle's current odometer
        vehicle = transaction.vehicle
        if hasattr(vehicle, 'current_odometer') and transaction.odometer_reading is not None:
            if vehicle.current_odometer is None or transaction.odometer_reading > vehicle.current_odometer:
                vehicle.current_odometer = transaction.odometer_reading
                vehicle.save(update_fields=['current_odometer'])
