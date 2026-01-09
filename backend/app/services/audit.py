"""
Audit Service - Tamper-proof logging for all system actions
Provides hash-based tamper detection and automatic logging for database state changes
"""
from app import db
from app.models.audit_log import AuditLog
from app.services.database import DatabaseService
from sqlalchemy import event
from sqlalchemy.orm import Session
from datetime import datetime
import hashlib
import json
import logging
from typing import Dict, Any, Optional, List
import uuid

logger = logging.getLogger(__name__)

class AuditService:
    """Service for creating and managing tamper-proof audit logs"""
    
    @staticmethod
    def create_log_entry(user_id: str, event_type: str, event_description: str,
                        ai_service_used: Optional[str] = None,
                        input_data: Optional[Dict[str, Any]] = None,
                        output_data: Optional[Dict[str, Any]] = None,
                        status: str = 'success') -> Optional[AuditLog]:
        """
        Create a new audit log entry with tamper-proof hash signature
        
        Args:
            user_id: ID of the user associated with this event
            event_type: Type of event (e.g., 'user_created', 'asset_added', 'policy_executed')
            event_description: Human-readable description of the event
            ai_service_used: Name of AI service used ('azure_vision', 'azure_openai', or None)
            input_data: Dictionary of input data for the operation
            output_data: Dictionary of output data from the operation
            status: Status of the operation ('success', 'failure', 'pending')
            
        Returns:
            Created AuditLog instance or None if creation failed
        """
        try:
            # Convert data dictionaries to JSON strings
            input_json = json.dumps(input_data, sort_keys=True) if input_data else None
            output_json = json.dumps(output_data, sort_keys=True) if output_data else None
            
            # Create audit log entry without hash first
            audit_log = AuditLog(
                user_id=user_id,
                event_type=event_type,
                event_description=event_description,
                ai_service_used=ai_service_used,
                input_data=input_json,
                output_data=output_json,
                status=status
            )
            
            # Save to database first
            if DatabaseService.safe_add(audit_log):
                # Now generate and update the hash
                audit_log.hash_signature = audit_log._generate_hash()
                if DatabaseService.safe_update(audit_log, hash_signature=audit_log.hash_signature):
                    logger.info(f"Audit log created: {event_type} for user {user_id}")
                    return audit_log
                else:
                    logger.error(f"Failed to update hash for audit log: {event_type}")
                    return audit_log  # Return anyway, hash can be generated later
            else:
                logger.error(f"Failed to save audit log: {event_type} for user {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating audit log entry: {str(e)}")
            return None
    
    @staticmethod
    def verify_log_integrity(log_id: str) -> bool:
        """
        Verify the integrity of a specific audit log entry
        
        Args:
            log_id: ID of the audit log to verify
            
        Returns:
            True if log is intact, False if tampered or not found
        """
        try:
            audit_log = DatabaseService.get_by_id(AuditLog, log_id)
            if not audit_log:
                logger.warning(f"Audit log not found: {log_id}")
                return False
            
            return audit_log.verify_integrity()
            
        except Exception as e:
            logger.error(f"Error verifying log integrity: {str(e)}")
            return False
    
    @staticmethod
    def verify_all_logs_integrity(user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Verify integrity of all audit logs or logs for a specific user
        
        Args:
            user_id: Optional user ID to filter logs, if None checks all logs
            
        Returns:
            Dictionary with verification results
        """
        try:
            # Get logs to verify
            if user_id:
                logs = DatabaseService.get_all(AuditLog, user_id=user_id)
            else:
                logs = DatabaseService.get_all(AuditLog)
            
            total_logs = len(logs)
            valid_logs = 0
            invalid_logs = []
            
            for log in logs:
                if log.verify_integrity():
                    valid_logs += 1
                else:
                    invalid_logs.append({
                        'log_id': log.log_id,
                        'event_type': log.event_type,
                        'timestamp': log.timestamp.isoformat() if log.timestamp else None,
                        'user_id': log.user_id
                    })
            
            return {
                'total_logs': total_logs,
                'valid_logs': valid_logs,
                'invalid_logs': len(invalid_logs),
                'integrity_percentage': (valid_logs / total_logs * 100) if total_logs > 0 else 100,
                'tampered_logs': invalid_logs
            }
            
        except Exception as e:
            logger.error(f"Error verifying logs integrity: {str(e)}")
            return {
                'total_logs': 0,
                'valid_logs': 0,
                'invalid_logs': 0,
                'integrity_percentage': 0,
                'tampered_logs': [],
                'error': str(e)
            }
    
    @staticmethod
    def get_audit_trail(user_id: str, event_type: Optional[str] = None,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get audit trail for a user with optional filtering
        
        Args:
            user_id: ID of the user to get audit trail for
            event_type: Optional event type filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            List of audit log entries as dictionaries
        """
        try:
            # Build query
            query = AuditLog.query.filter(AuditLog.user_id == user_id)
            
            if event_type:
                query = query.filter(AuditLog.event_type == event_type)
            
            if start_date:
                query = query.filter(AuditLog.timestamp >= start_date)
            
            if end_date:
                query = query.filter(AuditLog.timestamp <= end_date)
            
            # Order by timestamp descending (most recent first)
            logs = query.order_by(AuditLog.timestamp.desc()).all()
            
            # Convert to dictionaries and include integrity status
            audit_trail = []
            for log in logs:
                log_dict = log.to_dict()
                log_dict['integrity_verified'] = log.verify_integrity()
                audit_trail.append(log_dict)
            
            return audit_trail
            
        except Exception as e:
            logger.error(f"Error getting audit trail: {str(e)}")
            return []
    
    @staticmethod
    def log_user_action(user_id: str, action: str, details: Dict[str, Any],
                       status: str = 'success') -> Optional[AuditLog]:
        """
        Convenience method to log user actions
        
        Args:
            user_id: ID of the user performing the action
            action: Action being performed
            details: Dictionary with action details
            status: Status of the action
            
        Returns:
            Created AuditLog instance or None
        """
        return AuditService.create_log_entry(
            user_id=user_id,
            event_type=f'user_action_{action}',
            event_description=f'User performed action: {action}',
            input_data=details,
            status=status
        )
    
    @staticmethod
    def log_ai_service_call(user_id: str, service_name: str, operation: str,
                           input_data: Dict[str, Any], output_data: Dict[str, Any],
                           status: str = 'success') -> Optional[AuditLog]:
        """
        Convenience method to log AI service calls
        
        Args:
            user_id: ID of the user associated with the AI service call
            service_name: Name of the AI service ('azure_vision' or 'azure_openai')
            operation: Operation performed (e.g., 'ocr_extraction', 'policy_interpretation')
            input_data: Input data sent to the AI service
            output_data: Output data received from the AI service
            status: Status of the operation
            
        Returns:
            Created AuditLog instance or None
        """
        return AuditService.create_log_entry(
            user_id=user_id,
            event_type=f'ai_service_{operation}',
            event_description=f'AI service call: {service_name} - {operation}',
            ai_service_used=service_name,
            input_data=input_data,
            output_data=output_data,
            status=status
        )
    
    @staticmethod
    def log_database_change(user_id: str, table_name: str, operation: str,
                           record_id: str, changes: Dict[str, Any]) -> Optional[AuditLog]:
        """
        Convenience method to log database state changes
        
        Args:
            user_id: ID of the user associated with the change
            table_name: Name of the database table
            operation: Type of operation ('insert', 'update', 'delete')
            record_id: ID of the affected record
            changes: Dictionary describing the changes made
            
        Returns:
            Created AuditLog instance or None
        """
        return AuditService.create_log_entry(
            user_id=user_id,
            event_type=f'database_{operation}',
            event_description=f'Database {operation} on {table_name} record {record_id}',
            input_data={
                'table_name': table_name,
                'record_id': record_id,
                'operation': operation,
                'changes': changes
            },
            status='success'
        )

# Database event listeners for automatic logging
class DatabaseChangeLogger:
    """Automatic logging of database state changes using SQLAlchemy events"""
    
    @staticmethod
    def setup_automatic_logging():
        """Set up automatic logging for all database state changes"""
        
        # Listen for after_insert events
        @event.listens_for(Session, 'after_insert')
        def log_insert(mapper, connection, target):
            try:
                if hasattr(target, 'user_id') and target.user_id:
                    table_name = target.__tablename__
                    record_id = getattr(target, 'user_id', 'unknown')
                    
                    # Get primary key if available
                    if hasattr(target, '__table__'):
                        pk_columns = target.__table__.primary_key.columns.keys()
                        if pk_columns:
                            record_id = getattr(target, pk_columns[0], record_id)
                    
                    AuditService.log_database_change(
                        user_id=target.user_id,
                        table_name=table_name,
                        operation='insert',
                        record_id=str(record_id),
                        changes={'action': 'record_created'}
                    )
            except Exception as e:
                logger.error(f"Error in automatic insert logging: {str(e)}")
        
        # Listen for after_update events
        @event.listens_for(Session, 'after_update')
        def log_update(mapper, connection, target):
            try:
                if hasattr(target, 'user_id') and target.user_id:
                    table_name = target.__tablename__
                    record_id = getattr(target, 'user_id', 'unknown')
                    
                    # Get primary key if available
                    if hasattr(target, '__table__'):
                        pk_columns = target.__table__.primary_key.columns.keys()
                        if pk_columns:
                            record_id = getattr(target, pk_columns[0], record_id)
                    
                    # Get changed attributes
                    changes = {}
                    if hasattr(target, '__dict__'):
                        for attr in target.__dict__:
                            if not attr.startswith('_'):
                                changes[attr] = str(getattr(target, attr, ''))
                    
                    AuditService.log_database_change(
                        user_id=target.user_id,
                        table_name=table_name,
                        operation='update',
                        record_id=str(record_id),
                        changes=changes
                    )
            except Exception as e:
                logger.error(f"Error in automatic update logging: {str(e)}")
        
        # Listen for after_delete events
        @event.listens_for(Session, 'after_delete')
        def log_delete(mapper, connection, target):
            try:
                if hasattr(target, 'user_id') and target.user_id:
                    table_name = target.__tablename__
                    record_id = getattr(target, 'user_id', 'unknown')
                    
                    # Get primary key if available
                    if hasattr(target, '__table__'):
                        pk_columns = target.__table__.primary_key.columns.keys()
                        if pk_columns:
                            record_id = getattr(target, pk_columns[0], record_id)
                    
                    AuditService.log_database_change(
                        user_id=target.user_id,
                        table_name=table_name,
                        operation='delete',
                        record_id=str(record_id),
                        changes={'action': 'record_deleted'}
                    )
            except Exception as e:
                logger.error(f"Error in automatic delete logging: {str(e)}")

# Initialize automatic logging when module is imported
DatabaseChangeLogger.setup_automatic_logging()