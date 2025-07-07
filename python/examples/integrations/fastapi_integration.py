"""
FastAPI Integration Example for VibeCoding Logger

This example demonstrates how to integrate VibeCoding Logger with FastAPI
applications for enhanced API logging and debugging.
"""

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import time
import uuid
import logging

from vibelogger import create_file_logger
from vibelogger.handlers import setup_vibe_logging, VibeLoggerAdapter
from vibelogger.formatters import create_structured_logger

# Initialize VibeCoding Logger
vibe_logger = create_file_logger("fastapi_app")
api_logger = setup_vibe_logging(vibe_logger, "fastapi_app")

# Create FastAPI app
app = FastAPI(title="VibeCoding FastAPI Example")

# Pydantic models
class UserCreate(BaseModel):
    name: str
    email: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: str

class ErrorResponse(BaseModel):
    error: str
    correlation_id: Optional[str] = None


# Middleware for request logging and correlation tracking
class VibeLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to add VibeCoding context to all requests."""
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = create_structured_logger("fastapi_middleware", vibe_logger)
    
    async def dispatch(self, request: Request, call_next):
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        request.state.start_time = time.time()
        
        # Add correlation context
        self.logger.add_context(
            correlation_id=correlation_id,
            path=request.url.path,
            method=request.method,
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent", "")[:100]
        )
        
        # Log request start
        with self.logger.operation_context("http_request"):
            self.logger.info(
                f"Started {request.method} {request.url.path}",
                query_params=dict(request.query_params),
                headers={k: v for k, v in request.headers.items() 
                        if k.lower() not in ['authorization', 'cookie']}
            )
            
            try:
                # Process request
                response = await call_next(request)
                
                # Log successful response
                duration = (time.time() - request.state.start_time) * 1000
                self.logger.performance(
                    "http_request",
                    duration_ms=duration,
                    status_code=response.status_code,
                    response_size=len(response.body) if hasattr(response, 'body') else 0
                )
                
                return response
                
            except Exception as e:
                # Log request failure
                duration = (time.time() - request.state.start_time) * 1000
                self.logger.failure(
                    f"Request failed: {str(e)}",
                    duration_ms=duration,
                    error_type=type(e).__name__,
                    ai_todo=f"Analyze {request.method} {request.url.path} failures"
                )
                raise

# Add middleware
app.add_middleware(VibeLoggingMiddleware)


# Dependency to get correlation ID
def get_correlation_id(request: Request) -> str:
    """Dependency to extract correlation ID from request."""
    return getattr(request.state, 'correlation_id', str(uuid.uuid4()))


# Dependency to get structured logger for endpoint
def get_endpoint_logger(request: Request) -> 'StructuredLogger':
    """Dependency to get a configured logger for the endpoint."""
    logger = create_structured_logger("fastapi_endpoint", vibe_logger)
    
    # Add request context
    correlation_id = getattr(request.state, 'correlation_id', None)
    if correlation_id:
        logger.add_context(correlation_id=correlation_id)
    
    return logger


# API Endpoints
@app.get("/health")
async def health_check(
    logger: 'StructuredLogger' = Depends(get_endpoint_logger)
):
    """Health check endpoint with logging."""
    
    with logger.operation_context("health_check"):
        logger.info("Health check requested")
        
        # Simulate health checks
        services_status = {
            "database": "healthy",
            "cache": "healthy",
            "external_api": "healthy"
        }
        
        logger.success(
            "Health check completed",
            services_status=services_status
        )
        
        return {"status": "healthy", "services": services_status}


@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    logger: 'StructuredLogger' = Depends(get_endpoint_logger),
    correlation_id: str = Depends(get_correlation_id)
):
    """Get user by ID with enhanced logging."""
    
    with logger.operation_context("fetch_user"):
        logger.info(
            f"Fetching user profile for ID: {user_id}",
            user_id=user_id
        )
        
        try:
            # Simulate user lookup
            user_data = await _get_user_from_db(user_id, logger)
            
            logger.success(
                "User profile retrieved successfully",
                user_id=user_id,
                profile_fields=list(user_data.keys())
            )
            
            return UserResponse(**user_data)
            
        except ValueError as e:
            logger.failure(
                f"Invalid user ID: {user_id}",
                user_id=user_id,
                error_type="validation_error",
                ai_todo="Analyze user ID validation patterns"
            )
            raise HTTPException(
                status_code=400, 
                detail={
                    "error": "Invalid user ID", 
                    "correlation_id": correlation_id
                }
            )
            
        except Exception as e:
            logger.failure(
                f"Unexpected error fetching user: {str(e)}",
                user_id=user_id,
                error_details=str(e),
                ai_todo="Investigate root cause of user fetch failures"
            )
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Internal server error",
                    "correlation_id": correlation_id
                }
            )


@app.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    logger: 'StructuredLogger' = Depends(get_endpoint_logger),
    correlation_id: str = Depends(get_correlation_id)
):
    """Create new user with comprehensive logging."""
    
    with logger.operation_context("create_user"):
        logger.info(
            "Creating new user",
            user_email=user_data.email,
            user_name=user_data.name
        )
        
        try:
            # Validate user data
            await _validate_user_data(user_data, logger)
            
            # Create user
            created_user = await _create_user_in_db(user_data, logger)
            
            logger.success(
                "User created successfully",
                user_id=created_user["id"],
                user_email=created_user["email"]
            )
            
            return UserResponse(**created_user)
            
        except ValueError as e:
            logger.failure(
                f"User validation failed: {str(e)}",
                user_data=user_data.dict(),
                error_type="validation_error",
                ai_todo="Analyze user validation failures and improve validation rules"
            )
            raise HTTPException(
                status_code=422,
                detail={
                    "error": str(e),
                    "correlation_id": correlation_id
                }
            )
            
        except Exception as e:
            logger.failure(
                f"User creation failed: {str(e)}",
                user_data=user_data.dict(),
                error_details=str(e),
                ai_todo="Investigate user creation failures and suggest improvements"
            )
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Failed to create user",
                    "correlation_id": correlation_id
                }
            )


# Helper functions with logging
async def _get_user_from_db(user_id: str, logger) -> Dict[str, Any]:
    """Simulate database user lookup."""
    
    logger.debug(f"Querying database for user {user_id}")
    
    # Simulate various scenarios
    if user_id == "invalid":
        raise ValueError("Invalid user ID format")
    elif user_id == "999":
        raise Exception("Database connection timeout")
    elif user_id == "404":
        raise HTTPException(status_code=404, detail="User not found")
    
    # Simulate database query
    await _simulate_db_query(50, logger)  # 50ms query
    
    return {
        "id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com"
    }


async def _validate_user_data(user_data: UserCreate, logger) -> None:
    """Validate user data with logging."""
    
    logger.debug("Validating user data", user_email=user_data.email)
    
    if "@" not in user_data.email:
        raise ValueError("Invalid email format")
    
    if len(user_data.name) < 2:
        raise ValueError("Name must be at least 2 characters")
    
    # Simulate additional validation
    await _simulate_db_query(10, logger)  # Email uniqueness check
    
    logger.debug("User data validation passed")


async def _create_user_in_db(user_data: UserCreate, logger) -> Dict[str, Any]:
    """Simulate user creation in database."""
    
    logger.debug("Creating user in database")
    
    # Simulate database insertion
    await _simulate_db_query(100, logger)  # 100ms insert
    
    user_id = str(uuid.uuid4())
    
    logger.debug(f"User created with ID: {user_id}")
    
    return {
        "id": user_id,
        "name": user_data.name,
        "email": user_data.email
    }


async def _simulate_db_query(duration_ms: int, logger) -> None:
    """Simulate database query with performance logging."""
    import asyncio
    
    start_time = time.time()
    await asyncio.sleep(duration_ms / 1000)  # Convert to seconds
    actual_duration = (time.time() - start_time) * 1000
    
    logger.metric("db_query_duration", actual_duration, "ms")


# Exception handlers with VibeCoding logging
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with logging."""
    
    correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
    
    api_logger.vibe_warning(
        operation="http_exception",
        message=f"HTTP {exc.status_code}: {exc.detail}",
        context={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path,
            "method": request.method,
            "correlation_id": correlation_id
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "correlation_id": correlation_id
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions with logging."""
    
    correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
    
    api_logger.vibe_exception(
        operation="unhandled_exception",
        message=f"Unhandled exception: {str(exc)}",
        context={
            "exception_type": type(exc).__name__,
            "path": request.url.path,
            "method": request.method,
            "correlation_id": correlation_id
        },
        ai_todo="Investigate unhandled exception and add proper error handling"
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "correlation_id": correlation_id
        }
    )


# Startup and shutdown events with logging
@app.on_event("startup")
async def startup_event():
    """Application startup with logging."""
    
    api_logger.vibe_info(
        operation="app_startup",
        message="FastAPI application starting up",
        context={
            "app_title": app.title,
            "docs_url": "/docs"
        }
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown with logging."""
    
    api_logger.vibe_info(
        operation="app_shutdown",
        message="FastAPI application shutting down"
    )


# Run the application
if __name__ == "__main__":
    import uvicorn
    
    # Configure uvicorn logging to use VibeCoding
    uvicorn_logger = setup_vibe_logging(vibe_logger, "uvicorn")
    
    uvicorn_logger.vibe_info(
        operation="server_start",
        message="Starting FastAPI server with VibeCoding logging",
        context={
            "host": "127.0.0.1",
            "port": 8000
        }
    )
    
    uvicorn.run(
        "fastapi_integration:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_config=None  # Disable default logging to use our VibeCoding setup
    )