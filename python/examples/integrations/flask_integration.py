"""
Flask Integration Example for VibeCoding Logger

This example shows how to integrate VibeCoding Logger with Flask applications
for enhanced web application logging and debugging.
"""

from flask import Flask, request, jsonify, g
from werkzeug.exceptions import HTTPException
from functools import wraps
import time
import uuid
import logging

from vibelogger import create_file_logger
from vibelogger.handlers import setup_vibe_logging
from vibelogger.formatters import create_structured_logger

# Initialize VibeCoding Logger
vibe_logger = create_file_logger("flask_app")
app_logger = setup_vibe_logging(vibe_logger, "flask_app")

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Global structured logger
struct_logger = create_structured_logger("flask_app", vibe_logger)


# Request context setup
@app.before_request
def before_request():
    """Set up request context with VibeCoding logging."""
    
    # Generate correlation ID
    g.correlation_id = str(uuid.uuid4())
    g.start_time = time.time()
    
    # Add request context
    struct_logger.add_context(
        correlation_id=g.correlation_id,
        path=request.path,
        method=request.method,
        remote_addr=request.remote_addr,
        user_agent=request.headers.get('User-Agent', '')[:100]
    )
    
    # Log request start
    struct_logger.info(
        f"Started {request.method} {request.path}",
        query_params=dict(request.args),
        content_type=request.content_type,
        content_length=request.content_length
    )


@app.after_request
def after_request(response):
    """Log request completion."""
    
    if hasattr(g, 'start_time'):
        duration = (time.time() - g.start_time) * 1000
        
        struct_logger.performance(
            "http_request",
            duration_ms=duration,
            status_code=response.status_code,
            response_size=response.content_length or 0
        )
    
    return response


# Decorator for operation logging
def log_operation(operation_name):
    """Decorator to log operation context."""
    
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            with struct_logger.operation_context(operation_name):
                return f(*args, **kwargs)
        return wrapper
    return decorator


# Error handlers with VibeCoding logging
@app.errorhandler(HTTPException)
def handle_http_exception(e):
    """Handle HTTP exceptions with logging."""
    
    struct_logger.warning(
        f"HTTP {e.code}: {e.description}",
        status_code=e.code,
        description=e.description,
        correlation_id=getattr(g, 'correlation_id', None)
    )
    
    return jsonify({
        'error': e.description,
        'status_code': e.code,
        'correlation_id': getattr(g, 'correlation_id', None)
    }), e.code


@app.errorhandler(Exception)
def handle_exception(e):
    """Handle unexpected exceptions with logging."""
    
    struct_logger.error(
        f"Unhandled exception: {str(e)}",
        exception_type=type(e).__name__,
        correlation_id=getattr(g, 'correlation_id', None),
        ai_todo="Investigate unhandled exception and add proper error handling"
    )
    
    return jsonify({
        'error': 'Internal server error',
        'correlation_id': getattr(g, 'correlation_id', None)
    }), 500


# API Routes
@app.route('/health')
@log_operation("health_check")
def health_check():
    """Health check endpoint with logging."""
    
    struct_logger.info("Health check requested")
    
    # Simulate health checks
    services_status = {
        "database": "healthy",
        "cache": "healthy", 
        "external_api": "healthy"
    }
    
    struct_logger.success(
        "Health check completed",
        services_status=services_status
    )
    
    return jsonify({
        "status": "healthy",
        "services": services_status,
        "correlation_id": g.correlation_id
    })


@app.route('/users/<user_id>')
@log_operation("fetch_user")
def get_user(user_id):
    """Get user by ID with enhanced logging."""
    
    struct_logger.info(
        f"Fetching user profile for ID: {user_id}",
        user_id=user_id
    )
    
    try:
        # Simulate user lookup
        user_data = _get_user_from_db(user_id)
        
        struct_logger.success(
            "User profile retrieved successfully",
            user_id=user_id,
            profile_fields=list(user_data.keys())
        )
        
        return jsonify({
            **user_data,
            "correlation_id": g.correlation_id
        })
        
    except ValueError as e:
        struct_logger.failure(
            f"Invalid user ID: {user_id}",
            user_id=user_id,
            error_type="validation_error",
            ai_todo="Analyze user ID validation patterns"
        )
        return jsonify({
            "error": "Invalid user ID",
            "correlation_id": g.correlation_id
        }), 400
        
    except Exception as e:
        struct_logger.failure(
            f"Unexpected error fetching user: {str(e)}",
            user_id=user_id,
            error_details=str(e),
            ai_todo="Investigate root cause of user fetch failures"
        )
        return jsonify({
            "error": "Internal server error",
            "correlation_id": g.correlation_id
        }), 500


@app.route('/users', methods=['POST'])
@log_operation("create_user")
def create_user():
    """Create new user with comprehensive logging."""
    
    user_data = request.get_json()
    
    struct_logger.info(
        "Creating new user",
        user_email=user_data.get('email'),
        user_name=user_data.get('name')
    )
    
    try:
        # Validate user data
        _validate_user_data(user_data)
        
        # Create user
        created_user = _create_user_in_db(user_data)
        
        struct_logger.success(
            "User created successfully",
            user_id=created_user["id"],
            user_email=created_user["email"]
        )
        
        return jsonify({
            **created_user,
            "correlation_id": g.correlation_id
        }), 201
        
    except ValueError as e:
        struct_logger.failure(
            f"User validation failed: {str(e)}",
            user_data=user_data,
            error_type="validation_error",
            ai_todo="Analyze user validation failures and improve validation rules"
        )
        return jsonify({
            "error": str(e),
            "correlation_id": g.correlation_id
        }), 422
        
    except Exception as e:
        struct_logger.failure(
            f"User creation failed: {str(e)}",
            user_data=user_data,
            error_details=str(e),
            ai_todo="Investigate user creation failures and suggest improvements"
        )
        return jsonify({
            "error": "Failed to create user",
            "correlation_id": g.correlation_id
        }), 500


@app.route('/users/<user_id>/profile', methods=['PUT'])
@log_operation("update_user_profile")
def update_user_profile(user_id):
    """Update user profile with change tracking."""
    
    profile_data = request.get_json()
    
    struct_logger.info(
        f"Updating profile for user {user_id}",
        user_id=user_id,
        update_fields=list(profile_data.keys())
    )
    
    try:
        # Get current user data
        current_user = _get_user_from_db(user_id)
        
        # Track changes
        changes = {}
        for key, new_value in profile_data.items():
            if key in current_user and current_user[key] != new_value:
                changes[key] = {
                    "old": current_user[key],
                    "new": new_value
                }
        
        # Update user
        updated_user = _update_user_in_db(user_id, profile_data)
        
        struct_logger.success(
            "User profile updated successfully",
            user_id=user_id,
            changes_made=changes,
            human_note="Track profile changes for audit and security purposes"
        )
        
        return jsonify({
            **updated_user,
            "correlation_id": g.correlation_id
        })
        
    except Exception as e:
        struct_logger.failure(
            f"Profile update failed: {str(e)}",
            user_id=user_id,
            profile_data=profile_data,
            ai_todo="Analyze profile update failures"
        )
        return jsonify({
            "error": "Failed to update profile",
            "correlation_id": g.correlation_id
        }), 500


# Helper functions with logging
def _get_user_from_db(user_id):
    """Simulate database user lookup."""
    
    struct_logger.debug(f"Querying database for user {user_id}")
    
    # Simulate various scenarios
    if user_id == "invalid":
        raise ValueError("Invalid user ID format")
    elif user_id == "999":
        raise Exception("Database connection timeout")
    elif user_id == "404":
        from flask import abort
        abort(404, "User not found")
    
    # Simulate database query timing
    _simulate_db_query(50)  # 50ms query
    
    return {
        "id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com",
        "profile": {
            "bio": f"Bio for user {user_id}",
            "location": "San Francisco, CA"
        }
    }


def _validate_user_data(user_data):
    """Validate user data with logging."""
    
    struct_logger.debug("Validating user data")
    
    if not user_data.get('email'):
        raise ValueError("Email is required")
    
    if "@" not in user_data['email']:
        raise ValueError("Invalid email format")
    
    if not user_data.get('name'):
        raise ValueError("Name is required")
    
    if len(user_data['name']) < 2:
        raise ValueError("Name must be at least 2 characters")
    
    struct_logger.debug("User data validation passed")


def _create_user_in_db(user_data):
    """Simulate user creation in database."""
    
    struct_logger.debug("Creating user in database")
    
    # Simulate database insertion
    _simulate_db_query(100)  # 100ms insert
    
    user_id = str(uuid.uuid4())
    
    struct_logger.debug(f"User created with ID: {user_id}")
    
    return {
        "id": user_id,
        "name": user_data["name"],
        "email": user_data["email"]
    }


def _update_user_in_db(user_id, profile_data):
    """Simulate user profile update in database."""
    
    struct_logger.debug(f"Updating user {user_id} in database")
    
    # Simulate database update
    _simulate_db_query(75)  # 75ms update
    
    # Get current user and merge updates
    current_user = _get_user_from_db(user_id)
    current_user.update(profile_data)
    
    return current_user


def _simulate_db_query(duration_ms):
    """Simulate database query with performance logging."""
    
    start_time = time.time()
    time.sleep(duration_ms / 1000)  # Convert to seconds
    actual_duration = (time.time() - start_time) * 1000
    
    struct_logger.metric("db_query_duration", actual_duration, "ms")


# Flask CLI commands with VibeCoding logging
@app.cli.command()
def init_db():
    """Initialize database with logging."""
    
    with struct_logger.operation_context("database_initialization"):
        struct_logger.info("Starting database initialization")
        
        try:
            # Simulate database setup
            _simulate_db_query(500)  # 500ms setup
            
            struct_logger.success("Database initialized successfully")
            print("Database initialized!")
            
        except Exception as e:
            struct_logger.failure(
                f"Database initialization failed: {str(e)}",
                ai_todo="Investigate database initialization failures"
            )
            print(f"Error: {e}")


@app.cli.command()
def seed_data():
    """Seed database with sample data."""
    
    with struct_logger.operation_context("data_seeding"):
        struct_logger.info("Starting data seeding")
        
        try:
            # Create sample users
            sample_users = [
                {"name": "Alice Smith", "email": "alice@example.com"},
                {"name": "Bob Johnson", "email": "bob@example.com"},
                {"name": "Carol Davis", "email": "carol@example.com"}
            ]
            
            for user_data in sample_users:
                created_user = _create_user_in_db(user_data)
                struct_logger.debug(
                    f"Created sample user: {created_user['name']}",
                    user_id=created_user['id']
                )
            
            struct_logger.success(
                f"Seeded {len(sample_users)} sample users",
                users_created=len(sample_users)
            )
            print(f"Seeded {len(sample_users)} users!")
            
        except Exception as e:
            struct_logger.failure(
                f"Data seeding failed: {str(e)}",
                ai_todo="Investigate data seeding failures"
            )
            print(f"Error: {e}")


# Application factory pattern with logging
def create_app(config_name='default'):
    """Application factory with VibeCoding logging setup."""
    
    app = Flask(__name__)
    
    # Configure VibeCoding logging for different environments
    if config_name == 'production':
        vibe_logger = create_file_logger("flask_prod")
        app.logger.setLevel(logging.INFO)
    elif config_name == 'testing':
        vibe_logger = create_file_logger("flask_test")
        app.logger.setLevel(logging.DEBUG)
    else:
        vibe_logger = create_file_logger("flask_dev")
        app.logger.setLevel(logging.DEBUG)
    
    # Set up enhanced logging
    enhanced_logger = setup_vibe_logging(vibe_logger, f"flask_{config_name}")
    
    enhanced_logger.vibe_info(
        operation="app_creation",
        message=f"Flask app created with config: {config_name}",
        context={"config_name": config_name}
    )
    
    return app


# Run the application
if __name__ == '__main__':
    app_logger.vibe_info(
        operation="server_start",
        message="Starting Flask server with VibeCoding logging",
        context={
            "host": "127.0.0.1",
            "port": 5000,
            "debug": True
        }
    )
    
    app.run(host='127.0.0.1', port=5000, debug=True)