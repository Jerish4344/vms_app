from django.db import models
from django.utils import timezone
from vehicles.models import Vehicle
from django.conf import settings
from django.core.exceptions import ValidationError

class Trip(models.Model):
    """Record of a vehicle trip."""
    
    STATUS_CHOICES = (
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    vehicle = models.ForeignKey(
        Vehicle, 
        on_delete=models.CASCADE,
        related_name='trips'
    )
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='trips'
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    start_odometer = models.PositiveIntegerField(help_text="Odometer reading at trip start in km")
    end_odometer = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        help_text="Odometer reading at trip end in km"
    )
    
    # NEW DESTINATION FIELDS
    origin = models.CharField(
        max_length=255,
        help_text="Starting location/address"
    )
    destination = models.CharField(
        max_length=255,
        help_text="Destination location/address"
    )
    
    purpose = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ongoing'
    )
    
    class Meta:
        ordering = ['-start_time']
    
    def __str__(self):
        return f"{self.vehicle} driven by {self.driver.get_full_name()} from {self.origin} to {self.destination} on {self.start_time.date()}"
    
    def clean(self):
        """Validate trip data."""
        super().clean()
        
        # Validate end_odometer if provided
        if self.end_odometer is not None:
            if self.end_odometer <= self.start_odometer:
                raise ValidationError({
                    'end_odometer': f'End odometer ({self.end_odometer}) must be greater than start odometer ({self.start_odometer})'
                })
    
    def save(self, *args, **kwargs):
        """
        Override save to update related vehicle status and odometer.
        """
        # Store the original status to detect changes
        original_status = None
        if self.pk:
            try:
                original_trip = Trip.objects.get(pk=self.pk)
                original_status = original_trip.status
            except Trip.DoesNotExist:
                pass
        
        # For a new trip (starting)
        if not self.pk:
            # If starting a new trip, update vehicle status to in_use
            if self.status == 'ongoing':
                self.vehicle.status = 'in_use'
                # Ensure vehicle's current_odometer is not None before saving
                if self.vehicle.current_odometer is None:
                    self.vehicle.current_odometer = self.start_odometer
                self.vehicle.save()
        else:
            # For existing trip - check if status changed to completed or cancelled
            if (original_status == 'ongoing' and 
                self.status in ['completed', 'cancelled']):
                
                # Update vehicle status back to available
                self.vehicle.status = 'available'
                
                # Update vehicle odometer if completed with valid end_odometer
                if self.status == 'completed' and self.end_odometer:
                    # CRITICAL FIX: Ensure we never set current_odometer to None
                    if self.end_odometer > 0:
                        self.vehicle.current_odometer = self.end_odometer
                    else:
                        # Fallback: use start_odometer if end_odometer is invalid
                        self.vehicle.current_odometer = self.start_odometer
                elif self.status == 'cancelled':
                    # For cancelled trips, keep the original odometer or use start_odometer
                    if self.vehicle.current_odometer is None:
                        self.vehicle.current_odometer = self.start_odometer
                
                # Ensure current_odometer is never None before saving vehicle
                if self.vehicle.current_odometer is None:
                    self.vehicle.current_odometer = self.start_odometer
                
                self.vehicle.save()
        
        # Set end_time when trip is completed
        if self.status == 'completed' and not self.end_time:
            self.end_time = timezone.now()
        
        super().save(*args, **kwargs)
    
    def distance_traveled(self):
        """Calculate distance traveled during the trip."""
        if self.end_odometer is not None and self.start_odometer is not None:
            return max(0, self.end_odometer - self.start_odometer)
        return 0
    
    def get_duration_timedelta(self):
        """Calculate trip duration as a timedelta object."""
        if self.end_time and self.start_time:
            return self.end_time - self.start_time
        elif self.start_time and self.status == 'ongoing':
            # For ongoing trips, calculate duration from start_time to now
            return timezone.now() - self.start_time
        return None
    
    def duration(self):
        """Return trip duration as a formatted string 'Xh Ym' or 'Ym' or 'Xs'."""
        delta = self.get_duration_timedelta()
        if delta:
            total_seconds = int(delta.total_seconds())
            days = total_seconds // (24 * 3600)
            hours = (total_seconds // 3600) % 24
            minutes = (total_seconds // 60) % 60
            seconds = total_seconds % 60

            parts = []
            if days > 0:
                parts.append(f"{days}d")
            if hours > 0:
                parts.append(f"{hours}h")
            if minutes > 0:
                parts.append(f"{minutes}m")
            if not parts and seconds > 0:
                parts.append(f"{seconds}s")
            
            if not parts and total_seconds == 0:
                return "0m"
            
            return " ".join(parts) if parts else None
        return None
    
    def is_active(self):
        """Check if trip is currently active."""
        return self.status == 'ongoing'
    
    def can_be_ended_by(self, user):
        """Check if user can end this trip."""
        # Only the driver or admin/manager can end the trip
        return (
            user == self.driver or 
            hasattr(user, 'user_type') and user.user_type in ['admin', 'manager', 'vehicle_manager']
        )
    
    def get_route_summary(self):
        """Get a formatted route summary."""
        return f"{self.origin} → {self.destination}"
    
    def end_trip(self, end_odometer, notes=None):
        """
        Safely end a trip with proper validation.
        """
        if self.status != 'ongoing':
            raise ValidationError("Can only end ongoing trips")
        
        if not end_odometer or end_odometer <= self.start_odometer:
            raise ValidationError(f"End odometer ({end_odometer}) must be greater than start odometer ({self.start_odometer})")
        
        self.end_odometer = end_odometer
        self.end_time = timezone.now()
        self.status = 'completed'
        
        if notes:
            self.notes = notes
        
        # The save method will handle vehicle updates
        self.save()
    
    def cancel_trip(self, reason=None):
        """
        Cancel an ongoing trip.
        """
        if self.status != 'ongoing':
            raise ValidationError("Can only cancel ongoing trips")
        
        self.status = 'cancelled'
        self.end_time = timezone.now()
        
        if reason:
            self.notes = f"Trip cancelled: {reason}" + (f"\n{self.notes}" if self.notes else "")
        
        # The save method will handle vehicle status update
        self.save()