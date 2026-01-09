"""
Tests for Notification Delivery Service
"""
import unittest
from unittest.mock import patch, MagicMock
import json
from datetime import datetime

from app.services.notification_delivery import NotificationDeliveryService, DeliveryStatus, DeliveryMethod
from app.services.notification_templates import NotificationTemplateService

class TestNotificationDeliveryService(unittest.TestCase):
    """Test cases for NotificationDeliveryService"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.service = NotificationDeliveryService()
        self.template_service = NotificationTemplateService()
        
        # Sample notification data
        self.sample_notification = {
            'policy_id': 'test-policy-123',
            'platform': 'google',
            'action_type': 'delete',
            'subject': 'Test Death Notification',
            'body': 'This is a test notification for account deletion.',
            'delivery_method': 'email',
            'account_identifier': 'test@gmail.com'
        }
        
        self.sample_user_info = {
            'full_name': 'John Doe',
            'date_of_death': '2024-01-01',
            'contact_name': 'Jane Doe',
            'contact_email': 'jane.doe@email.com',
            'relationship': 'Spouse'
        }
    
    def test_delivery_status_tracking(self):
        """Test that delivery status is properly tracked"""
        notification_id = 'test-notification-123'
        
        # Initially, status should not exist
        status = self.service.get_delivery_status(notification_id)
        self.assertIsNone(status)
        
        # Update status
        success = self.service.update_delivery_status(
            notification_id, 
            DeliveryStatus.SENT.value,
            {'test': 'details'}
        )
        self.assertFalse(success)  # Should fail because notification doesn't exist yet
    
    @patch('smtplib.SMTP')
    def test_email_delivery_success(self, mock_smtp):
        """Test successful email delivery"""
        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        # Configure environment variables for test
        with patch.dict('os.environ', {
            'SMTP_USERNAME': 'test@example.com',
            'SMTP_PASSWORD': 'testpass',
            'FROM_EMAIL': 'test@example.com'
        }):
            # Create new service instance with mocked environment
            service = NotificationDeliveryService()
            
            # Test email delivery
            result = service.deliver_notification(
                notification=self.sample_notification,
                delivery_method='email',
                user_id='test-user-123'
            )
            
            # Verify result
            self.assertEqual(result['status'], DeliveryStatus.SENT.value)
            self.assertIn('delivery_details', result)
            
            # Verify SMTP was called
            mock_smtp.assert_called_once()
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once()
            mock_server.sendmail.assert_called_once()
            mock_server.quit.assert_called_once()
    
    @patch('requests.Session.post')
    def test_api_delivery_success(self, mock_post):
        """Test successful API delivery"""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'message': 'success'}
        mock_response.content = b'{"message": "success"}'
        mock_post.return_value = mock_response
        
        # Test API delivery
        api_notification = self.sample_notification.copy()
        api_notification['delivery_method'] = 'api'
        
        result = self.service.deliver_notification(
            notification=api_notification,
            delivery_method='api',
            user_id='test-user-123'
        )
        
        # Verify result
        self.assertEqual(result['status'], DeliveryStatus.SENT.value)
        self.assertIn('delivery_details', result)
        
        # Verify API was called
        mock_post.assert_called_once()
    
    def test_batch_delivery(self):
        """Test batch notification delivery"""
        notifications = [
            self.sample_notification,
            {
                'policy_id': 'test-policy-456',
                'platform': 'facebook',
                'action_type': 'memorialize',
                'subject': 'Test Memorialization',
                'body': 'Test memorialization request.',
                'delivery_method': 'form'
            }
        ]
        
        with patch.object(self.service, 'deliver_notification') as mock_deliver:
            # Mock successful delivery
            mock_deliver.return_value = {
                'status': DeliveryStatus.SENT.value,
                'notification_id': 'test-123'
            }
            
            # Test batch delivery
            result = self.service.batch_deliver_notifications(
                notifications=notifications,
                user_id='test-user-123'
            )
            
            # Verify results
            self.assertEqual(result['total_notifications'], 2)
            self.assertEqual(result['successful_deliveries'], 2)
            self.assertEqual(result['failed_deliveries'], 0)
            self.assertEqual(len(result['delivery_results']), 2)
            
            # Verify deliver_notification was called for each notification
            self.assertEqual(mock_deliver.call_count, 2)
    
    def test_retry_logic(self):
        """Test retry logic for failed deliveries"""
        # Test getting pending retries (should be empty initially)
        pending = self.service.get_pending_retries()
        self.assertEqual(len(pending), 0)
        
        # Test processing empty retry queue
        result = self.service.process_retry_queue('test-user-123')
        self.assertEqual(result['processed_retries'], 0)
    
    def test_delivery_statistics(self):
        """Test delivery statistics calculation"""
        # Initially should have no statistics
        stats = self.service.get_delivery_statistics()
        self.assertEqual(stats['total_notifications'], 0)
        self.assertEqual(stats['success_rate'], 0.0)
        
        # Add some mock delivery records
        self.service.delivery_status['test-1'] = {
            'status': DeliveryStatus.SENT.value,
            'platform': 'google',
            'delivery_method': 'email'
        }
        self.service.delivery_status['test-2'] = {
            'status': DeliveryStatus.FAILED.value,
            'platform': 'facebook',
            'delivery_method': 'form'
        }
        
        # Check updated statistics
        stats = self.service.get_delivery_statistics()
        self.assertEqual(stats['total_notifications'], 2)
        self.assertEqual(stats['success_rate'], 0.5)
        self.assertEqual(stats['status_counts'][DeliveryStatus.SENT.value], 1)
        self.assertEqual(stats['status_counts'][DeliveryStatus.FAILED.value], 1)

class TestNotificationTemplateService(unittest.TestCase):
    """Test cases for NotificationTemplateService"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.service = NotificationTemplateService()
        
        self.sample_context = {
            'full_name': 'John Doe',
            'date_of_death': '2024-01-01',
            'account_identifier': 'john.doe@gmail.com',
            'contact_name': 'Jane Doe',
            'contact_email': 'jane.doe@email.com',
            'relationship': 'Spouse'
        }
    
    def test_get_builtin_template(self):
        """Test retrieving built-in templates"""
        # Test getting Google delete template
        template = self.service.get_template('google', 'delete', 'email')
        self.assertIsNotNone(template)
        self.assertIn('subject', template)
        self.assertIn('body', template)
        self.assertIn('required_docs', template)
        
        # Test getting Facebook memorialize template
        template = self.service.get_template('facebook', 'memorialize', 'form')
        self.assertIsNotNone(template)
        self.assertIn('form_url', template)
        
        # Test getting non-existent template (should fall back to generic)
        template = self.service.get_template('unknown_platform', 'delete', 'email')
        self.assertIsNotNone(template)  # Should get generic template
    
    def test_template_personalization(self):
        """Test template personalization with context data"""
        # Get a template
        template = self.service.get_template('google', 'delete', 'email')
        self.assertIsNotNone(template)
        
        # Personalize it
        personalized = self.service.personalize_template(template, self.sample_context)
        
        # Check that placeholders were replaced
        self.assertIn('John Doe', personalized['subject'])
        self.assertIn('John Doe', personalized['body'])
        self.assertIn('2024-01-01', personalized['body'])
        self.assertIn('jane.doe@email.com', personalized['body'])
        
        # Check metadata was added
        self.assertIn('personalized_at', personalized)
        self.assertIn('context_used', personalized)
    
    def test_generate_notification_from_template(self):
        """Test complete notification generation from template"""
        notification = self.service.generate_notification_from_template(
            platform='google',
            action_type='delete',
            context=self.sample_context,
            template_type='email'
        )
        
        self.assertIsNotNone(notification)
        self.assertEqual(notification['platform'], 'google')
        self.assertEqual(notification['action_type'], 'delete')
        self.assertIn('John Doe', notification['subject'])
        self.assertIn('John Doe', notification['body'])
        self.assertIn('required_documents', notification)
        self.assertIn('contact_information', notification)
        self.assertTrue(notification['template_used'])
    
    def test_custom_template_creation(self):
        """Test creating custom templates"""
        custom_template_data = {
            'subject': 'Custom Template - {full_name}',
            'body': 'This is a custom template for {platform_name} {action_type}. Contact: {contact_email}',
            'required_docs': ['death_certificate', 'custom_doc'],
            'delivery_method': 'email'
        }
        
        # Create custom template
        success = self.service.create_custom_template(
            platform='custom_platform',
            action_type='custom_action',
            template_type='email',
            template_data=custom_template_data,
            user_id='test-user-123'
        )
        
        self.assertTrue(success)
        
        # Retrieve and verify custom template
        template = self.service.get_template('custom_platform', 'custom_action', 'email')
        self.assertIsNotNone(template)
        self.assertEqual(template['subject'], custom_template_data['subject'])
        self.assertIn('created_at', template)
        self.assertEqual(template['created_by'], 'test-user-123')
    
    def test_template_validation(self):
        """Test template validation"""
        # Valid template
        valid_template = {
            'subject': 'Valid Template',
            'body': 'This template contains {full_name} and {date_of_death}',
            'delivery_method': 'email'
        }
        
        result = self.service.validate_template(valid_template)
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)
        
        # Invalid template (missing required fields)
        invalid_template = {
            'subject': 'Invalid Template'
            # Missing body
        }
        
        result = self.service.validate_template(invalid_template)
        self.assertFalse(result['valid'])
        self.assertGreater(len(result['errors']), 0)
        
        # Template with dangerous content
        dangerous_template = {
            'subject': 'Dangerous Template',
            'body': 'This contains <script>alert("xss")</script> dangerous content',
            'delivery_method': 'email'
        }
        
        result = self.service.validate_template(dangerous_template)
        self.assertFalse(result['valid'])
        self.assertIn('dangerous content', ' '.join(result['errors']).lower())
    
    def test_platform_requirements(self):
        """Test platform requirements retrieval"""
        # Test known platform
        reqs = self.service.get_platform_requirements('google')
        self.assertIn('required_docs', reqs)
        self.assertIn('contact_methods', reqs)
        self.assertIn('processing_time', reqs)
        self.assertIn('contact_info', reqs)
        
        # Test unknown platform (should get defaults)
        reqs = self.service.get_platform_requirements('unknown_platform')
        self.assertIn('required_docs', reqs)
        self.assertEqual(reqs['required_docs'], ['death_certificate'])
    
    def test_template_statistics(self):
        """Test template statistics"""
        stats = self.service.get_template_statistics()
        
        self.assertIn('total_builtin_templates', stats)
        self.assertIn('total_custom_templates', stats)
        self.assertIn('platforms_with_templates', stats)
        self.assertIn('action_types_supported', stats)
        self.assertIn('template_types_available', stats)
        
        # Should have some built-in templates
        self.assertGreater(stats['total_builtin_templates'], 0)
        self.assertIn('google', stats['platforms_with_templates'])
        self.assertIn('delete', stats['action_types_supported'])
        self.assertIn('email', stats['template_types_available'])

if __name__ == '__main__':
    unittest.main()