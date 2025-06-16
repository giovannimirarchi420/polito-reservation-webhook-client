"""
Notification service for sending status updates via webhooks.

This module provides functionality to send notifications about
BareMetalHost provisioning status to external endpoints.
"""
import json
from datetime import datetime, timezone
from typing import Dict, Optional, Any
import uuid

import requests

from .. import config
from .security import WebhookSecurity

logger = config.logger


class NotificationError(Exception):
    """Custom exception for notification operations."""
    pass


class NotificationService:
    """Service for sending notifications to external endpoints."""
    
    def __init__(self):
        self.endpoint = config.NOTIFICATION_ENDPOINT
        self.timeout = config.NOTIFICATION_TIMEOUT
        self.log_endpoint = config.WEBHOOK_LOG_ENDPOINT
        self.log_timeout = config.WEBHOOK_LOG_TIMEOUT
        self.security = WebhookSecurity()  # For generating signatures
    
    def _generate_event_id(self) -> str:
        """Generate a unique event ID."""
        return f"event-{uuid.uuid4()}"
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now(timezone.utc).isoformat()
    
    def _generate_signature(self, payload_bytes: bytes) -> Optional[str]:
        """
        Generate HMAC signature for the notification payload.
        
        Args:
            payload_bytes: Raw payload bytes
            
        Returns:
            HMAC signature string or None if no webhook secret is configured
        """
        try:
            return self.security._generate_signature(payload_bytes)
        except Exception as e:
            logger.warning(f"Failed to generate signature: {e}")
            return None
    
    def _create_notification_payload(
        self,
        webhook_id: str,
        user_id: str,
        resource_name: str,
        event_id: str,
        success: bool,
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create notification payload for BareMetalHost provisioning.
        
        Args:
            webhook_id: Webhook identifier
            user_id: User identifier
            resource_name: Name of the BareMetalHost resource
            event_id: Event identifier
            success: Whether provisioning was successful
            error_message: Error message if provisioning failed
            
        Returns:
            Notification payload dictionary
        """
        timestamp = self._get_current_timestamp()
        
        if success:
            message = (
                f"Your bare metal server reservation '{resource_name}' has been successfully "
                f"provisioned and will be available soon after the system boot completes. "
                f"This could take some minutes. You can login using SSH with the user 'prognose' "
                f"and your configured SSH key to the IP address specified in the resource specification."
            )
            notification_type = "SUCCESS"
            event_type = "PROVISIONING_COMPLETED"
        else:
            message = (
                f"Your bare metal server reservation '{resource_name}' provisioning failed. "
                f"Error: {error_message or 'Unknown error occurred'}"
            )
            notification_type = "ERROR"
            event_type = "PROVISIONING_FAILED"
        
        payload = {
            "webhookId": webhook_id,
            "userId": user_id,
            "message": message,
            "type": notification_type,
            "eventId": event_id,
            "resourceId": resource_name,
            "eventType": event_type,
            "metadata": {
                "resourceType": "BareMetalHost",
                "resourceName": resource_name,
                "timestamp": timestamp,
                "namespace": config.K8S_NAMESPACE
            }
        }
        
        if not success and error_message:
            payload["metadata"]["errorMessage"] = error_message
        
        return payload
    
    def _create_webhook_log_payload(
        self,
        webhook_id: str,
        event_type: str,
        success: bool,
        status_code: int = 200,
        response_message: str = "OK",
        retry_count: int = 0,
        resource_name: Optional[str] = None,
        user_id: Optional[str] = None,
        error_message: Optional[str] = None,
        event_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create webhook log payload for logging webhook events.
        
        Args:
            webhook_id: Webhook identifier
            event_type: Type of event (EVENT_START, EVENT_END)
            success: Whether the operation was successful
            status_code: HTTP status code
            response_message: Response message
            retry_count: Number of retry attempts
            resource_name: Name of the resource (optional)
            user_id: User identifier (optional)
            error_message: Error message if failed (optional)
            event_id: Event identifier (optional)
            
        Returns:
            Webhook log payload dictionary
        """
        # Create the original event payload that would have been sent to our webhook
        original_payload = {
            "eventType": event_type,
            "timestamp": self._get_current_timestamp(),
            "resourceName": resource_name or "unknown",
            "userId": user_id or "unknown"
        }
        
        if event_id:
            original_payload["eventId"] = event_id
        
        # Create the log payload according to the API specification
        log_payload = {
            "webhookId": webhook_id,
            "eventType": event_type,
            "payload": json.dumps(original_payload, separators=(',', ':')),  # Compact JSON string
            "statusCode": status_code,
            "response": response_message,
            "success": success,
            "retryCount": retry_count
        }
        
        # Add optional metadata
        metadata = {
            "resourceType": "BareMetalHost",
            "namespace": config.K8S_NAMESPACE,
            "timestamp": self._get_current_timestamp()
        }
        
        if resource_name:
            metadata["resourceName"] = resource_name
        if error_message:
            metadata["errorMessage"] = error_message
        if user_id:
            metadata["userId"] = user_id
        if event_id:
            metadata["eventId"] = event_id
            
        log_payload["metadata"] = metadata
        
        return log_payload
    
    def send_provisioning_notification(
        self,
        webhook_id: str,
        user_id: str,
        resource_name: str,
        success: bool,
        error_message: Optional[str] = None,
        event_id: Optional[str] = None
    ) -> bool:
        """
        Send a notification about BareMetalHost provisioning status.
        
        Args:
            webhook_id: Webhook identifier
            user_id: User identifier
            resource_name: Name of the BareMetalHost resource
            success: Whether provisioning was successful
            error_message: Error message if provisioning failed
            event_id: Event identifier (generated if not provided)
            
        Returns:
            True if notification was sent successfully, False otherwise
        """
        if not self.endpoint:
            logger.warning("NOTIFICATION_ENDPOINT not configured. Skipping notification.")
            return True
        
        event_id = event_id or self._generate_event_id()
        
        try:
            payload = self._create_notification_payload(
                webhook_id, user_id, resource_name, event_id, success, error_message
            )
            
            # Convert payload to JSON bytes for signature generation
            payload_json = json.dumps(payload, separators=(',', ':'))  # Compact JSON
            payload_bytes = payload_json.encode('utf-8')
            
            # Generate HMAC signature
            signature = self._generate_signature(payload_bytes)
            
            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "polito-reservation-webhook-client/1.0",
                "X-Webhook-Signature": signature
            }
                
            
            logger.info(
                f"Sending provisioning notification for resource '{resource_name}' "
                f"(success: {success}) to {self.endpoint}"
            )
            logger.debug(f"Notification payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                self.endpoint,
                data=payload_bytes,  # Use raw bytes to match signature
                timeout=self.timeout,
                headers=headers
            )
            
            response.raise_for_status()
            
            logger.info(
                f"Successfully sent notification for resource '{resource_name}' "
                f"(status: {response.status_code})"
            )
            return True
            
        except requests.exceptions.Timeout:
            logger.error(
                f"Timeout sending notification for resource '{resource_name}' "
                f"to {self.endpoint} (timeout: {self.timeout}s)"
            )
            return False
            
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Error sending notification for resource '{resource_name}' "
                f"to {self.endpoint}: {str(e)}"
            )
            return False
            
        except Exception as e:
            logger.error(
                f"Unexpected error sending notification for resource '{resource_name}': {str(e)}"
            )
            return False
        
    def send_webhook_log(
        self,
        webhook_id: str,
        event_type: str,
        success: bool,
        status_code: int = 200,
        response_message: str = "OK",
        retry_count: int = 0,
        resource_name: Optional[str] = None,
        user_id: Optional[str] = None,
        error_message: Optional[str] = None,
        event_id: Optional[str] = None
    ) -> bool:
        """
        Send webhook log to the central logging system.
        
        Args:
            webhook_id: Webhook identifier
            event_type: Type of event (EVENT_START, EVENT_END)
            success: Whether the operation was successful
            status_code: HTTP status code
            response_message: Response message
            retry_count: Number of retry attempts
            resource_name: Name of the resource (optional)
            user_id: User identifier (optional)
            error_message: Error message if failed (optional)
            event_id: Event identifier (optional)
            
        Returns:
            True if log was sent successfully, False otherwise
        """
        if not self.log_endpoint:
            logger.debug("WEBHOOK_LOG_ENDPOINT not configured. Skipping webhook log.")
            return True
        
        try:
            payload = self._create_webhook_log_payload(
                webhook_id=webhook_id,
                event_type=event_type,
                success=success,
                status_code=status_code,
                response_message=response_message,
                retry_count=retry_count,
                resource_name=resource_name,
                user_id=user_id,
                error_message=error_message,
                event_id=event_id
            )
            
            # Convert payload to JSON bytes for signature generation
            payload_json = json.dumps(payload, separators=(',', ':'))  # Compact JSON
            payload_bytes = payload_json.encode('utf-8')
            
            # Generate HMAC signature
            signature = self._generate_signature(payload_bytes)
            
            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "polito-reservation-webhook-client/1.0",
                "X-Webhook-Signature": signature
            }
            
            logger.debug(
                f"Sending webhook log for event '{event_type}' "
                f"(success: {success}, resource: {resource_name}) to {self.log_endpoint}"
            )
            logger.debug(f"Webhook log payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                self.log_endpoint,
                data=payload_bytes,  # Use raw bytes to match signature
                timeout=self.log_timeout,
                headers=headers
            )
            
            response.raise_for_status()
            
            logger.debug(
                f"Successfully sent webhook log for event '{event_type}' "
                f"(status: {response.status_code})"
            )
            return True
            
        except requests.exceptions.Timeout:
            logger.warning(
                f"Timeout sending webhook log for event '{event_type}' "
                f"to {self.log_endpoint} (timeout: {self.log_timeout}s)"
            )
            return False
            
        except requests.exceptions.RequestException as e:
            logger.warning(
                f"Error sending webhook log for event '{event_type}' "
                f"to {self.log_endpoint}: {str(e)}"
            )
            return False
            
        except Exception as e:
            logger.warning(
                f"Unexpected error sending webhook log for event '{event_type}': {str(e)}"
            )
            return False

# Singleton instance
_notification_service = NotificationService()


def send_provisioning_notification(
    webhook_id: str,
    user_id: str,
    resource_name: str,
    success: bool,
    error_message: Optional[str] = None,
    event_id: Optional[str] = None
) -> bool:
    """
    Send a notification about BareMetalHost provisioning status.
    
    This function provides a convenient interface to the notification service.
    
    Args:
        webhook_id: Webhook identifier
        user_id: User identifier
        resource_name: Name of the BareMetalHost resource
        success: Whether provisioning was successful
        error_message: Error message if provisioning failed
        event_id: Event identifier (generated if not provided)
        
    Returns:
        True if notification was sent successfully, False otherwise
    """
    return _notification_service.send_provisioning_notification(
        webhook_id, user_id, resource_name, success, error_message, event_id
    )


def send_webhook_log(
    webhook_id: str,
    event_type: str,
    success: bool,
    status_code: int = 200,
    response_message: str = "OK",
    retry_count: int = 0,
    resource_name: Optional[str] = None,
    user_id: Optional[str] = None,
    error_message: Optional[str] = None,
    event_id: Optional[str] = None
) -> bool:
    """
    Send webhook log to the central logging system.
    
    This function provides a convenient interface to the webhook log service.
    
    Args:
        webhook_id: Webhook identifier
        event_type: Type of event (EVENT_START, EVENT_END)
        success: Whether the operation was successful
        status_code: HTTP status code
        response_message: Response message
        retry_count: Number of retry attempts
        resource_name: Name of the resource (optional)
        user_id: User identifier (optional)
        error_message: Error message if failed (optional)
        event_id: Event identifier (optional)
        
    Returns:
        True if log was sent successfully, False otherwise
    """
    return _notification_service.send_webhook_log(
        webhook_id=webhook_id,
        event_type=event_type,
        success=success,
        status_code=status_code,
        response_message=response_message,
        retry_count=retry_count,
        resource_name=resource_name,
        user_id=user_id,
        error_message=error_message,
        event_id=event_id
    )
