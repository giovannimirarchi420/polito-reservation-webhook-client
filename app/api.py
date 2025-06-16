"""
Webhook API endpoints for handling reservation events.

This module provides FastAPI router with endpoints for processing webhook events
related to resource provisioning and deprovisioning.
"""
from typing import Optional, List, Union # Added Union
from datetime import datetime # Added datetime
import uuid

from fastapi import APIRouter, Request, Header, HTTPException, status
from fastapi.responses import JSONResponse

from . import config, models
from .services import security, kubernetes, notification

logger = config.logger
router = APIRouter()

# Constants for event types
EVENT_START = 'EVENT_START'
EVENT_END = 'EVENT_END'
EVENT_DELETED = 'EVENT_DELETED' # Added EVENT_DELETED


async def _verify_webhook_signature(request: Request, signature: Optional[str]) -> bytes:
    """
    Verify webhook signature and return raw payload.
    
    Args:
        request: FastAPI request object
        signature: Webhook signature header
        
    Returns:
        Raw request body as bytes
        
    Raises:
        HTTPException: If signature verification fails
    """
    payload_raw = await request.body()
    
    # Use the WebhookSecurity class for signature verification
    webhook_secret_value = config.WEBHOOK_SECRET
    if webhook_secret_value:
        sec_service = security.WebhookSecurity(webhook_secret_value)
        if not sec_service.verify_signature(payload_raw, signature):
            logger.warning("Webhook signature verification failed.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, # Changed to 403
                detail="Invalid webhook signature"
            )
        logger.info("Webhook signature verified successfully.")
    else:
        logger.warning("Webhook secret not configured. Skipping signature verification.")
        # Allow requests if no secret is configured, or raise error based on policy
        # For now, allowing, consistent with previous direct call to security.verify_signature behavior
    
    return payload_raw


def _create_batch_success_response(action: str, count: int, user_id: Optional[str]) -> JSONResponse:
    """Create a standardized success response for batch operations."""
    user_str = f" for user {user_id}" if user_id else ""
    message = f"Batch {action} initiated for {count} events{user_str}."
    response_data = {"status": "success", "message": message}
    logger.debug(f"Response data: {response_data}")
    return JSONResponse(response_data)

def _post_batch_provision_actions(events: List[models.Event], user_info: dict, active_resources: Optional[List[models.Event]] = None) -> None:
    """
    Perform actions after all resources in a batch have been provisioned.
    This function configures network switch settings to create VLANs and 
    assign server ports for the batch of provisioned resources.
    """
    logger.info(f"Executing post-batch provision actions for user {user_info.get('username')}, {len(events)} new resources.")
    
    # Log the resources that were just provisioned
    for event in events:
        logger.info(f"  Post-provision check for NEW resource: {event.resource_name} (Event ID: {event.event_id})")
    
    # Log active resources if present (resources the user already had)
    if active_resources and len(active_resources) > 0:
        logger.info(f"  User also has {len(active_resources)} existing active resources:")
        for active_resource in active_resources:
            logger.info(f"    - ACTIVE resource: {active_resource.resource_name} (Event ID: {active_resource.event_id})")
    
    # Configure network switch for the batch of provisioned servers
    if config.NETWORK_CONFIG_ENABLED:
        try:
            from app.services.network import get_switch_manager
            
            # Extract resource names from events
            resource_names = [event.resource_name for event in events]
            resource_names.append(resource.resource_name for resource in active_resources)
            # Configure network switch
            switch_manager = get_switch_manager()
            success = switch_manager.configure_batch_network(resource_names, user_info)
            
            if success:
                logger.info(f"Successfully configured network switch for batch of {len(events)} resources")
            else:
                logger.error(f"Failed to configure network switch for batch of {len(events)} resources")
                
        except Exception as e:
            logger.error(f"Error during network configuration: {e}")
            # Don't raise the exception to avoid breaking the provisioning workflow
    else:
        logger.info("Network configuration is disabled (NETWORK_CONFIG_ENABLED=false)")
    
    logger.info("Post-batch provision actions completed.")


def _handle_provision_event(
    resource_name: str, 
    ssh_public_key: Optional[str], 
    webhook_id: str,
    user_id: str,
    event_id: Optional[str] = None
) -> bool:
    """
    Handle provisioning event for a single resource. Returns True on success.
    """
    logger.info(
        f"[{EVENT_START}] Processing event for resource '{resource_name}' (Event ID: {event_id}). "
        f"Attempting to provision with image '{config.PROVISION_IMAGE}'."
    )
    
    # Provision the BareMetalHost with asynchronous monitoring
    success = kubernetes.patch_baremetalhost(
        bmh_name=resource_name,
        image_url=config.PROVISION_IMAGE,
        ssh_key=ssh_public_key,
        checksum=config.PROVISION_CHECKSUM,
        checksum_type=config.PROVISION_CHECKSUM_TYPE,
        webhook_id=webhook_id,
        user_id=user_id,
        event_id=event_id,
        timeout=config.PROVISIONING_TIMEOUT
    )
    
    if not success:
        # Send immediate notification and webhook log if the provisioning failed to start
        if webhook_id and user_id:
            notification_sent = notification.send_provisioning_notification(
                webhook_id=webhook_id,
                user_id=user_id,
                resource_name=resource_name,
                success=False,
                error_message="Failed to start provisioning",
                event_id=event_id
            )
            if not notification_sent:
                logger.warning(f"Failed to send notification for resource '{resource_name}'")
            
            # Send webhook log for the failed provisioning attempt
            webhook_log_sent = notification.send_webhook_log(
                webhook_id=webhook_id,
                event_type=EVENT_START,
                success=False,
                status_code=500,
                response_message="Failed to start provisioning",
                retry_count=0,
                resource_name=resource_name,
                user_id=user_id,
                error_message="Failed to start provisioning",
                event_id=event_id
            )
            if not webhook_log_sent:
                logger.warning(f"Failed to send webhook log for resource '{resource_name}'")
    
    if success:
        # Send webhook log for successful provisioning initiation
        if webhook_id and user_id:
            webhook_log_sent = notification.send_webhook_log(
                webhook_id=webhook_id,
                event_type=EVENT_START,
                success=True,
                status_code=200,
                response_message="Provisioning initiated successfully",
                retry_count=0,
                resource_name=resource_name,
                user_id=user_id,
                error_message=None,
                event_id=event_id
            )
            if not webhook_log_sent:
                logger.warning(f"Failed to send webhook log for resource '{resource_name}'")
        
        logger.info(f"[{EVENT_START}] Successfully initiated provisioning for resource '{resource_name}' (Event ID: {event_id}). Monitoring in background.")
        return True
    else:
        logger.error(f"[{EVENT_START}] Failed to start provisioning for resource '{resource_name}' (Event ID: {event_id}).")
        return False


def _handle_deprovision_event(
    resource_name: str, 
    event_id: Optional[str] = None,
    webhook_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> bool:
    """
    Handle deprovisioning event for a single resource. Returns True on success.
    """
    deprovision_target = config.DEPROVISION_IMAGE if config.DEPROVISION_IMAGE else None
    # Modified logger to be more generic for use by EVENT_DELETED
    logger.info(
        f"Processing deprovision event for resource '{resource_name}' (Event ID: {event_id}). "
        f"Attempting to deprovision with target '{deprovision_target}'."
    )
    
    success = kubernetes.patch_baremetalhost(resource_name, deprovision_target)
    
    # Send webhook log if webhook_id is available
    if webhook_id:
        webhook_log_sent = notification.send_webhook_log(
            webhook_id=webhook_id,
            event_type=EVENT_END,
            success=success,
            status_code=200 if success else 500,
            response_message="Deprovisioning completed successfully" if success else "Deprovisioning failed",
            retry_count=0,
            resource_name=resource_name,
            user_id=user_id,
            error_message=None if success else "Failed to initiate deprovisioning",
            event_id=event_id
        )
        if not webhook_log_sent:
            logger.warning(f"Failed to send webhook log for resource '{resource_name}'")
    
    if success:
        logger.info(f"Successfully initiated deprovisioning for resource '{resource_name}' (Event ID: {event_id}).")
        return True
    else:
        logger.error(f"Failed deprovisioning for resource '{resource_name}' (Event ID: {event_id}).")
        return False

@router.post("/webhook")
async def handle_webhook(
    payload: Union[models.WebhookPayload, models.EventWebhookPayload], # Updated payload type
    request: Request, 
    x_webhook_signature: Optional[str] = Header(None)
) -> JSONResponse:
    """
    Handle incoming webhook events for resource provisioning/deprovisioning.
    Always expects a list of events in the payload for EVENT_START and EVENT_END.
    Expects a single data object for EVENT_DELETED.
    """
    logger.info(f"Received webhook request. Attempting to parse payload.")
    
    raw_payload = await _verify_webhook_signature(request, x_webhook_signature)
    
    # Log based on the payload structure
    if isinstance(payload, models.WebhookPayload):
        active_resources_count = len(payload.active_resources) if payload.active_resources else 0
        logger.info(
            f"Processing webhook. Event Type: '{payload.event_type}', "
            f"User: '{payload.username}', Event Count: {payload.event_count}, "
            f"Active Resources Count: {active_resources_count}."
            f" Raw payload snippet: {raw_payload}"
        )

        # Log active resources if present
        if payload.active_resources and len(payload.active_resources) > 0:
            logger.info(f"User '{payload.username}' has {len(payload.active_resources)} active resources:")
            for active_resource in payload.active_resources:
                logger.info(
                    f"  - Active Resource: '{active_resource.resource_name}' ({active_resource.resource_type}) "
                    f"Event: '{active_resource.event_title}' (until {active_resource.event_end})"
                )
        else:
            logger.info(f"User '{payload.username}' has no active resources at this time.")
            
        processed_events_count = 0
        failed_event_details = []
        
        user_info = {
            "userId": payload.user_id,
            "username": payload.username,
            "email": payload.email,
            "sshPublicKey": payload.ssh_public_key
        }

        if not payload.events:
            logger.warning("Received payload with no events listed.")
            return _create_batch_success_response(payload.event_type.lower(), 0, payload.user_id)

        if payload.event_type == EVENT_START:
            
            successful_provision_events = []
            for event in payload.events:
                if _handle_provision_event(
                    event.resource_name, 
                    payload.ssh_public_key, 
                    payload.webhook_id,
                    payload.user_id or "unknown",
                    event.event_id
                ):
                    processed_events_count += 1
                    successful_provision_events.append(event)
                else:
                    failed_event_details.append({"event_id": event.event_id, "resource_name": event.resource_name, "action": "provision"})
            
            if successful_provision_events:
                 _post_batch_provision_actions(successful_provision_events, user_info, payload.active_resources)

        elif payload.event_type == EVENT_END:
            for event in payload.events:
                if _handle_deprovision_event(
                    event.resource_name, 
                    event.event_id,
                    payload.webhook_id,
                    payload.user_id
                ):
                    processed_events_count += 1
                else:
                    failed_event_details.append({"event_id": event.event_id, "resource_name": event.resource_name, "action": "deprovision"})
        # Note: Unknown event type for WebhookPayload is handled further down
        
        if failed_event_details:
            logger.error(f"Webhook processing for user {payload.username} (Event Type: {payload.event_type}) encountered {len(failed_event_details)} failures out of {payload.event_count} events.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Processing for event type '{payload.event_type}' failed for {len(failed_event_details)} out of {payload.event_count} events. Failures: {failed_event_details}"
            )
        
        # If all events (if any) were processed successfully
        return _create_batch_success_response(payload.event_type.lower(), processed_events_count, payload.user_id)

    elif isinstance(payload, models.EventWebhookPayload):
        logger.info(
            f"Processing webhook. Event Type: '{payload.event_type}', "
            f"Webhook ID: '{payload.webhook_id}', Resource Name: '{payload.data.resource.name}'."
            f" Raw payload snippet: {raw_payload}"
        )
        if payload.event_type == EVENT_DELETED:
            now = payload.timestamp # Use timestamp from the payload
            
            # Ensure start and end times are offset-aware for comparison with offset-aware 'now'
            # Pydantic v2 automatically handles ISO 8601 strings to offset-aware datetimes
            reservation_start = payload.data.start
            reservation_end = payload.data.end

            logger.debug(f"Current time (UTC): {now}, Reservation Start: {reservation_start}, Reservation End: {reservation_end}")

            if reservation_start <= now < reservation_end:
                logger.info(f"Reservation for resource '{payload.data.resource.name}' is currently active. Initiating deprovision.")
                if _handle_deprovision_event(
                    payload.data.resource.name, 
                    event_id=str(payload.data.id),
                    webhook_id=payload.webhook_id,
                    user_id=payload.data.keycloakId if payload.data else None
                ):
                    logger.info(f"Successfully initiated deprovisioning for resource '{payload.data.resource.name}' due to EVENT_DELETED.")
                    return JSONResponse({
                        "status": "success", 
                        "message": f"Deprovisioning initiated for resource '{payload.data.resource.name}' due to active reservation deletion."
                    })
                else:
                    logger.error(f"Failed to initiate deprovisioning for resource '{payload.data.resource.name}' for EVENT_DELETED.")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to deprovision resource '{payload.data.resource.name}' after EVENT_DELETED."
                    )
            else:
                logger.info(f"Reservation for resource '{payload.data.resource.name}' is not currently active. No deprovision action taken for EVENT_DELETED. Start: {reservation_start}, End: {reservation_end}, Now: {now}")
                return JSONResponse({
                    "status": "success", # Or "no_action_needed"
                    "message": f"No deprovision action taken for resource '{payload.data.resource.name}' as reservation is not currently active."
                })
        else:
            return JSONResponse({
                "status": "success",
                "message": f"No action needed for event type '{payload.event_type}'."
            })
    else:
        # If event type is not recognized, return success with no action needed
        event_type_to_log = payload.event_type if hasattr(payload, 'event_type') else "unknown"
        username_to_log = payload.username if isinstance(payload, models.WebhookPayload) and hasattr(payload, 'username') else "N/A"
        
        logger.info(f"Received event type '{event_type_to_log}' for user {username_to_log}. No action configured for this event type.")
        return JSONResponse({
            "status": "success",
            "message": f"No action needed for event type '{event_type_to_log}'."
        })


@router.get("/healthz")
def health_check() -> dict:
    """
    Health check endpoint.
    
    Returns:
        Dict containing health status
    """
    response_data = {"status": "ok"}
    logger.debug(f"Health check response: {response_data}")
    return response_data
