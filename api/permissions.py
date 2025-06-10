from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to edit objects.
    Others can only read.
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to any authenticated request
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Write permissions are only allowed to admin users
        return request.user and (request.user.is_staff or 
                                request.user.user_type in ['admin', 'manager', 'vehicle_manager'])

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or admins to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated request
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Write permissions are only allowed to the owner or admin
        if hasattr(obj, 'driver') and obj.driver == request.user:
            return True
        
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
            
        return request.user.is_staff or request.user.user_type in ['admin', 'manager', 'vehicle_manager']

class IsDriverOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow drivers or admins to access.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        # Allow if user is a driver or admin/manager
        return (hasattr(request.user, 'user_type') and 
                (request.user.user_type == 'driver' or 
                 request.user.user_type in ['admin', 'manager', 'vehicle_manager'] or
                 request.user.is_staff))

class IsVehicleAssignedToUser(permissions.BasePermission):
    """
    Custom permission to only allow access to vehicles assigned to the user.
    """
    def has_object_permission(self, request, view, obj):
        # Admin/managers can access any vehicle
        if request.user.is_staff or request.user.user_type in ['admin', 'manager', 'vehicle_manager']:
            return True
            
        # For vehicles, check if user is assigned
        if hasattr(obj, 'assigned_driver'):
            return obj.assigned_driver == request.user.get_full_name()
            
        # For trips, check if user is the driver
        if hasattr(obj, 'driver'):
            return obj.driver == request.user
            
        # For maintenance, check if user is assigned to the vehicle
        if hasattr(obj, 'vehicle') and hasattr(obj.vehicle, 'assigned_driver'):
            return obj.vehicle.assigned_driver == request.user.get_full_name()
            
        return False

class IsManagerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow managers or admins to access.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        # Allow if user is an admin or manager
        return (request.user.is_staff or 
                (hasattr(request.user, 'user_type') and 
                 request.user.user_type in ['admin', 'manager', 'vehicle_manager']))

class IsActiveUser(permissions.BasePermission):
    """
    Custom permission to only allow active users to access the API.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_active

class CanStartTrip(permissions.BasePermission):
    """
    Custom permission to only allow users who can start trips.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        # Only POST requests (creating trips) need special permission
        if request.method != 'POST':
            return True
            
        # Admins and managers can always start trips
        if request.user.is_staff or request.user.user_type in ['admin', 'manager', 'vehicle_manager']:
            return True
            
        # Drivers can start trips
        if hasattr(request.user, 'user_type') and request.user.user_type == 'driver':
            return True
            
        return False
