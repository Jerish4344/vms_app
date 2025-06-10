from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework import exceptions
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

# Token expiry duration - default to 7 days if not set in settings
TOKEN_EXPIRY_DAYS = getattr(settings, 'TOKEN_EXPIRY_DAYS', 7)

class ExpiringTokenAuthentication(TokenAuthentication):
    """
    Custom token authentication that supports token expiration.
    """
    keyword = 'Token'  # Authorization header prefix
    
    def authenticate_credentials(self, key):
        """
        Authenticate token credentials with expiry check.
        """
        try:
            token = Token.objects.get(key=key)
        except ObjectDoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid token')

        # Check if token has expired
        if self._token_expired(token):
            token.delete()
            raise exceptions.AuthenticationFailed('Token has expired')

        if not token.user.is_active:
            raise exceptions.AuthenticationFailed('User inactive or deleted')

        # Update the token's last_used timestamp
        self._update_token_last_used(token)
        
        return (token.user, token)
    
    def _token_expired(self, token):
        """
        Check if a token has expired based on its creation time.
        """
        # If token has a created attribute, use it
        if hasattr(token, 'created'):
            expiry_date = token.created + timedelta(days=TOKEN_EXPIRY_DAYS)
            return expiry_date < timezone.now()
        
        # If we can't determine expiry, assume it's valid
        return False
    
    def _update_token_last_used(self, token):
        """
        Update the token's last used timestamp if the field exists.
        """
        if hasattr(token, 'last_used'):
            token.last_used = timezone.now()
            token.save(update_fields=['last_used'])


def get_token_for_user(user):
    """
    Get or create a token for a user.
    If the token exists but has expired, delete it and create a new one.
    """
    # Delete any existing expired token
    try:
        token = Token.objects.get(user=user)
        if _is_token_expired(token):
            token.delete()
            token = None
    except Token.DoesNotExist:
        token = None
    
    # Create a new token if needed
    if token is None:
        token = Token.objects.create(user=user)
    
    return token


def _is_token_expired(token):
    """
    Check if a token has expired.
    """
    if hasattr(token, 'created'):
        expiry_date = token.created + timedelta(days=TOKEN_EXPIRY_DAYS)
        return expiry_date < timezone.now()
    return False


def refresh_token(token):
    """
    Refresh an authentication token by deleting the old one and creating a new one.
    """
    user = token.user
    token.delete()
    new_token = Token.objects.create(user=user)
    return new_token


class MobileAppAuthBackend:
    """
    Custom authentication backend for the mobile app.
    This allows authentication with either username or email plus password.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate a user by username or email.
        """
        if not username or not password:
            return None
        
        # Try to authenticate with username
        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            # Try to authenticate with email
            try:
                user = User.objects.get(email=username)
                if user.check_password(password):
                    return user
            except User.DoesNotExist:
                return None
        
        return None
    
    def get_user(self, user_id):
        """
        Get a user by ID.
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


# Helper function to validate user credentials and return a token
def validate_user_and_get_token(username, password):
    """
    Validate user credentials and return a token if valid.
    """
    try:
        # Try username first
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # Try email
            user = User.objects.get(email=username)
        
        # Check password
        if user.check_password(password):
            if not user.is_active:
                return None, "User account is disabled"
            
            # Get or create token
            token = get_token_for_user(user)
            return token, None
        else:
            return None, "Invalid password"
    
    except User.DoesNotExist:
        return None, "User not found"
    except Exception as e:
        logger.error(f"Error validating user credentials: {str(e)}")
        return None, "Authentication error"
