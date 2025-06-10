from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)
def handle_driver_creation(sender, instance, created, **kwargs):
    """Handle new driver account creation"""
    if created and instance.user_type == 'driver':
        logger.info(f"New driver account created: {instance.username} - Status: {instance.approval_status}")
        
        # Send notification to managers (optional)
        if getattr(settings, 'DRIVER_APPROVAL_NOTIFICATIONS', False):
            notify_managers_new_driver(instance)

@receiver(pre_save, sender=User)
def track_approval_changes(sender, instance, **kwargs):
    """Track approval status changes"""
    if instance.pk:  # Only for existing users
        try:
            old_instance = User.objects.get(pk=instance.pk)
            if (old_instance.approval_status != instance.approval_status and 
                instance.user_type == 'driver'):
                
                logger.info(f"Approval status changed for {instance.username}: "
                           f"{old_instance.approval_status} → {instance.approval_status}")
                
                # Send notification to driver (optional)
                if getattr(settings, 'DRIVER_APPROVAL_NOTIFICATIONS', False):
                    notify_driver_status_change(instance, old_instance.approval_status)
                    
        except User.DoesNotExist:
            pass

def notify_managers_new_driver(driver):
    """Send notification to managers about new driver"""
    managers = User.objects.filter(
        user_type__in=['admin', 'manager', 'vehicle_manager'],
        is_active=True,
        email__isnull=False
    ).exclude(email='')
    
    if managers.exists():
        subject = f'New Driver Approval Required: {driver.get_full_name()}'
        message = f'''
        A new driver has registered and requires approval:
        
        Name: {driver.get_full_name()}
        Employee ID: {driver.hr_employee_id}
        Email: {driver.email}
        Phone: {driver.phone_number}
        
        Please review and approve/reject this driver in the admin panel.
        '''
        
        manager_emails = [m.email for m in managers]
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                manager_emails,
                fail_silently=True
            )
        except Exception as e:
            logger.error(f"Failed to send manager notification: {e}")

def notify_driver_status_change(driver, old_status):
    """Send notification to driver about status change"""
    if not driver.email:
        return
    
    if driver.approval_status == 'approved':
        subject = 'VMS Access Approved'
        message = f'''
        Dear {driver.get_full_name()},
        
        Your access to the Vehicle Management System has been approved!
        You can now log in and access all driver features.
        
        Login at: [Your VMS URL]
        
        Best regards,
        VMS Team
        '''
    elif driver.approval_status == 'rejected':
        subject = 'VMS Access Request Update'
        message = f'''
        Dear {driver.get_full_name()},
        
        Your access request to the Vehicle Management System has been reviewed.
        
        Status: Not Approved
        {f"Reason: {driver.rejection_reason}" if driver.rejection_reason else ""}
        
        Please contact your manager for more information.
        
        Best regards,
        VMS Team
        '''
    else:
        return
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [driver.email],
            fail_silently=True
        )
    except Exception as e:
        logger.error(f"Failed to send driver notification to {driver.email}: {e}")