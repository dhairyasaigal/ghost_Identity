"""
Notification Delivery Service
Handles email and API-based notification delivery with status tracking and retry logic
"""
import os
import json
import logging
import smtplib
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.services.audit import AuditService
from app.services.azure_resilience import with_azure_retry, AzureServiceError

logger = logging.getLogger(__name__)

class DeliveryStatus(Enum):
    """Enumeration for notification delivery status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRY = "retry"
    EXPIRED = "expired"

class DeliveryMethod(Enum):
    """Enumeration for delivery methods"""
    EMAIL = "email"
    API = "api"
    WEBHOOK = "webhook"
    FORM_SUBMISSION = "form"

class NotificationDeliveryService:
    """
    Service for delivering notifications to platforms with status tracking and retry logic
    """
    
    def __init__(self):
        """Initialize the Notification Delivery Service"""
        self.audit_service = AuditService()
        
        # Email configuration
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_username)
        
        # Retry configuration
        self.max_retries = int(os.getenv('MAX_DELIVERY_RETRIES', '3'))
        self.base_retry_delay = int(os.getenv('BASE_RETRY_DELAY', '300'))  # 5 minutes
        self.max_retry_delay = int(os.getenv('MAX_RETRY_DELAY', '3600'))   # 1 hour
        self.retry_multiplier = float(os.getenv('RETRY_MULTIPLIER', '2.0'))
        
        # Delivery tracking
        self.delivery_status = {}  # In-memory status tracking (should be database in production)
        
        # HTTP session for API calls
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],  # Updated parameter name
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Platform-specific API configurations
        self.platform_apis = {
            'google': {
                'endpoint': 'https://www.googleapis.com/gmail/v1/users/me/messages/send',
                'auth_required': True,
                'method': 'POST'
            },
            'facebook': {
                'endpoint': 'https://graph.facebook.com/v18.0/me/messages',
                'auth_required': True,
                'method': 'POST'
            },
            'microsoft': {
                'endpoint': 'https://graph.microsoft.com/v1.0/me/sendMail',
                'auth_required': True,
                'method': 'POST'
            }
        }
    
    def deliver_notification(self, notification: Dict[str, Any], 
                           delivery_method: str = None, 
                           user_id: str = None) -> Dict[str, Any]:
        """
        Deliver a single notification with status tracking
        
        Args:
            notification: Notification dictionary containing delivery details
            delivery_method: Override delivery method (email, api, webhook, form)
            user_id: User ID for audit logging
            
        Returns:
            Dictionary containing delivery result and status
        """
        notification_id = notification.get('policy_id', f"notif_{int(time.time())}")
        
        # Determine delivery method
        method = delivery_method or notification.get('delivery_method', 'email')
        
        # Initialize delivery tracking
        delivery_record = {
            'notification_id': notification_id,
            'platform': notification.get('platform', 'unknown'),
            'delivery_method': method,
            'status': DeliveryStatus.PENDING.value,
            'attempts': 0,
            'created_at': datetime.utcnow().isoformat(),
            'last_attempt': None,
            'next_retry': None,
            'error_message': None,
            'delivery_details': {}
        }
        
        self.delivery_status[notification_id] = delivery_record
        
        # Log delivery attempt
        if user_id:
            self.audit_service.create_log_entry(
                user_id=user_id,
                event_type="notification_delivery_start",
                event_description=f"Starting delivery of notification to {notification.get('platform')} via {method}",
                input_data={
                    'notification_id': notification_id,
                    'platform': notification.get('platform'),
                    'delivery_method': method
                }
            )
        
        try:
            # Deliver based on method
            if method == DeliveryMethod.EMAIL.value:
                result = self._deliver_via_email(notification, delivery_record)
            elif method == DeliveryMethod.API.value:
                result = self._deliver_via_api(notification, delivery_record)
            elif method == DeliveryMethod.WEBHOOK.value:
                result = self._deliver_via_webhook(notification, delivery_record)
            elif method == DeliveryMethod.FORM_SUBMISSION.value:
                result = self._deliver_via_form(notification, delivery_record)
            else:
                raise ValueError(f"Unsupported delivery method: {method}")
            
            # Update delivery status
            delivery_record.update(result)
            delivery_record['last_attempt'] = datetime.utcnow().isoformat()
            delivery_record['attempts'] += 1
            
            # Log successful delivery
            if user_id and result.get('status') == DeliveryStatus.SENT.value:
                self.audit_service.create_log_entry(
                    user_id=user_id,
                    event_type="notification_delivery_success",
                    event_description=f"Successfully delivered notification to {notification.get('platform')}",
                    input_data={'notification_id': notification_id},
                    output_data=result,
                    status="success"
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error delivering notification {notification_id}: {str(e)}")
            
            # Update delivery status with error
            delivery_record['status'] = DeliveryStatus.FAILED.value
            delivery_record['error_message'] = str(e)
            delivery_record['last_attempt'] = datetime.utcnow().isoformat()
            delivery_record['attempts'] += 1
            
            # Schedule retry if within limits
            if delivery_record['attempts'] < self.max_retries:
                retry_delay = min(
                    self.base_retry_delay * (self.retry_multiplier ** (delivery_record['attempts'] - 1)),
                    self.max_retry_delay
                )
                delivery_record['next_retry'] = (datetime.utcnow() + timedelta(seconds=retry_delay)).isoformat()
                delivery_record['status'] = DeliveryStatus.RETRY.value
            
            # Log delivery error
            if user_id:
                self.audit_service.create_log_entry(
                    user_id=user_id,
                    event_type="notification_delivery_error",
                    event_description=f"Failed to deliver notification to {notification.get('platform')}: {str(e)}",
                    input_data={'notification_id': notification_id},
                    status="failure"
                )
            
            return {
                'status': delivery_record['status'],
                'error_message': str(e),
                'notification_id': notification_id,
                'retry_scheduled': delivery_record['status'] == DeliveryStatus.RETRY.value,
                'next_retry': delivery_record.get('next_retry')
            }
    
    def _deliver_via_email(self, notification: Dict[str, Any], 
                          delivery_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deliver notification via email
        
        Args:
            notification: Notification dictionary
            delivery_record: Delivery tracking record
            
        Returns:
            Dictionary containing delivery result
        """
        if not all([self.smtp_username, self.smtp_password]):
            raise ValueError("SMTP credentials not configured")
        
        # Extract email details
        to_email = notification.get('recipient_email')
        if not to_email:
            # Use platform-specific contact email or default
            platform_name = notification.get('platform', '').lower()
            platform_contacts = {
                'google': 'accounts-support@google.com',
                'facebook': 'support@facebook.com',
                'chase_bank': 'estate.services@chase.com',
                'wells_fargo': 'estate.services@wellsfargo.com',
                'bank_of_america': 'estate.administration@bankofamerica.com'
            }
            to_email = platform_contacts.get(platform_name, 'support@example.com')
        
        subject = notification.get('subject', 'Death Notification')
        body = notification.get('body', '')
        
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = self.from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add body
        msg.attach(MIMEText(body, 'plain'))
        
        # Add attachments if specified
        attachments = notification.get('attachments', [])
        for attachment in attachments:
            if isinstance(attachment, dict) and 'filename' in attachment and 'content' in attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment['content'])
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {attachment["filename"]}'
                )
                msg.attach(part)
        
        # Send email
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            
            text = msg.as_string()
            server.sendmail(self.from_email, to_email, text)
            server.quit()
            
            return {
                'status': DeliveryStatus.SENT.value,
                'delivery_details': {
                    'to_email': to_email,
                    'subject': subject,
                    'sent_at': datetime.utcnow().isoformat(),
                    'message_id': msg.get('Message-ID', 'unknown')
                }
            }
            
        except smtplib.SMTPException as e:
            raise Exception(f"SMTP error: {str(e)}")
    
    def _deliver_via_api(self, notification: Dict[str, Any], 
                        delivery_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deliver notification via platform API
        
        Args:
            notification: Notification dictionary
            delivery_record: Delivery tracking record
            
        Returns:
            Dictionary containing delivery result
        """
        platform_name = notification.get('platform', '').lower()
        
        # Get platform API configuration
        api_config = self.platform_apis.get(platform_name)
        if not api_config:
            raise ValueError(f"No API configuration found for platform: {platform_name}")
        
        # Prepare API request
        endpoint = api_config['endpoint']
        method = api_config.get('method', 'POST')
        
        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'GhostIdentityProtection/1.0'
        }
        
        # Add authentication if required
        if api_config.get('auth_required'):
            auth_token = os.getenv(f'{platform_name.upper()}_API_TOKEN')
            if auth_token:
                headers['Authorization'] = f'Bearer {auth_token}'
            else:
                logger.warning(f"No API token configured for {platform_name}")
        
        # Prepare payload
        payload = {
            'subject': notification.get('subject', ''),
            'body': notification.get('body', ''),
            'platform': platform_name,
            'action_type': notification.get('action_type', ''),
            'account_identifier': notification.get('account_identifier', ''),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Make API request
        try:
            if method.upper() == 'POST':
                response = self.session.post(endpoint, json=payload, headers=headers, timeout=30)
            elif method.upper() == 'PUT':
                response = self.session.put(endpoint, json=payload, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            return {
                'status': DeliveryStatus.SENT.value,
                'delivery_details': {
                    'endpoint': endpoint,
                    'response_status': response.status_code,
                    'response_data': response.json() if response.content else {},
                    'sent_at': datetime.utcnow().isoformat()
                }
            }
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
    
    def _deliver_via_webhook(self, notification: Dict[str, Any], 
                           delivery_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deliver notification via webhook
        
        Args:
            notification: Notification dictionary
            delivery_record: Delivery tracking record
            
        Returns:
            Dictionary containing delivery result
        """
        webhook_url = notification.get('webhook_url')
        if not webhook_url:
            raise ValueError("Webhook URL not specified")
        
        # Prepare webhook payload
        payload = {
            'event_type': 'death_notification',
            'platform': notification.get('platform', ''),
            'action_type': notification.get('action_type', ''),
            'notification_data': {
                'subject': notification.get('subject', ''),
                'body': notification.get('body', ''),
                'account_identifier': notification.get('account_identifier', ''),
                'required_documents': notification.get('required_documents', [])
            },
            'timestamp': datetime.utcnow().isoformat(),
            'notification_id': notification.get('policy_id', '')
        }
        
        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'GhostIdentityProtection/1.0'
        }
        
        # Add webhook signature if secret is configured
        webhook_secret = os.getenv('WEBHOOK_SECRET')
        if webhook_secret:
            import hmac
            import hashlib
            
            payload_str = json.dumps(payload, sort_keys=True)
            signature = hmac.new(
                webhook_secret.encode('utf-8'),
                payload_str.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            headers['X-Webhook-Signature'] = f'sha256={signature}'
        
        # Send webhook
        try:
            response = self.session.post(webhook_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            return {
                'status': DeliveryStatus.SENT.value,
                'delivery_details': {
                    'webhook_url': webhook_url,
                    'response_status': response.status_code,
                    'response_data': response.text[:500],  # Limit response data
                    'sent_at': datetime.utcnow().isoformat()
                }
            }
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Webhook delivery failed: {str(e)}")
    
    def _deliver_via_form(self, notification: Dict[str, Any], 
                         delivery_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deliver notification via form submission (simulated)
        
        Args:
            notification: Notification dictionary
            delivery_record: Delivery tracking record
            
        Returns:
            Dictionary containing delivery result
        """
        form_url = notification.get('form_url')
        if not form_url:
            # Use platform-specific form URLs
            platform_name = notification.get('platform', '').lower()
            form_urls = {
                'facebook': 'https://www.facebook.com/help/contact/228813257197480',
                'instagram': 'https://help.instagram.com/contact/1474899482730688',
                'linkedin': 'https://www.linkedin.com/help/linkedin/answer/2842',
                'microsoft': 'https://account.microsoft.com/profile/contact-info'
            }
            form_url = form_urls.get(platform_name)
        
        if not form_url:
            raise ValueError("Form URL not available for platform")
        
        # For now, we'll simulate form submission by creating a structured request
        # In a real implementation, this might use browser automation or platform-specific APIs
        
        form_data = {
            'deceased_name': notification.get('deceased_name', ''),
            'account_identifier': notification.get('account_identifier', ''),
            'action_requested': notification.get('action_type', ''),
            'message': notification.get('body', ''),
            'contact_email': notification.get('contact_email', ''),
            'form_url': form_url,
            'submission_method': 'automated'
        }
        
        # Log form submission details (in real implementation, this would submit the form)
        logger.info(f"Form submission prepared for {notification.get('platform')}: {form_url}")
        
        return {
            'status': DeliveryStatus.SENT.value,
            'delivery_details': {
                'form_url': form_url,
                'form_data': form_data,
                'submission_method': 'simulated',
                'sent_at': datetime.utcnow().isoformat(),
                'note': 'Form submission simulated - manual submission may be required'
            }
        }
    
    def batch_deliver_notifications(self, notifications: List[Dict[str, Any]], 
                                  user_id: str = None) -> Dict[str, Any]:
        """
        Deliver multiple notifications in batch with status tracking
        
        Args:
            notifications: List of notification dictionaries
            user_id: User ID for audit logging
            
        Returns:
            Dictionary containing batch delivery results
        """
        batch_id = f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(str(notifications)) % 10000}"
        
        batch_results = {
            'batch_id': batch_id,
            'total_notifications': len(notifications),
            'successful_deliveries': 0,
            'failed_deliveries': 0,
            'delivery_results': [],
            'started_at': datetime.utcnow().isoformat(),
            'completed_at': None
        }
        
        # Log batch start
        if user_id:
            self.audit_service.create_log_entry(
                user_id=user_id,
                event_type="notification_batch_delivery_start",
                event_description=f"Starting batch delivery of {len(notifications)} notifications",
                input_data={'batch_id': batch_id, 'notification_count': len(notifications)}
            )
        
        # Deliver each notification
        for notification in notifications:
            try:
                result = self.deliver_notification(notification, user_id=user_id)
                batch_results['delivery_results'].append(result)
                
                if result.get('status') in [DeliveryStatus.SENT.value, DeliveryStatus.DELIVERED.value]:
                    batch_results['successful_deliveries'] += 1
                else:
                    batch_results['failed_deliveries'] += 1
                    
            except Exception as e:
                logger.error(f"Error in batch delivery for notification {notification.get('policy_id', 'unknown')}: {str(e)}")
                batch_results['failed_deliveries'] += 1
                batch_results['delivery_results'].append({
                    'notification_id': notification.get('policy_id', 'unknown'),
                    'status': DeliveryStatus.FAILED.value,
                    'error_message': str(e)
                })
        
        batch_results['completed_at'] = datetime.utcnow().isoformat()
        
        # Log batch completion
        if user_id:
            self.audit_service.create_log_entry(
                user_id=user_id,
                event_type="notification_batch_delivery_complete",
                event_description=f"Batch delivery complete: {batch_results['successful_deliveries']} successful, {batch_results['failed_deliveries']} failed",
                input_data={'batch_id': batch_id},
                output_data=batch_results,
                status="success" if batch_results['failed_deliveries'] == 0 else "partial_success"
            )
        
        return batch_results
    
    def get_delivery_status(self, notification_id: str) -> Optional[Dict[str, Any]]:
        """
        Get delivery status for a specific notification
        
        Args:
            notification_id: ID of the notification
            
        Returns:
            Dictionary containing delivery status or None if not found
        """
        return self.delivery_status.get(notification_id)
    
    def get_pending_retries(self) -> List[Dict[str, Any]]:
        """
        Get list of notifications pending retry
        
        Returns:
            List of notification records that need retry
        """
        pending_retries = []
        current_time = datetime.utcnow()
        
        for notification_id, record in self.delivery_status.items():
            if (record['status'] == DeliveryStatus.RETRY.value and 
                record.get('next_retry') and
                datetime.fromisoformat(record['next_retry']) <= current_time):
                pending_retries.append(record)
        
        return pending_retries
    
    def process_retry_queue(self, user_id: str = None) -> Dict[str, Any]:
        """
        Process notifications that are ready for retry
        
        Args:
            user_id: User ID for audit logging
            
        Returns:
            Dictionary containing retry processing results
        """
        pending_retries = self.get_pending_retries()
        
        if not pending_retries:
            return {
                'processed_retries': 0,
                'successful_retries': 0,
                'failed_retries': 0,
                'results': []
            }
        
        retry_results = {
            'processed_retries': len(pending_retries),
            'successful_retries': 0,
            'failed_retries': 0,
            'results': []
        }
        
        for retry_record in pending_retries:
            notification_id = retry_record['notification_id']
            
            try:
                # Get original notification (this would come from database in real implementation)
                # For now, we'll create a minimal notification for retry
                notification = {
                    'policy_id': notification_id,
                    'platform': retry_record['platform'],
                    'delivery_method': retry_record['delivery_method'],
                    'subject': f"Retry: Death Notification for {retry_record['platform']}",
                    'body': "This is a retry of a previously failed notification."
                }
                
                result = self.deliver_notification(notification, user_id=user_id)
                retry_results['results'].append(result)
                
                if result.get('status') in [DeliveryStatus.SENT.value, DeliveryStatus.DELIVERED.value]:
                    retry_results['successful_retries'] += 1
                else:
                    retry_results['failed_retries'] += 1
                    
            except Exception as e:
                logger.error(f"Error processing retry for notification {notification_id}: {str(e)}")
                retry_results['failed_retries'] += 1
                retry_results['results'].append({
                    'notification_id': notification_id,
                    'status': DeliveryStatus.FAILED.value,
                    'error_message': str(e)
                })
        
        return retry_results
    
    def update_delivery_status(self, notification_id: str, status: str, 
                             details: Dict[str, Any] = None) -> bool:
        """
        Update delivery status for a notification
        
        Args:
            notification_id: ID of the notification
            status: New status value
            details: Additional details to update
            
        Returns:
            Boolean indicating success
        """
        if notification_id not in self.delivery_status:
            return False
        
        self.delivery_status[notification_id]['status'] = status
        self.delivery_status[notification_id]['updated_at'] = datetime.utcnow().isoformat()
        
        if details:
            self.delivery_status[notification_id]['delivery_details'].update(details)
        
        return True
    
    def get_delivery_statistics(self) -> Dict[str, Any]:
        """
        Get delivery statistics across all notifications
        
        Returns:
            Dictionary containing delivery statistics
        """
        stats = {
            'total_notifications': len(self.delivery_status),
            'status_counts': {},
            'platform_counts': {},
            'method_counts': {},
            'success_rate': 0.0
        }
        
        successful_count = 0
        
        for record in self.delivery_status.values():
            status = record['status']
            platform = record['platform']
            method = record['delivery_method']
            
            # Count by status
            stats['status_counts'][status] = stats['status_counts'].get(status, 0) + 1
            
            # Count by platform
            stats['platform_counts'][platform] = stats['platform_counts'].get(platform, 0) + 1
            
            # Count by method
            stats['method_counts'][method] = stats['method_counts'].get(method, 0) + 1
            
            # Count successful deliveries
            if status in [DeliveryStatus.SENT.value, DeliveryStatus.DELIVERED.value]:
                successful_count += 1
        
        # Calculate success rate
        if stats['total_notifications'] > 0:
            stats['success_rate'] = successful_count / stats['total_notifications']
        
        return stats