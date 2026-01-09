"""
Comprehensive Error Handling and User Feedback Module
Provides standardized error responses and user-friendly error messages
"""
import logging
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories for classification"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    SERVICE_UNAVAILABLE = "service_unavailable"
    NETWORK = "network"
    DATA_INTEGRITY = "data_integrity"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM = "system"

class UserFeedbackService:
    """Service for generating user-friendly error messages and feedback"""
    
    @staticmethod
    def create_error_response(
        error_code: str,
        error_message: str,
        category: ErrorCategory,
        severity: ErrorSeverity,
        user_message: Optional[str] = None,
        suggested_actions: Optional[list] = None,
        technical_details: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create standardized error response
        
        Args:
            error_code: Unique error code for tracking
            error_message: Technical error message
            category: Error category
            severity: Error severity level
            user_message: User-friendly error message
            suggested_actions: List of suggested actions for the user
            technical_details: Additional technical information
            retry_after: Seconds to wait before retrying (if applicable)
            
        Returns:
            Standardized error response dictionary
        """
        response = {
            'status': 'error',
            'error': {
                'code': error_code,
                'message': error_message,
                'category': category.value,
                'severity': severity.value,
                'user_message': user_message or UserFeedbackService._generate_user_message(category, error_message),
                'suggested_actions': suggested_actions or UserFeedbackService._generate_suggested_actions(category),
                'timestamp': logger.handlers[0].formatter.formatTime(logging.LogRecord(
                    name='', level=0, pathname='', lineno=0, msg='', args=(), exc_info=None
                )) if logger.handlers else None
            }
        }
        
        if technical_details:
            response['error']['technical_details'] = technical_details
        
        if retry_after:
            response['error']['retry_after'] = retry_after
        
        return response
    
    @staticmethod
    def _generate_user_message(category: ErrorCategory, technical_message: str) -> str:
        """Generate user-friendly message based on error category"""
        user_messages = {
            ErrorCategory.AUTHENTICATION: "Authentication failed. Please check your credentials and try again.",
            ErrorCategory.AUTHORIZATION: "You don't have permission to perform this action. Please contact your administrator.",
            ErrorCategory.VALIDATION: "The information provided is invalid. Please check your input and try again.",
            ErrorCategory.SERVICE_UNAVAILABLE: "The service is temporarily unavailable. Please try again in a few minutes.",
            ErrorCategory.NETWORK: "Network connection issue. Please check your internet connection and try again.",
            ErrorCategory.DATA_INTEGRITY: "Data integrity issue detected. Please contact support for assistance.",
            ErrorCategory.BUSINESS_LOGIC: "Unable to complete the requested operation due to business rules.",
            ErrorCategory.SYSTEM: "A system error occurred. Please try again or contact support if the problem persists."
        }
        
        return user_messages.get(category, "An unexpected error occurred. Please try again or contact support.")
    
    @staticmethod
    def _generate_suggested_actions(category: ErrorCategory) -> list:
        """Generate suggested actions based on error category"""
        action_suggestions = {
            ErrorCategory.AUTHENTICATION: [
                "Verify your username and password",
                "Check if your account is locked",
                "Try resetting your password"
            ],
            ErrorCategory.AUTHORIZATION: [
                "Contact your system administrator",
                "Verify you have the necessary permissions",
                "Check if your account status is active"
            ],
            ErrorCategory.VALIDATION: [
                "Review the input requirements",
                "Check for required fields",
                "Verify data format is correct"
            ],
            ErrorCategory.SERVICE_UNAVAILABLE: [
                "Wait a few minutes and try again",
                "Check service status page",
                "Contact support if issue persists"
            ],
            ErrorCategory.NETWORK: [
                "Check your internet connection",
                "Try refreshing the page",
                "Contact your network administrator"
            ],
            ErrorCategory.DATA_INTEGRITY: [
                "Contact technical support immediately",
                "Do not retry the operation",
                "Provide error details to support team"
            ],
            ErrorCategory.BUSINESS_LOGIC: [
                "Review the operation requirements",
                "Check if prerequisites are met",
                "Contact support for clarification"
            ],
            ErrorCategory.SYSTEM: [
                "Try the operation again",
                "Clear browser cache and cookies",
                "Contact support if problem continues"
            ]
        }
        
        return action_suggestions.get(category, ["Try again later", "Contact support if issue persists"])

class DeathVerificationErrorHandler:
    """Specialized error handler for death verification processes"""
    
    @staticmethod
    def handle_ocr_failure(error: Exception, user_id: str) -> Dict[str, Any]:
        """Handle OCR extraction failures"""
        return UserFeedbackService.create_error_response(
            error_code="OCR_EXTRACTION_FAILED",
            error_message=str(error),
            category=ErrorCategory.SERVICE_UNAVAILABLE,
            severity=ErrorSeverity.MEDIUM,
            user_message="Unable to extract text from the death certificate. The document may be unclear or the OCR service is temporarily unavailable.",
            suggested_actions=[
                "Ensure the document is clear and readable",
                "Try uploading a higher quality image",
                "Submit for manual review if the issue persists",
                "Contact support for assistance"
            ],
            technical_details={"user_id": user_id, "service": "azure_vision"}
        )
    
    @staticmethod
    def handle_certificate_validation_failure(validation_errors: list, user_id: str) -> Dict[str, Any]:
        """Handle certificate validation failures"""
        return UserFeedbackService.create_error_response(
            error_code="CERTIFICATE_VALIDATION_FAILED",
            error_message=f"Certificate validation failed: {'; '.join(validation_errors)}",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.HIGH,
            user_message="The death certificate could not be validated. Required information may be missing or unclear.",
            suggested_actions=[
                "Verify the document is a valid death certificate",
                "Ensure all required fields are visible and clear",
                "Upload a different copy of the certificate",
                "Submit for manual review"
            ],
            technical_details={"user_id": user_id, "validation_errors": validation_errors}
        )
    
    @staticmethod
    def handle_name_mismatch(extracted_name: str, profile_name: str, similarity_score: float, user_id: str) -> Dict[str, Any]:
        """Handle name matching failures"""
        return UserFeedbackService.create_error_response(
            error_code="NAME_VERIFICATION_FAILED",
            error_message=f"Name mismatch: extracted '{extracted_name}' vs profile '{profile_name}' (similarity: {similarity_score:.2f})",
            category=ErrorCategory.BUSINESS_LOGIC,
            severity=ErrorSeverity.HIGH,
            user_message="The name on the death certificate does not match the user profile. This may be due to name variations or OCR errors.",
            suggested_actions=[
                "Verify the certificate belongs to the correct person",
                "Check for name variations (maiden name, nicknames, etc.)",
                "Upload a clearer image of the certificate",
                "Submit for manual review with explanation"
            ],
            technical_details={
                "user_id": user_id,
                "extracted_name": extracted_name,
                "profile_name": profile_name,
                "similarity_score": similarity_score
            }
        )
    
    @staticmethod
    def handle_date_validation_failure(date_string: str, error_reason: str, user_id: str) -> Dict[str, Any]:
        """Handle date validation failures"""
        return UserFeedbackService.create_error_response(
            error_code="DATE_VALIDATION_FAILED",
            error_message=f"Date validation failed for '{date_string}': {error_reason}",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            user_message="The date of death on the certificate is invalid or could not be parsed.",
            suggested_actions=[
                "Verify the date format is clear and readable",
                "Check that the date is not in the future",
                "Upload a clearer image of the certificate",
                "Submit for manual review"
            ],
            technical_details={
                "user_id": user_id,
                "date_string": date_string,
                "error_reason": error_reason
            }
        )
    
    @staticmethod
    def handle_service_unavailable(service_name: str, retry_after: Optional[int], user_id: str) -> Dict[str, Any]:
        """Handle Azure service unavailability"""
        return UserFeedbackService.create_error_response(
            error_code="AZURE_SERVICE_UNAVAILABLE",
            error_message=f"Azure {service_name} service is temporarily unavailable",
            category=ErrorCategory.SERVICE_UNAVAILABLE,
            severity=ErrorSeverity.MEDIUM,
            user_message=f"The {service_name} service is temporarily unavailable. Your request has been queued for processing when the service becomes available.",
            suggested_actions=[
                f"Try again in {retry_after // 60} minutes" if retry_after else "Try again in a few minutes",
                "Submit for manual review if urgent",
                "Check service status page for updates"
            ],
            technical_details={"user_id": user_id, "service": service_name},
            retry_after=retry_after
        )

class AuditErrorHandler:
    """Specialized error handler for audit logging failures"""
    
    @staticmethod
    def handle_audit_failure(operation: str, error: Exception, user_id: str) -> Dict[str, Any]:
        """Handle audit logging failures"""
        return UserFeedbackService.create_error_response(
            error_code="AUDIT_LOG_FAILURE",
            error_message=f"Failed to log audit event for {operation}: {str(error)}",
            category=ErrorCategory.DATA_INTEGRITY,
            severity=ErrorSeverity.CRITICAL,
            user_message="A critical system error occurred while logging this operation. The operation may have completed but was not properly recorded.",
            suggested_actions=[
                "Contact system administrator immediately",
                "Do not retry the operation",
                "Provide operation details to support team"
            ],
            technical_details={"user_id": user_id, "operation": operation, "error": str(error)}
        )

class DatabaseErrorHandler:
    """Specialized error handler for database operations"""
    
    @staticmethod
    def handle_connection_failure(error: Exception) -> Dict[str, Any]:
        """Handle database connection failures"""
        return UserFeedbackService.create_error_response(
            error_code="DATABASE_CONNECTION_FAILED",
            error_message=f"Database connection failed: {str(error)}",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.CRITICAL,
            user_message="Unable to connect to the database. The system is temporarily unavailable.",
            suggested_actions=[
                "Try again in a few minutes",
                "Contact support if issue persists",
                "Check system status page"
            ],
            technical_details={"error": str(error)}
        )
    
    @staticmethod
    def handle_transaction_failure(operation: str, error: Exception, user_id: str) -> Dict[str, Any]:
        """Handle database transaction failures"""
        return UserFeedbackService.create_error_response(
            error_code="DATABASE_TRANSACTION_FAILED",
            error_message=f"Database transaction failed for {operation}: {str(error)}",
            category=ErrorCategory.DATA_INTEGRITY,
            severity=ErrorSeverity.HIGH,
            user_message="The operation could not be completed due to a database error. No changes have been made.",
            suggested_actions=[
                "Try the operation again",
                "Contact support if issue persists",
                "Verify your input data is correct"
            ],
            technical_details={"user_id": user_id, "operation": operation, "error": str(error)}
        )