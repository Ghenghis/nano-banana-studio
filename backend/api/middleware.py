"""
Nano Banana Studio Pro - API Middleware
========================================
Error handling, logging, and request validation middleware.
"""

import time
import logging
import traceback
from typing import Callable, Any
from datetime import datetime

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("api-middleware")


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Global error handling middleware with structured error responses.
    Provides meaningful feedback and suggested fixes for common errors.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Log successful requests
            process_time = time.time() - start_time
            logger.info(
                f"{request.method} {request.url.path} "
                f"completed in {process_time:.3f}s "
                f"status={response.status_code}"
            )
            
            # Add timing header
            response.headers["X-Process-Time"] = f"{process_time:.3f}"
            
            return response
            
        except HTTPException as e:
            # Handle FastAPI HTTP exceptions
            return self._create_error_response(
                status_code=e.status_code,
                error_type="http_error",
                message=e.detail,
                request=request,
                process_time=time.time() - start_time
            )
            
        except ValueError as e:
            # Handle validation errors
            return self._create_error_response(
                status_code=400,
                error_type="validation_error",
                message=str(e),
                request=request,
                process_time=time.time() - start_time,
                suggestions=[
                    "Check that all required fields are provided",
                    "Verify field types match the expected format",
                    "Review the API documentation for correct usage"
                ]
            )
            
        except FileNotFoundError as e:
            return self._create_error_response(
                status_code=404,
                error_type="file_not_found",
                message=str(e),
                request=request,
                process_time=time.time() - start_time,
                suggestions=[
                    "Verify the file path is correct",
                    "Check if the file was uploaded successfully",
                    "Ensure the resource ID is valid"
                ]
            )
            
        except PermissionError as e:
            return self._create_error_response(
                status_code=403,
                error_type="permission_error",
                message=str(e),
                request=request,
                process_time=time.time() - start_time,
                suggestions=[
                    "Check file/directory permissions",
                    "Verify API key has necessary scopes",
                    "Contact administrator if issue persists"
                ]
            )
            
        except ConnectionError as e:
            return self._create_error_response(
                status_code=503,
                error_type="connection_error",
                message=f"Service connection failed: {e}",
                request=request,
                process_time=time.time() - start_time,
                suggestions=[
                    "Check if required services are running",
                    "Verify network connectivity",
                    "Try again in a few moments"
                ]
            )
            
        except Exception as e:
            # Log unexpected errors with full traceback
            logger.error(
                f"Unexpected error in {request.method} {request.url.path}: {e}\n"
                f"{traceback.format_exc()}"
            )
            
            return self._create_error_response(
                status_code=500,
                error_type="internal_error",
                message="An unexpected error occurred",
                request=request,
                process_time=time.time() - start_time,
                details=str(e) if logger.level <= logging.DEBUG else None,
                suggestions=[
                    "Check server logs for details",
                    "Retry the request",
                    "Contact support if issue persists"
                ]
            )
    
    def _create_error_response(
        self,
        status_code: int,
        error_type: str,
        message: str,
        request: Request,
        process_time: float,
        details: str = None,
        suggestions: list = None
    ) -> JSONResponse:
        """Create structured error response."""
        
        error_body = {
            "success": False,
            "error": {
                "type": error_type,
                "status_code": status_code,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url.path),
                "method": request.method
            }
        }
        
        if details:
            error_body["error"]["details"] = details
            
        if suggestions:
            error_body["error"]["suggestions"] = suggestions
        
        logger.warning(
            f"{request.method} {request.url.path} "
            f"failed with {status_code} in {process_time:.3f}s: {message}"
        )
        
        return JSONResponse(
            status_code=status_code,
            content=error_body,
            headers={"X-Process-Time": f"{process_time:.3f}"}
        )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all incoming requests with relevant details."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Log request
        logger.debug(
            f"Incoming {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        
        response = await call_next(request)
        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Validate common request requirements."""
    
    # Endpoints that require specific content types
    JSON_REQUIRED_PATHS = ["/api/v1/enhance", "/api/v1/timeline/quick-create"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check content type for JSON endpoints
        if request.method in ["POST", "PUT", "PATCH"]:
            for path in self.JSON_REQUIRED_PATHS:
                if request.url.path.startswith(path):
                    content_type = request.headers.get("content-type", "")
                    if not content_type.startswith(("application/json", "multipart/form-data")):
                        return JSONResponse(
                            status_code=415,
                            content={
                                "success": False,
                                "error": {
                                    "type": "unsupported_media_type",
                                    "message": "Content-Type must be application/json or multipart/form-data",
                                    "suggestions": [
                                        "Set Content-Type header to application/json",
                                        "Use multipart/form-data for file uploads"
                                    ]
                                }
                            }
                        )
        
        return await call_next(request)


def setup_middleware(app):
    """Setup all middleware for the FastAPI application."""
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RequestValidationMiddleware)
    logger.info("API middleware configured")
