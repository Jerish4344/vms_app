from rest_framework import serializers
from vehicles.models import Vehicle, VehicleType
from trips.models import Trip
from maintenance.models import Maintenance
from fuel.models import FuelTransaction, FuelStation # Added FuelStation
from accounts.models import CustomUser
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Serializer for user accounts."""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name', 'user_type', 'phone_number']
        read_only_fields = ['id'] # Removed user_type from read_only as it might be needed for role checks
    
    def get_full_name(self, obj):
        return obj.get_full_name()

class VehicleTypeSerializer(serializers.ModelSerializer):
    """Serializer for vehicle types."""
    class Meta:
        model = VehicleType
        fields = ['id', 'name', 'description', 'category']

class VehicleSerializer(serializers.ModelSerializer):
    """Serializer for vehicles."""
    vehicle_type = VehicleTypeSerializer(read_only=True)
    vehicle_type_id = serializers.PrimaryKeyRelatedField(
        queryset=VehicleType.objects.all(),
        write_only=True,
        source='vehicle_type',
        allow_null=True # Allow vehicle type to be optional
    )
    status_display = serializers.SerializerMethodField()
    current_driver = serializers.SerializerMethodField() # Kept this, might be useful
    documents_valid = serializers.SerializerMethodField() # Kept this
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Vehicle
        fields = [
            'id', 'vehicle_type', 'vehicle_type_id', 'make', 'model', 'year', 
            'license_plate', 'vin', 'color', 'current_odometer', 'status', 
            'status_display', 'image', 'image_url', 'acquisition_date', 
            'fuel_type', 'seating_capacity', 'current_driver', 'documents_valid',
            'owner_name', 'rc_valid_till', 'insurance_expiry_date', 'fitness_expiry',
            'permit_expiry', 'pollution_cert_expiry', 'gps_fitted', 'gps_name',
            'driver_contact', 'assigned_driver', 'purpose_of_vehicle', 'company_owned',
            'usage_type', 'used_by'
        ]
        read_only_fields = ['id', 'status_display', 'current_driver', 'documents_valid', 'image_url']
    
    def get_status_display(self, obj):
        return obj.get_status_display() # Use model's get_status_display method
    
    def get_current_driver(self, obj):
        # Assuming get_current_driver() method exists on Vehicle model
        # and returns a User instance or None
        driver = obj.get_current_driver() if hasattr(obj, 'get_current_driver') else None
        if driver:
            return UserSerializer(driver).data
        return None
    
    def get_documents_valid(self, obj):
        # Assuming get_document_status() method exists
        return obj.get_document_status() if hasattr(obj, 'get_document_status') else None
    
    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

class TripSerializer(serializers.ModelSerializer):
    """Serializer for trips."""
    vehicle = VehicleSerializer(read_only=True)
    vehicle_id = serializers.PrimaryKeyRelatedField(
        queryset=Vehicle.objects.all(),
        write_only=True,
        source='vehicle'
    )
    driver = UserSerializer(read_only=True)
    driver_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        source='driver',
        allow_null=True, # Driver might not be assigned initially or could be system trip
        required=False
    )
    status_display = serializers.SerializerMethodField()
    duration_display = serializers.SerializerMethodField()
    distance = serializers.SerializerMethodField()
    
    class Meta:
        model = Trip
        fields = [
            'id', 'vehicle', 'vehicle_id', 'driver', 'driver_id', 
            'start_time', 'end_time', 'start_odometer', 'end_odometer',
            'origin', 'destination', 'purpose', 'notes', 'status',
            'status_display', 'duration_display', 'distance'
        ]
        read_only_fields = ['id', 'status_display', 'duration_display', 'distance']
    
    def get_status_display(self, obj):
        return obj.get_status_display() # Use model's get_status_display
    
    def get_duration_display(self, obj):
        return obj.duration # Use model's duration property or method
    
    def get_distance(self, obj):
        return obj.distance_traveled # Use model's distance_traveled property or method
    
    def validate(self, data):
        """
        Validate that a vehicle is available for a new trip and
        that end_odometer is greater than start_odometer.
        """
        # For new trips, check vehicle availability
        if not self.instance: 
            vehicle = data.get('vehicle')
            if vehicle and hasattr(vehicle, 'status') and vehicle.status != 'available':
                # Check if status is one of the known 'unavailable' types
                unavailable_statuses = ['maintenance', 'in_use', 'retired', 'unavailable']
                if vehicle.status.lower() in unavailable_statuses:
                    raise serializers.ValidationError(
                        f"Vehicle {vehicle.license_plate} is not available (current status: {vehicle.get_status_display()})"
                    )
        
        start_odometer = data.get('start_odometer', self.instance.start_odometer if self.instance else None)
        end_odometer = data.get('end_odometer')
        
        if end_odometer is not None and start_odometer is not None:
            if end_odometer <= start_odometer:
                raise serializers.ValidationError(
                    f"End odometer ({end_odometer}) must be greater than start odometer ({start_odometer})"
                )
        
        return data

class MaintenanceSerializer(serializers.ModelSerializer):
    """Serializer for maintenance records."""
    vehicle = VehicleSerializer(read_only=True)
    vehicle_id = serializers.PrimaryKeyRelatedField(
        queryset=Vehicle.objects.all(),
        write_only=True,
        source='vehicle'
    )
    status_display = serializers.SerializerMethodField()
    # Assuming maintenance_type and provider are CharFields or ForeignKeys that are handled by default
    # If they are ForeignKeys and need specific representation, create serializers for them.
    # For now, using PrimaryKeyRelatedField for provider if it's a FK.
    # provider = ProviderSerializer(read_only=True) # Example if Provider model and serializer exist
    # provider_id = serializers.PrimaryKeyRelatedField(queryset=Provider.objects.all(), source='provider', write_only=True)

    class Meta:
        model = Maintenance
        fields = [
            'id', 'vehicle', 'vehicle_id', 'maintenance_type', 'description', # Assuming maintenance_type is a FK to a MaintenanceType model or a choice field
            'status', 'status_display', 'scheduled_date', 'completion_date',
            'odometer_reading', 'cost', 'provider', 'notes' # Assuming provider is FK to a Provider model or CharField
        ]
        read_only_fields = ['id', 'status_display']
    
    def get_status_display(self, obj):
        return obj.get_status_display() # Use model's get_status_display

class FuelStationSerializer(serializers.ModelSerializer):
    """Serializer for fuel stations."""
    class Meta:
        model = FuelStation
        fields = ['id', 'name', 'address', 'latitude', 'longitude', 'station_type']

class FuelTransactionSerializer(serializers.ModelSerializer):
    """Serializer for fuel transactions, supporting both fuel and electric vehicles."""
    vehicle = VehicleSerializer(read_only=True)
    vehicle_id = serializers.PrimaryKeyRelatedField(
        queryset=Vehicle.objects.all(),
        write_only=True,
        source='vehicle'
    )
    driver = UserSerializer(read_only=True)
    driver_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        source='driver'
    )
    fuel_station = FuelStationSerializer(read_only=True, allow_null=True)
    fuel_station_id = serializers.PrimaryKeyRelatedField(
        queryset=FuelStation.objects.all(),
        write_only=True,
        source='fuel_station',
        allow_null=True,
        required=False
    )
    is_electric = serializers.SerializerMethodField()
    receipt_image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = FuelTransaction
        fields = [
            'id', 
            'vehicle', 'vehicle_id', 
            'driver', 'driver_id',
            'fuel_station', 'fuel_station_id',
            'date', 
            'fuel_type', 
            'quantity', 
            'cost_per_liter', 
            'energy_consumed', 
            'cost_per_kwh', 
            'charging_duration_minutes',
            'total_cost', 
            'odometer_reading', 
            'receipt_image', 
            'notes',
            'is_electric'
        ]
        read_only_fields = ['id', 'vehicle', 'driver', 'fuel_station', 'is_electric']

    def get_is_electric(self, obj):
        return obj.is_electric_transaction()

    def validate_odometer_reading(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Odometer reading cannot be negative.")
        return value

    def validate(self, data):
        # Basic validation, model's save method handles total_cost and fuel_type for electric.
        vehicle = data.get('vehicle', getattr(self.instance, 'vehicle', None))
        if not vehicle:
            # This case should be caught by vehicle_id being required if creating
            if not self.instance: # Only if creating and vehicle_id not provided
                 raise serializers.ValidationError({"vehicle_id": "Vehicle is required."})
        
        # Odometer check against vehicle's current odometer if creating
        # For updates, this logic might be more complex (e.g., allow corrections)
        if not self.instance: # Only on create
            odometer_reading = data.get('odometer_reading')
            if vehicle and hasattr(vehicle, 'current_odometer') and vehicle.current_odometer is not None and odometer_reading is not None:
                if odometer_reading < vehicle.current_odometer:
                    # Allow if it's a minor correction or first entry, but flag if significantly lower.
                    # For simplicity, we'll just raise a warning or allow it.
                    # For stricter validation:
                    # raise serializers.ValidationError(
                    #     f"Odometer reading ({odometer_reading}) cannot be less than vehicle's current odometer ({vehicle.current_odometer})."
                    # )
                    pass # Or add specific logic for handling this.

        # Ensure that for electric transactions, energy fields are provided if fuel fields are not, and vice-versa.
        # The model's is_electric_transaction() might not be available here directly without the instance.
        # We can infer from vehicle.fuel_type or vehicle.is_electric() if vehicle is resolved.
        
        fuel_type = data.get('fuel_type')
        quantity = data.get('quantity')
        cost_per_liter = data.get('cost_per_liter')
        energy_consumed = data.get('energy_consumed')
        cost_per_kwh = data.get('cost_per_kwh')

        # If vehicle object is available (e.g. during create when vehicle_id is resolved to vehicle instance)
        # or if self.instance is available (during update)
        current_vehicle = vehicle or (self.instance.vehicle if self.instance else None)

        if current_vehicle and hasattr(current_vehicle, 'is_electric') and current_vehicle.is_electric():
            if fuel_type and fuel_type.lower() != 'electric':
                data['fuel_type'] = 'Electric' # Correct fuel_type if vehicle is electric
            elif not fuel_type:
                 data['fuel_type'] = 'Electric'

            if quantity is not None or cost_per_liter is not None:
                raise serializers.ValidationError("Fuel quantity/cost_per_liter should not be provided for an electric vehicle.")
            if energy_consumed is None and cost_per_kwh is None and not data.get('total_cost'):
                # If total_cost is also not provided, then these are needed.
                # Model save handles total_cost calculation, so this might be too strict here.
                pass
        elif current_vehicle: # Non-electric
            if energy_consumed is not None or cost_per_kwh is not None:
                raise serializers.ValidationError("Energy consumed/cost_per_kwh should not be provided for a non-electric vehicle.")
            if quantity is None and cost_per_liter is None and not data.get('total_cost'):
                # Similar to above, model save handles total_cost.
                pass
        
        # Total cost validation: if provided, must be positive
        total_cost = data.get('total_cost')
        if total_cost is not None and total_cost < 0:
            raise serializers.ValidationError({"total_cost": "Total cost cannot be negative."})
            
        return data
