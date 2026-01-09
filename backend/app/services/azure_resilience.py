"""
Azure Service Resilience Module
Provides error handling, retry logic, and graceful degradation for Azure services
"""
import time
import logging
import functools
from typing import Any, Callable, Dict, Optional, Tuple, Union
from enum import Enum
from datetime import datetime, timedelta

from azure.core.exceptions import (
    AzureError, 
    ServiceRequestError, 
    ServiceResponseError,
    HttpResponseError,
    ResourceNotFoundError,
    ClientAuthenticationError
)

from app.services.audit import AuditService

logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    """Enum for tracking Azure service availability status"""
    AVAILABLE = "available"
    DEGRADED = "degraded" 
    UNAVAILABLE = "unavailable"

class RetryStrategy(Enum):
    """Enum for different retry strategies"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_INTERVAL = "fixed_interval"

class AzureServiceError(Exception):
    """Custom exception for Azure service errors"""
    def __init__(self, message: str, service_name: str, error_type: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.service_name = service_name
        self.error_type = error_type
        self.retry_after = retry_after

class AzureResilienceService:
    """Service for managing Azure service resilience and error handling"""
    
    def __init__(self):
        self.audit_service = AuditService()
        self.service_status = {}
        self.failure_counts = {}
        self.last_failure_times = {}
        
        # Configuration
        self.max_retries = 3
        self.base_delay = 1.0  # Base delay in seconds
        self.max_delay = 60.0  # Maximum delay in seconds
        self.circuit_breaker_threshold = 5  # Failures before circuit opens
        self.circuit_breaker_timeout = 300  # Seconds before trying again
    
    def with_retry(self, 
                   service_name: str,
                   strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
                   max_retries: Optional[int] = None,
                   base_delay: Optional[float] = None,
                   max_delay: Optional[float] = None):
        """
        Decorator for adding retry logic to Azure service calls
        
        Args:
            service_name: Name of the Azure service (e.g., 'azure_vision', 'azure_openai')
            strategy: Retry strategy to use
            max_retries: Maximum number of retry attempts
            base_delay: Base delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                return self._execute_with_retry(
                    func, service_name, strategy, 
                    max_retries or self.max_retries,
                    base_delay or self.base_delay,
                    max_delay or self.max_delay,
                    *args, **kwargs
                )
            return wrapper
        return decorator
    
    def _execute_with_retry(self, 
                           func: Callable, 
                           service_name: str,
                           strategy: RetryStrategy,
                           max_retries: int,
                           base_delay: float,
                           max_delay: float,
                           *args, **kwargs) -> Any:
        """
        Execute function with retry logic and circuit breaker pattern
        
        Args:
            func: Function to execute
            service_name: Name of the Azure service
            strategy: Retry strategy
            max_retries: Maximum retry attempts
            base_delay: Base delay between retries
            max_delay: Maximum delay between retries
            *args, **kwargs: Arguments to pass to the function
            
        Returns:
            Function result
            
        Raises:
            AzureServiceError: When all retries are exhausted or circuit is open
        """
        # Check circuit breaker
        if self._is_circuit_open(service_name):
            error_msg = f"Circuit breaker is open for {service_name}. Service temporarily unavailable."
            logger.warning(error_msg)
            
            self.audit_service.create_log_entry(
                user_id=kwargs.get('user_id', 'system'),
                event_type="azure_service_circuit_open",
                event_description=error_msg,
                ai_service_used=service_name,
                status="failure"
            )
            
            raise AzureServiceError(
                error_msg, 
                service_name, 
                "circuit_breaker_open",
                retry_after=self.circuit_breaker_timeout
            )
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                # Log attempt if it's a retry
                if attempt > 0:
                    self.audit_service.create_log_entry(
                        user_id=kwargs.get('user_id', 'system'),
                        event_type="azure_service_retry_attempt",
                        event_description=f"Retry attempt {attempt} for {service_name}",
                        ai_service_used=service_name,
                        input_data={"attempt": attempt, "max_retries": max_retries}
                    )
                
                # Execute the function
                result = func(*args, **kwargs)
                
                # Success - reset failure count and update status
                self._record_success(service_name)
                return result
                
            except (AzureError, ServiceRequestError, ServiceResponseError, HttpResponseError) as e:
                last_exception = e
                
                # Record the failure
                self._record_failure(service_name, str(e))
                
                # Check if this is the last attempt
                if attempt == max_retries:
                    break
                
                # Determine if error is retryable
                if not self._is_retryable_error(e):
                    logger.error(f"Non-retryable error for {service_name}: {str(e)}")
                    break
                
                # Calculate delay for next attempt
                delay = self._calculate_delay(strategy, attempt, base_delay, max_delay)
                
                logger.warning(f"Azure service {service_name} failed (attempt {attempt + 1}/{max_retries + 1}): {str(e)}. Retrying in {delay:.2f} seconds.")
                
                # Wait before retry
                time.sleep(delay)
                
            except Exception as e:
                # Non-Azure errors are not retried
                last_exception = e
                logger.error(f"Non-Azure error in {service_name}: {str(e)}")
                break
        
        # All retries exhausted or non-retryable error
        error_msg = f"Azure service {service_name} failed after {max_retries + 1} attempts: {str(last_exception)}"
        logger.error(error_msg)
        
        self.audit_service.create_log_entry(
            user_id=kwargs.get('user_id', 'system'),
            event_type="azure_service_failure",
            event_description=error_msg,
            ai_service_used=service_name,
            input_data={"attempts": max_retries + 1, "final_error": str(last_exception)},
            status="failure"
        )
        
        # Determine error type
        error_type = self._classify_error(last_exception)
        
        raise AzureServiceError(error_msg, service_name, error_type) from last_exception
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """
        Determine if an error is retryable
        
        Args:
            error: Exception that occurred
            
        Returns:
            True if error is retryable, False otherwise
        """
        # Authentication errors are not retryable
        if isinstance(error, ClientAuthenticationError):
            return False
        
        # Resource not found errors are not retryable
        if isinstance(error, ResourceNotFoundError):
            return False
        
        # HTTP errors with specific status codes
        if isinstance(error, HttpResponseError):
            # Don't retry client errors (4xx) except for rate limiting (429)
            if hasattr(error, 'status_code'):
                status_code = error.status_code
                if 400 <= status_code < 500 and status_code != 429:
                    return False
        
        # Service errors and network errors are generally retryable
        return True
    
    def _calculate_delay(self, 
                        strategy: RetryStrategy, 
                        attempt: int, 
                        base_delay: float, 
                        max_delay: float) -> float:
        """
        Calculate delay for next retry attempt
        
        Args:
            strategy: Retry strategy to use
            attempt: Current attempt number (0-based)
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
            
        Returns:
            Delay in seconds
        """
        if strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = base_delay * (2 ** attempt)
        elif strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = base_delay * (attempt + 1)
        else:  # FIXED_INTERVAL
            delay = base_delay
        
        # Apply jitter to avoid thundering herd
        import random
        jitter = random.uniform(0.8, 1.2)
        delay *= jitter
        
        return min(delay, max_delay)
    
    def _record_success(self, service_name: str) -> None:
        """Record successful service call"""
        self.service_status[service_name] = ServiceStatus.AVAILABLE
        self.failure_counts[service_name] = 0
        if service_name in self.last_failure_times:
            del self.last_failure_times[service_name]
    
    def _record_failure(self, service_name: str, error_message: str) -> None:
        """Record failed service call"""
        self.failure_counts[service_name] = self.failure_counts.get(service_name, 0) + 1
        self.last_failure_times[service_name] = datetime.now()
        
        # Update service status based on failure count
        failure_count = self.failure_counts[service_name]
        if failure_count >= self.circuit_breaker_threshold:
            self.service_status[service_name] = ServiceStatus.UNAVAILABLE
        elif failure_count > 1:
            self.service_status[service_name] = ServiceStatus.DEGRADED
    
    def _is_circuit_open(self, service_name: str) -> bool:
        """Check if circuit breaker is open for a service"""
        if self.service_status.get(service_name) != ServiceStatus.UNAVAILABLE:
            return False
        
        last_failure = self.last_failure_times.get(service_name)
        if not last_failure:
            return False
        
        # Check if timeout period has passed
        time_since_failure = (datetime.now() - last_failure).total_seconds()
        return time_since_failure < self.circuit_breaker_timeout
    
    def _classify_error(self, error: Exception) -> str:
        """Classify error type for reporting"""
        if isinstance(error, ClientAuthenticationError):
            return "authentication_error"
        elif isinstance(error, ResourceNotFoundError):
            return "resource_not_found"
        elif isinstance(error, ServiceRequestError):
            return "request_error"
        elif isinstance(error, ServiceResponseError):
            return "response_error"
        elif isinstance(error, HttpResponseError):
            return f"http_error_{getattr(error, 'status_code', 'unknown')}"
        else:
            return "unknown_error"
    
    def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """
        Get current status of an Azure service
        
        Args:
            service_name: Name of the service
            
        Returns:
            Dictionary containing service status information
        """
        status = self.service_status.get(service_name, ServiceStatus.AVAILABLE)
        failure_count = self.failure_counts.get(service_name, 0)
        last_failure = self.last_failure_times.get(service_name)
        
        return {
            'service_name': service_name,
            'status': status.value,
            'failure_count': failure_count,
            'last_failure': last_failure.isoformat() if last_failure else None,
            'circuit_open': self._is_circuit_open(service_name)
        }
    
    def get_all_service_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all tracked services"""
        all_services = set(self.service_status.keys()) | set(self.failure_counts.keys())
        return {
            service: self.get_service_status(service) 
            for service in all_services
        }
    
    def reset_circuit_breaker(self, service_name: str) -> bool:
        """
        Manually reset circuit breaker for a service
        
        Args:
            service_name: Name of the service
            
        Returns:
            True if reset was successful
        """
        try:
            self.service_status[service_name] = ServiceStatus.AVAILABLE
            self.failure_counts[service_name] = 0
            if service_name in self.last_failure_times:
                del self.last_failure_times[service_name]
            
            self.audit_service.create_log_entry(
                user_id='system',
                event_type="circuit_breaker_reset",
                event_description=f"Circuit breaker manually reset for {service_name}",
                ai_service_used=service_name,
                status="success"
            )
            
            logger.info(f"Circuit breaker reset for service: {service_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset circuit breaker for {service_name}: {str(e)}")
            return False

# Global instance for use across the application
azure_resilience = AzureResilienceService()

def with_azure_retry(service_name: str, **kwargs):
    """Convenience decorator for Azure service retry logic"""
    return azure_resilience.with_retry(service_name, **kwargs)

def get_service_health() -> Dict[str, Any]:
    """Get health status of all Azure services"""
    return azure_resilience.get_all_service_status()

def reset_service_circuit(service_name: str) -> bool:
    """Reset circuit breaker for a specific service"""
    return azure_resilience.reset_circuit_breaker(service_name)