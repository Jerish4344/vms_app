from django.contrib import admin
from .models import Trip

@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    """Admin configuration for Trip model."""
    
    list_display = ('id', 'vehicle', 'driver', 'get_route_summary', 'start_time', 'end_time', 'status', 'distance_traveled')
    list_filter = ('status', 'vehicle', 'driver', 'start_time')
    search_fields = ('vehicle__license_plate', 'driver__username', 'purpose', 'origin', 'destination')
    readonly_fields = ('distance_traveled', 'duration', 'get_route_summary')
    
    fieldsets = (
        ('Trip Details', {
            'fields': ('vehicle', 'driver', 'start_time', 'end_time', 'status')
        }),
        ('Route Information', {
            'fields': ('origin', 'destination', 'get_route_summary')
        }),
        ('Odometer Readings', {
            'fields': ('start_odometer', 'end_odometer', 'distance_traveled')
        }),
        ('Additional Information', {
            'fields': ('purpose', 'notes', 'duration'),
        }),
    )
    
    def get_route_summary(self, obj):
        """Display route summary in admin."""
        return obj.get_route_summary()
    get_route_summary.short_description = 'Route'
    
    def distance_traveled(self, obj):
        """Calculate the distance traveled."""
        if obj.end_odometer and obj.start_odometer:
            return f"{obj.end_odometer - obj.start_odometer} km"
        return "In progress"
    
    def duration(self, obj):
        """Calculate the trip duration."""
        if obj.end_time and obj.start_time:
            duration = obj.end_time - obj.start_time
            hours = duration.seconds // 3600
            minutes = (duration.seconds % 3600) // 60
            return f"{hours}h {minutes}m"
        return "In progress"