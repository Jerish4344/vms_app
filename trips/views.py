from django.forms import ValidationError
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from accounts.permissions import AdminRequiredMixin, ManagerRequiredMixin, VehicleManagerRequiredMixin, DriverRequiredMixin
from .models import Trip
from vehicles.models import Vehicle
from accounts.models import CustomUser
from .forms import TripForm, EndTripForm

class CanDriveVehicleMixin:
    """
    Mixin to check if user can drive vehicles.
    Allows: drivers, admins, managers, and vehicle_managers
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Allow these user types to drive vehicles
        allowed_user_types = ['driver', 'admin', 'manager', 'vehicle_manager']
        
        if request.user.user_type not in allowed_user_types:
            messages.error(request, 'You do not have permission to access this feature.')
            raise PermissionDenied("User does not have vehicle driving permissions")
        
        return super().dispatch(request, *args, **kwargs)

class TripListView(LoginRequiredMixin, ListView):
    model = Trip
    template_name = 'trips/trip_list.html'
    context_object_name = 'trips'
    paginate_by = 20
    
    def get_queryset(self):
        # Get base queryset based on user permissions
        if self.request.user.user_type == 'driver':
            queryset = Trip.objects.filter(driver=self.request.user)
        elif self.request.user.user_type in ['admin', 'manager', 'vehicle_manager']:
            queryset = Trip.objects.all()
        else:
            queryset = Trip.objects.none()
        
        # Apply filters
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(vehicle__license_plate__icontains=search_query) |
                Q(vehicle__make__icontains=search_query) |
                Q(vehicle__model__icontains=search_query) |
                Q(driver__first_name__icontains=search_query) |
                Q(driver__last_name__icontains=search_query) |
                Q(origin__icontains=search_query) |
                Q(destination__icontains=search_query) |
                Q(purpose__icontains=search_query)
            )
        
        vehicle_id = self.request.GET.get('vehicle', '')
        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)
        
        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.select_related('vehicle', 'driver').order_by('-start_time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all trips for separation (without pagination)
        all_trips = self.get_queryset()
        
        # Separate trips by status
        ongoing_trips = []
        completed_trips = []
        cancelled_trips = []
        
        for trip in all_trips:
            if trip.status == 'ongoing':
                ongoing_trips.append(trip)
            elif trip.status == 'completed':
                completed_trips.append(trip)
            elif trip.status == 'cancelled':
                cancelled_trips.append(trip)
        
        # Add separated trips to context
        context['ongoing_trips'] = ongoing_trips
        context['completed_trips'] = completed_trips
        context['cancelled_trips'] = cancelled_trips
        
        # Add counts
        context['ongoing_count'] = len(ongoing_trips)
        context['completed_count'] = len(completed_trips)
        context['cancelled_count'] = len(cancelled_trips)
        
        # Add vehicles for filter
        if self.request.user.user_type == 'driver':
            context['vehicles'] = Vehicle.objects.filter(
                Q(assigned_driver=self.request.user) | 
                Q(trips__driver=self.request.user)
            ).distinct()
        else:
            context['vehicles'] = Vehicle.objects.all()
        
        # Add search parameters for maintaining filters in pagination
        search_params = {}
        if self.request.GET.get('search'):
            search_params['search'] = self.request.GET.get('search')
        if self.request.GET.get('vehicle'):
            search_params['vehicle'] = self.request.GET.get('vehicle')
        if self.request.GET.get('status'):
            search_params['status'] = self.request.GET.get('status')
        
        context['search_params'] = search_params
        
        # Add user permissions context
        context['can_start_trip'] = self.request.user.user_type in ['driver', 'admin', 'manager', 'vehicle_manager']
        
        return context

class TripDetailView(LoginRequiredMixin, DetailView):
    model = Trip
    template_name = 'trips/trip_detail.html'
    context_object_name = 'trip'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trip = self.get_object()
        
        # Add locations if you have a location tracking model
        if hasattr(trip, 'locations'):
            context['locations'] = trip.locations.all().order_by('timestamp')
        
        # Add route information for display
        context['route_summary'] = trip.get_route_summary()
        
        # Check if user can end this trip
        context['can_end_trip'] = trip.can_be_ended_by(self.request.user)
        
        return context
    
class TripTrackingView(LoginRequiredMixin, CanDriveVehicleMixin, TemplateView):
    """
    View for users to track their active trip with geolocation.
    This provides a real-time tracking interface with maps.
    """
    template_name = 'trips/trip_tracking.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trip_id = self.kwargs.get('pk')
        trip = get_object_or_404(Trip, pk=trip_id)
        
        # Check permissions - trip driver or management users can track
        if (trip.driver != self.request.user and 
            self.request.user.user_type not in ['admin', 'manager', 'vehicle_manager']):
            messages.error(self.request, "You can only track trips assigned to you.")
            return redirect('trip_list')
        
        # Trip should be active
        if trip.status != 'ongoing':
            messages.error(self.request, "This trip is not currently active.")
            return redirect('trip_list')
        
        context['trip'] = trip
        
        # Get fleet manager for emergency contact
        fleet_managers = CustomUser.objects.filter(user_type__in=['manager', 'vehicle_manager'])
        context['fleet_manager'] = fleet_managers.first() if fleet_managers.exists() else None
        
        # Get nearby fuel stations (could be enhanced with geolocation API)
        context['fuel_stations'] = True  # Placeholder for actual fuel station data
        
        return context

class StartTripView(LoginRequiredMixin, CanDriveVehicleMixin, CreateView):
    """
    View for starting a new trip.
    Accessible by: drivers, admins, managers, and vehicle_managers
    """
    model = Trip
    form_class = TripForm
    template_name = 'trips/start_trip.html'
    success_url = reverse_lazy('trip_list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Only show available vehicles
        form.fields['vehicle'].queryset = Vehicle.objects.filter(status='available')
        return form
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add available vehicles to the context
        available_vehicles = Vehicle.objects.filter(status='available').select_related('vehicle_type')
        context['available_vehicles'] = available_vehicles
        
        # Add vehicle types for filter buttons
        try:
            from vehicles.models import VehicleType
            context['vehicle_types'] = VehicleType.objects.all()
        except ImportError:
            # If VehicleType model doesn't exist, set empty queryset
            context['vehicle_types'] = []
        
        # Add user role information for template display
        context['user_role'] = self.request.user.get_user_type_display()
        context['is_management'] = self.request.user.user_type in ['admin', 'manager', 'vehicle_manager']
        
        # Check if user has active trips
        active_trips = Trip.objects.filter(
            driver=self.request.user, 
            status='ongoing'
        )
        context['active_trips'] = active_trips
        context['has_active_trip'] = active_trips.exists()
        
        return context
    
    def form_valid(self, form):
        # Check if user already has an active trip (optional restriction)
        active_trips = Trip.objects.filter(
            driver=self.request.user, 
            status='ongoing'
        )
        
        if active_trips.exists():
            messages.warning(
                self.request,
                f'You already have an active trip. Please end your current trip before starting a new one.'
            )
            return redirect('trip_list')
        
        # Set the driver to the current user
        form.instance.driver = self.request.user
        form.instance.status = 'ongoing'
        
        # Set the start time to the current time
        form.instance.start_time = timezone.now()
        
        # Update vehicle status to 'in_use'
        vehicle = form.instance.vehicle
        vehicle.status = 'in_use'
        vehicle.save()
        
        # Success message with user role indication
        user_role = self.request.user.get_user_type_display()
        messages.success(
            self.request, 
            f'Trip started successfully by {user_role} from {form.instance.origin} to {form.instance.destination}!'
        )
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)

class EndTripView(LoginRequiredMixin, UpdateView):
    model = Trip
    template_name = 'trips/end_trip_form.html'
    fields = ['end_odometer', 'notes']
    
    def get_object(self):
        trip = get_object_or_404(Trip, pk=self.kwargs['pk'], status='ongoing')
        
        # Check permissions
        if not trip.can_be_ended_by(self.request.user):
            messages.error(self.request, 'You do not have permission to end this trip.')
            raise PermissionDenied("Cannot end this trip")
        
        return trip
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trip = self.get_object()
        context['trip'] = trip
        
        # Add user role information
        context['user_role'] = self.request.user.get_user_type_display()
        context['is_driver'] = trip.driver == self.request.user
        context['is_management'] = self.request.user.user_type in ['admin', 'manager', 'vehicle_manager']
        
        return context
    
    def form_valid(self, form):
        trip = form.instance
        end_odometer = form.cleaned_data.get('end_odometer')
        
        # Validate end_odometer
        if not end_odometer or end_odometer <= trip.start_odometer:
            messages.error(
                self.request, 
                f'End odometer ({end_odometer}) must be greater than start odometer ({trip.start_odometer}).'
            )
            return self.form_invalid(form)
        
        try:
            # Use the model's end_trip method
            trip.end_trip(end_odometer=end_odometer, notes=form.cleaned_data.get('notes'))
            
            # Success message with role indication
            user_role = self.request.user.get_user_type_display()
            ended_by = "you" if trip.driver == self.request.user else f"{user_role}"
            
            messages.success(
                self.request, 
                f'Trip ended successfully by {ended_by}! Distance: {trip.distance_traveled()} km'
            )
            
        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, f'Error ending trip: {str(e)}')
            return self.form_invalid(form)
        
        return redirect('trip_detail', pk=trip.pk)
    
    def form_invalid(self, form):
        # Add form errors to messages
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field}: {error}")
        
        return super().form_invalid(form)