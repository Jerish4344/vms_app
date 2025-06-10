from django import forms
from django.utils import timezone
from .models import Trip
from vehicles.models import Vehicle

class TripForm(forms.ModelForm):
    """Form for creating a new trip."""
    
    class Meta:
        model = Trip
        fields = ['vehicle', 'origin', 'destination', 'start_odometer', 'purpose', 'notes']
        widgets = {
            'origin': forms.TextInput(attrs={
                'placeholder': 'e.g., Main Office, 123 Business St, City',
                'class': 'form-control'
            }),
            'destination': forms.TextInput(attrs={
                'placeholder': 'e.g., Client Office, Airport, Warehouse',
                'class': 'form-control'
            }),
            'purpose': forms.TextInput(attrs={
                'placeholder': 'e.g., Client Meeting, Delivery, etc.',
                'class': 'form-control'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3, 
                'placeholder': 'Additional trip details...',
                'class': 'form-control'
            }),
            'start_odometer': forms.NumberInput(attrs={
                'min': 0,
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Only show available vehicles
        self.fields['vehicle'].queryset = Vehicle.objects.filter(status='available')
        
        # Add custom help text
        self.fields['start_odometer'].help_text = "Current odometer reading in kilometers"
        self.fields['origin'].help_text = "Starting point of your trip"
        self.fields['destination'].help_text = "Where you're going"
        
        # Make sure origin and destination are required
        self.fields['origin'].required = True
        self.fields['destination'].required = True
        
        # Make start_time a hidden field with current time
        self.fields['start_time'] = forms.DateTimeField(
            widget=forms.HiddenInput(),
            initial=timezone.now()
        )
    
    def clean_start_odometer(self):
        """Validate start odometer is not less than vehicle's current odometer."""
        start_odometer = self.cleaned_data.get('start_odometer')
        vehicle = self.cleaned_data.get('vehicle')
        
        if vehicle and start_odometer < vehicle.current_odometer:
            raise forms.ValidationError(
                f"Start odometer cannot be less than vehicle's current odometer ({vehicle.current_odometer} km)."
            )
        
        return start_odometer
    
    def clean_origin(self):
        """Validate origin field."""
        origin = self.cleaned_data.get('origin')
        if not origin or len(origin.strip()) < 3:
            raise forms.ValidationError("Please provide a valid starting location (minimum 3 characters).")
        return origin.strip()
    
    def clean_destination(self):
        """Validate destination field."""
        destination = self.cleaned_data.get('destination')
        if not destination or len(destination.strip()) < 3:
            raise forms.ValidationError("Please provide a valid destination (minimum 3 characters).")
        return destination.strip()
    
    def clean(self):
        """Cross-field validation."""
        cleaned_data = super().clean()
        origin = cleaned_data.get('origin')
        destination = cleaned_data.get('destination')
        
        if origin and destination and origin.lower().strip() == destination.lower().strip():
            raise forms.ValidationError("Origin and destination cannot be the same.")
        
        return cleaned_data

class EndTripForm(forms.ModelForm):
    """Form for ending a trip."""
    
    class Meta:
        model = Trip
        fields = ['end_odometer', 'notes']
        widgets = {
            'end_odometer': forms.NumberInput(attrs={
                'min': 0,
                'class': 'form-control'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3, 
                'placeholder': 'Additional trip details or final remarks...',
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add custom help text
        self.fields['end_odometer'].help_text = "Current odometer reading in kilometers"
        
        # Set minimum value for end_odometer
        if self.instance and self.instance.start_odometer:
            self.fields['end_odometer'].widget.attrs['min'] = self.instance.start_odometer
    
    def clean_end_odometer(self):
        """Validate end odometer is greater than start odometer."""
        end_odometer = self.cleaned_data.get('end_odometer')
        
        if self.instance and self.instance.start_odometer:
            if end_odometer < self.instance.start_odometer:
                raise forms.ValidationError(
                    f"End odometer cannot be less than start odometer ({self.instance.start_odometer} km)."
                )
        
        return end_odometer