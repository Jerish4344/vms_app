from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

class CustomUserAdmin(UserAdmin):
    """Enhanced admin for approval system"""
    
    list_display = (
        'username', 'email', 'first_name', 'last_name', 
        'user_type', 'approval_status_badge', 'hr_auth_badge', 
        'is_active', 'date_joined'
    )
    
    list_filter = (
        'user_type', 'approval_status', 'is_active', 
        'hr_authenticated_at', 'approved_at'
    )
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'email', 'phone_number', 'address')
        }),
        ('Driver Info', {
            'fields': ('license_number', 'license_expiry', 'profile_picture')
        }),
        ('Approval System', {
            'fields': ('approval_status', 'approved_by', 'approved_at', 'rejection_reason'),
            'classes': ('collapse',)
        }),
        ('HR Integration', {
            'fields': ('hr_employee_id', 'hr_authenticated_at', 'hr_data'),
            'classes': ('collapse',)
        }),
        ('Permissions', {
            'fields': ('user_type', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    readonly_fields = ('approved_at', 'hr_authenticated_at')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'hr_employee_id')
    
    def approval_status_badge(self, obj):
        """Display approval status as colored badge"""
        if obj.user_type != 'driver':
            return format_html('<span class="badge bg-secondary">N/A</span>')
        
        colors = {
            'pending': 'warning',
            'approved': 'success', 
            'rejected': 'danger'
        }
        color = colors.get(obj.approval_status, 'secondary')
        
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_approval_status_display()
        )
    approval_status_badge.short_description = 'Approval Status'
    
    def hr_auth_badge(self, obj):
        """Display HR authentication status"""
        if obj.hr_authenticated_at:
            return format_html(
                '<span class="badge bg-info" title="{}">HR Auth</span>',
                obj.hr_authenticated_at.strftime('%Y-%m-%d %H:%M')
            )
        return format_html('<span class="badge bg-secondary">Local</span>')
    hr_auth_badge.short_description = 'Auth Type'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('approved_by')

admin.site.register(CustomUser, CustomUserAdmin)