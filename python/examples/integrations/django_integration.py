"""
Django Integration Example for VibeCoding Logger

This example shows how to integrate VibeCoding Logger with Django applications
for enhanced logging and AI-driven debugging.
"""

# settings.py configuration
VIBE_LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'vibe_json': {
            '()': 'vibelogger.formatters.VibeJSONFormatter',
            'include_extra': True,
            'include_env': False,
        },
    },
    'handlers': {
        'vibe_file': {
            'level': 'INFO',
            'class': 'vibelogger.handlers.VibeLoggingHandler',
            'vibe_logger': None,  # Will be set up in Django app ready()
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'vibe_json',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['vibe_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['vibe_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'myapp': {  # Replace with your app name
            'handlers': ['vibe_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}

# apps.py - Django App Configuration
from django.apps import AppConfig
from django.conf import settings
import logging.config

class MyAppConfig(AppConfig):
    name = 'myapp'  # Replace with your app name
    
    def ready(self):
        # Set up VibeCoding Logger integration
        from vibelogger import create_file_logger
        from vibelogger.handlers import VibeLoggingHandler
        
        # Create VibeCoding Logger
        vibe_logger = create_file_logger('django_app')
        
        # Update the handler with the actual logger instance
        logging_config = settings.VIBE_LOGGING_CONFIG.copy()
        logging_config['handlers']['vibe_file']['vibe_logger'] = vibe_logger
        
        # Configure logging
        logging.config.dictConfig(logging_config)


# views.py - Enhanced Django Views with VibeCoding
from django.http import JsonResponse
from django.views import View
from vibelogger.handlers import VibeLoggerAdapter
import logging

# Get enhanced logger
logger = VibeLoggerAdapter(logging.getLogger(__name__), {})

class UserView(View):
    def get(self, request, user_id):
        """Get user profile with enhanced logging."""
        
        logger.vibe_info(
            operation="fetch_user_profile",
            message=f"Fetching profile for user {user_id}",
            context={
                'user_id': user_id,
                'request_ip': request.META.get('REMOTE_ADDR'),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:100],
            },
            human_note="Track user profile access patterns"
        )
        
        try:
            # Simulate user lookup
            user_data = self._get_user_data(user_id)
            
            logger.vibe_info(
                operation="fetch_user_profile",
                message="User profile retrieved successfully",
                context={
                    'user_id': user_id,
                    'profile_fields': list(user_data.keys())
                }
            )
            
            return JsonResponse(user_data)
            
        except ValueError as e:
            logger.vibe_exception(
                operation="fetch_user_profile",
                message="Invalid user ID provided",
                context={
                    'user_id': user_id,
                    'error_type': 'validation_error'
                },
                ai_todo="Analyze user ID validation patterns and suggest improvements"
            )
            return JsonResponse({'error': 'Invalid user ID'}, status=400)
            
        except Exception as e:
            logger.vibe_exception(
                operation="fetch_user_profile", 
                message="Unexpected error fetching user profile",
                context={
                    'user_id': user_id,
                    'error_details': str(e)
                },
                ai_todo="Investigate root cause of unexpected user profile errors"
            )
            return JsonResponse({'error': 'Internal server error'}, status=500)
    
    def _get_user_data(self, user_id):
        """Simulate user data retrieval."""
        if user_id == "invalid":
            raise ValueError("Invalid user ID format")
        if user_id == "999":
            raise Exception("Database connection error")
        
        return {
            'id': user_id,
            'name': f'User {user_id}',
            'email': f'user{user_id}@example.com'
        }


# middleware.py - Custom Middleware with VibeCoding Logging
from django.utils.deprecation import MiddlewareMixin
from vibelogger.formatters import create_structured_logger
import time
import uuid

class VibeLoggingMiddleware(MiddlewareMixin):
    """Middleware to add VibeCoding context to all requests."""
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.logger = create_structured_logger('django_middleware')
    
    def process_request(self, request):
        """Add correlation ID and start request logging."""
        # Generate correlation ID for request tracking
        request.correlation_id = str(uuid.uuid4())
        request.start_time = time.time()
        
        self.logger.add_context(
            correlation_id=request.correlation_id,
            path=request.path,
            method=request.method,
            user_id=getattr(request.user, 'id', None) if hasattr(request, 'user') else None
        )
        
        with self.logger.operation_context("http_request"):
            self.logger.info(
                f"Started {request.method} {request.path}",
                request_headers=dict(request.headers),
                query_params=dict(request.GET)
            )
    
    def process_response(self, request, response):
        """Log request completion."""
        if hasattr(request, 'start_time'):
            duration = (time.time() - request.start_time) * 1000
            
            self.logger.performance(
                "http_request",
                duration_ms=duration,
                status_code=response.status_code,
                response_size=len(response.content) if hasattr(response, 'content') else 0
            )
        
        return response


# models.py - Enhanced Model Operations
from django.db import models
from vibelogger.handlers import setup_vibe_logging
from vibelogger import create_file_logger

# Set up model-specific logging
vibe_logger = create_file_logger('django_models')
model_logger = setup_vibe_logging(vibe_logger, 'myapp.models')

class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        """Enhanced save with logging."""
        is_new = self.pk is None
        
        model_logger.vibe_info(
            operation="user_save",
            message=f"{'Creating' if is_new else 'Updating'} user",
            context={
                'user_id': self.pk,
                'is_new': is_new,
                'fields_changed': self._get_changed_fields() if not is_new else None
            },
            human_note="Track user data changes for audit purposes"
        )
        
        try:
            result = super().save(*args, **kwargs)
            
            model_logger.vibe_info(
                operation="user_save",
                message=f"User {'created' if is_new else 'updated'} successfully",
                context={'user_id': self.pk}
            )
            
            return result
            
        except Exception as e:
            model_logger.vibe_exception(
                operation="user_save",
                message="Failed to save user",
                context={
                    'user_data': {
                        'name': self.name,
                        'email': self.email
                    }
                },
                ai_todo="Analyze user save failures and suggest data validation improvements"
            )
            raise
    
    def _get_changed_fields(self):
        """Get list of changed fields."""
        if not self.pk:
            return None
        
        try:
            original = User.objects.get(pk=self.pk)
            changed = []
            for field in self._meta.fields:
                if getattr(original, field.name) != getattr(self, field.name):
                    changed.append(field.name)
            return changed
        except User.DoesNotExist:
            return None


# Usage in Django shell or management commands
if __name__ == "__main__":
    # Example of using VibeCoding Logger in Django management commands
    from django.core.management.base import BaseCommand
    
    class Command(BaseCommand):
        help = 'Example management command with VibeCoding logging'
        
        def __init__(self):
            super().__init__()
            from vibelogger import create_file_logger
            from vibelogger.formatters import create_structured_logger
            
            vibe_logger = create_file_logger('django_command')
            self.logger = create_structured_logger('management_command', vibe_logger)
        
        def handle(self, *args, **options):
            with self.logger.operation_context("data_migration"):
                self.logger.info("Starting data migration")
                
                try:
                    # Perform migration tasks
                    self._migrate_users()
                    self.logger.success("Data migration completed")
                    
                except Exception as e:
                    self.logger.failure(
                        "Data migration failed",
                        ai_todo="Analyze migration failure and suggest recovery steps"
                    )
                    raise
        
        def _migrate_users(self):
            """Example migration logic."""
            users = User.objects.all()
            self.logger.info(f"Processing {users.count()} users")
            
            for user in users:
                self.logger.debug(
                    f"Processing user {user.id}",
                    user_email=user.email
                )