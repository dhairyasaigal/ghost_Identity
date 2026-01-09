"""
Service modules for business logic
"""
from .database import DatabaseService, create_user_profile, create_trusted_contact, create_action_policy
from .audit import AuditService, DatabaseChangeLogger
from .death_verification import DeathVerificationService
from .action_engine import ActionEngineService
from .azure_resilience import AzureResilienceService, with_azure_retry, get_service_health, reset_service_circuit
from .error_handling import UserFeedbackService, DeathVerificationErrorHandler, AuditErrorHandler, DatabaseErrorHandler
from .notification_delivery import NotificationDeliveryService, DeliveryStatus, DeliveryMethod
from .notification_templates import NotificationTemplateService, TemplateType, ActionType

__all__ = [
    'DatabaseService', 'AuditService', 'DatabaseChangeLogger', 'DeathVerificationService',
    'ActionEngineService', 'AzureResilienceService', 'UserFeedbackService', 'DeathVerificationErrorHandler', 
    'AuditErrorHandler', 'DatabaseErrorHandler', 'NotificationDeliveryService', 'NotificationTemplateService',
    'DeliveryStatus', 'DeliveryMethod', 'TemplateType', 'ActionType',
    'create_user_profile', 'create_trusted_contact', 'create_action_policy',
    'with_azure_retry', 'get_service_health', 'reset_service_circuit'
]