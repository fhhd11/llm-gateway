import structlog
import logging
import sys
from typing import Any, Dict
from app.config import get_settings

settings = get_settings()

# Configure standard logging to work with structlog
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=getattr(logging, settings.log_level.upper(), logging.INFO)
)

# Configure structlog with comprehensive processors
structlog.configure(
    processors=[
        # Add timestamp
        structlog.processors.TimeStamper(fmt="iso"),
        
        # Add log level
        structlog.stdlib.filter_by_level,
        
        # Add caller information
        structlog.processors.CallsiteParameterAdder(
            parameters=[
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        ),
        
        # Add exception info
        structlog.processors.format_exc_info,
        
        # Add stack info
        structlog.processors.StackInfoRenderer(),
        
        # Add module name
        structlog.stdlib.add_logger_name,
        
        # Add log level name
        structlog.stdlib.add_log_level,
        
        # Add log level number
        structlog.stdlib.add_log_level_number,
        
        # Render as JSON
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# Create a base logger
logger = structlog.get_logger()

def get_logger(name: str = None) -> structlog.stdlib.BoundLogger:
    """Get a logger with the specified name"""
    return structlog.get_logger(name)

def log_request(request_id: str, method: str, url: str, user_id: str = None, **kwargs):
    """Log HTTP request with structured data"""
    log_data = {
        "request_id": request_id,
        "method": method,
        "url": url,
    }
    if user_id:
        log_data["user_id"] = user_id
    
    # Add any additional kwargs, but don't override existing fields
    for key, value in kwargs.items():
        if key not in log_data:
            log_data[key] = value
    
    logger.info("HTTP request", **log_data)

def log_response(request_id: str, status_code: int, response_time: float, **kwargs):
    """Log HTTP response with structured data"""
    log_data = {
        "request_id": request_id,
        "status_code": status_code,
        "response_time_ms": round(response_time * 1000, 2),
    }
    
    # Add any additional kwargs, but don't override existing fields
    for key, value in kwargs.items():
        if key not in log_data:
            log_data[key] = value
    
    # Use appropriate log level based on status code
    if status_code >= 500:
        logger.error("HTTP response", **log_data)
    elif status_code >= 400:
        logger.warning("HTTP response", **log_data)
    else:
        logger.info("HTTP response", **log_data)

def log_llm_call(model: str, user_id: str, input_tokens: int = None, output_tokens: int = None, 
                 cost: float = None, duration: float = None, success: bool = True, **kwargs):
    """Log LLM API call with structured data"""
    log_data = {
        "model": model,
        "user_id": user_id,
        "success": success,
    }
    
    if input_tokens is not None:
        log_data["input_tokens"] = input_tokens
    if output_tokens is not None:
        log_data["output_tokens"] = output_tokens
    if cost is not None:
        log_data["cost"] = cost
    if duration is not None:
        log_data["duration_ms"] = round(duration * 1000, 2)
    
    # Add any additional kwargs, but don't override existing fields
    for key, value in kwargs.items():
        if key not in log_data:
            log_data[key] = value
    
    if success:
        logger.info("LLM call completed", **log_data)
    else:
        logger.error("LLM call failed", **log_data)

def log_billing_operation(user_id: str, operation: str, amount: float, balance_before: float, 
                         balance_after: float, success: bool = True, **kwargs):
    """Log billing operations with structured data"""
    log_data = {
        "user_id": user_id,
        "operation": operation,
        "amount": amount,
        "balance_before": balance_before,
        "balance_after": balance_after,
        "success": success,
    }
    
    # Add any additional kwargs, but don't override existing fields
    for key, value in kwargs.items():
        if key not in log_data:
            log_data[key] = value
    
    if success:
        logger.info("Billing operation completed", **log_data)
    else:
        logger.error("Billing operation failed", **log_data)

def log_error(error: Exception, context: Dict[str, Any] = None, **kwargs):
    """Log errors with structured data"""
    log_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
    }
    
    if context:
        log_data["context"] = context
    
    # Add any additional kwargs, but don't override existing fields
    for key, value in kwargs.items():
        if key not in log_data:
            log_data[key] = value
    
    logger.error("Application error", **log_data)

def log_performance(operation: str, duration: float, **kwargs):
    """Log performance metrics with structured data"""
    log_data = {
        "operation": operation,
        "duration_ms": round(duration * 1000, 2),
    }
    
    # Add any additional kwargs, but don't override existing fields
    for key, value in kwargs.items():
        if key not in log_data:
            log_data[key] = value
    
    logger.info("Performance metric", **log_data)