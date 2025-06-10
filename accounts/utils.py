import requests
import logging
from django.conf import settings
from datetime import datetime, timedelta
from django.core.cache import cache

logger = logging.getLogger(__name__)

class StyleHRAPIClient:
    """
    Utility class for StyleHR API interactions
    """
    
    def __init__(self):
        self.api_url = getattr(settings, 'STYLEHR_API_URL', 'https://stylehr.in/api/login/')
        self.timeout = getattr(settings, 'STYLEHR_API_TIMEOUT', 30)
    
    def authenticate_user(self, username, password):
        """
        Authenticate user with StyleHR API
        """
        try:
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            payload = {
                'email': username,
                'password': password
            }
            
            logger.info(f"Attempting StyleHR authentication for: {username}")
            
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and self._is_valid_response(response_data):
                        logger.info(f"StyleHR authentication successful for: {username}")
                        return response_data
                except ValueError:
                    logger.error(f"Invalid JSON response from StyleHR for: {username}")
            
            # Log the actual response for debugging
            logger.warning(f"StyleHR authentication failed for {username}. Status: {response.status_code}, Response: {response.text[:200]}")
            return None
            
        except requests.RequestException as e:
            logger.error(f"StyleHR API request failed for {username}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during StyleHR authentication for {username}: {str(e)}")
            return None
    
    def _is_valid_response(self, response_data):
        """
        Check if the response contains valid employee data
        """
        # Check for common employee data fields
        required_fields = ['employee_id', 'email']  # Adjust based on actual StyleHR response
        optional_fields = ['first_name', 'last_name', 'role', 'department']
        
        # At least one required field should be present
        has_required = any(field in response_data for field in required_fields)
        
        # Should not be an error message
        is_not_error = 'Invalid username/password' not in str(response_data)
        
        return has_required and is_not_error
    
    def validate_driver_role(self, hr_user_data):
        """
        Validate if user has driver role in HR system
        """
        # Extract role-related information
        role_fields = [
            hr_user_data.get('role', ''),
            hr_user_data.get('department', ''),
            hr_user_data.get('job_title', ''),
            hr_user_data.get('designation', ''),
            hr_user_data.get('position', '')
        ]
        
        # Combine all role information
        role_text = ' '.join(str(field).lower() for field in role_fields)
        
        # Driver keywords - customize based on your organization
        driver_keywords = [
            'driver', 'chauffeur', 'vehicle_operator', 'company_driver',
            'fleet_driver', 'transport', 'logistics_driver', 'delivery_driver'
        ]
        
        is_driver = any(keyword in role_text for keyword in driver_keywords)
        
        if not is_driver:
            logger.info(f"Role validation failed. Role text: {role_text}")
        
        return is_driver


def sync_user_with_hr_data(user, hr_data):
    """
    Utility function to sync user data with HR system data
    """
    try:
        updated_fields = []
        
        # Map HR fields to User model fields
        field_mappings = {
            'first_name': hr_data.get('first_name', ''),
            'last_name': hr_data.get('last_name', ''),
            'email': hr_data.get('email', ''),
            'phone_number': hr_data.get('phone', '') or hr_data.get('mobile', ''),
            'address': hr_data.get('address', '') or hr_data.get('current_address', ''),
            'license_number': hr_data.get('license_number', '') or hr_data.get('driving_license', ''),
        }
        
        # Update fields if they have changed
        for field, value in field_mappings.items():
            if value and getattr(user, field) != value:
                setattr(user, field, value)
                updated_fields.append(field)
        
        # Handle license expiry date
        license_expiry = hr_data.get('license_expiry', '') or hr_data.get('license_expiry_date', '')
        if license_expiry:
            try:
                # Try multiple date formats
                for date_format in ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y']:
                    try:
                        parsed_date = datetime.strptime(str(license_expiry), date_format).date()
                        if user.license_expiry != parsed_date:
                            user.license_expiry = parsed_date
                            updated_fields.append('license_expiry')
                        break
                    except ValueError:
                        continue
            except Exception as e:
                logger.warning(f"Could not parse license expiry date: {license_expiry}")
        
        # Save if any fields were updated
        if updated_fields:
            user.save()
            logger.info(f"Updated user {user.username} fields: {updated_fields}")
        
        return updated_fields
        
    except Exception as e:
        logger.error(f"Error syncing user {user.username} with HR data: {str(e)}")
        return []


def get_hr_user_info(username, use_cache=True):
    """
    Get user information from HR system with caching
    """
    cache_key = f"hr_user_info_{username}"
    
    if use_cache:
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
    
    # This would require a separate API endpoint to get user info
    # For now, we'll return None as StyleHR only provides login endpoint
    return None


def check_hr_system_health():
    """
    Check if StyleHR system is accessible
    """
    try:
        response = requests.get('https://stylehr.in', timeout=10)
        return response.status_code == 200
    except:
        return False