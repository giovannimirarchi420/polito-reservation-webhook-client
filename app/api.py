"""
Webhook API endpoints for handling reservation events.

This module provides FastAPI router with endpoints for processing webhook events
related to resource provisioning and deprovisioning.
"""
from typing import Optional, List

from fastapi import APIRouter, Request, Header, HTTPException, status
from fastapi.responses import JSONResponse

from . import config, models
from .services import security, kubernetes

logger = config.logger
router = APIRouter()

# Constants for event types
EVENT_START = 'EVENT_START'
EVENT_END = 'EVENT_END'


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
    webhook_secret_value = config.WEBHOOK_SECRET # Changed from config.settings.webhook_secret
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

def _post_batch_provision_actions(events: List[models.Event], user_info: dict) -> None:
    """
    Perform actions after all resources in a batch have been provisioned.
    This is a placeholder for custom logic, e.g., setting up networking,
    shared storage, or notifying a user/system.
    """
    logger.info(f"Executing post-batch provision actions for user {user_info.get('username')}, {len(events)} resources.")
    # Example: Log the resources that were provisioned
    for event in events:
        logger.info(f"  Post-provision check for: {event.resource_name} (Event ID: {event.event_id})")
    # Add your custom logic here
    # This could involve:
    # - Configuring network policies between the provisioned resources
    # - Setting up shared file systems or databases
    # - Sending a notification that the batch of resources is ready
    # - Triggering a subsequent workflow
    logger.info("Post-batch provision actions placeholder completed.")


def _handle_provision_event(resource_name: str, ssh_public_key: Optional[str], event_id: Optional[str] = None) -> bool:
    """
    Handle provisioning event for a single resource. Returns True on success.
    """
    logger.info(
        f"[{EVENT_START}] Processing event for resource '{resource_name}' (Event ID: {event_id}). "
        f"Attempting to provision with image '{config.PROVISION_IMAGE}'."
    )
    
    success = kubernetes.patch_baremetalhost(
        bmh_name=resource_name,
        image_url=config.PROVISION_IMAGE,
        ssh_key=ssh_public_key,
        checksum=config.PROVISION_CHECKSUM,
        checksum_type=config.PROVISION_CHECKSUM_TYPE
    )
    
    if success:
        logger.info(f"[{EVENT_START}] Successfully initiated provisioning for resource '{resource_name}' (Event ID: {event_id}).")
        return True
    else:
        logger.error(f"[{EVENT_START}] Failed provisioning for resource '{resource_name}' (Event ID: {event_id}).")
        return False


def _handle_deprovision_event(resource_name: str, event_id: Optional[str] = None) -> bool:
    """
    Handle deprovisioning event for a single resource. Returns True on success.
    """
    deprovision_target = config.DEPROVISION_IMAGE if config.DEPROVISION_IMAGE else None
    logger.info(
        f"[{EVENT_END}] Processing event for resource '{resource_name}' (Event ID: {event_id}). "
        f"Attempting to deprovision with target '{deprovision_target}'."
    )
    
    success = kubernetes.patch_baremetalhost(resource_name, deprovision_target)
    
    if success:
        logger.info(f"[{EVENT_END}] Successfully initiated deprovisioning for resource '{resource_name}' (Event ID: {event_id}).")
        return True
    else:
        logger.error(f"[{EVENT_END}] Failed deprovisioning for resource '{resource_name}' (Event ID: {event_id}).")
        return False

@router.post("/webhook")
async def handle_webhook(
    payload: models.WebhookPayload, # Now directly uses the unified WebhookPayload
    request: Request, 
    x_webhook_signature: Optional[str] = Header(None)
) -> JSONResponse:
    """
    Handle incoming webhook events for resource provisioning/deprovisioning.
    Always expects a list of events in the payload.
    """
    logger.info(f"Received webhook request. Attempting to parse payload.")
    
    raw_payload = await _verify_webhook_signature(request, x_webhook_signature)
    
    # Log based on the unified payload structure
    logger.info(
        f"Processing webhook. Event Type: '{payload.event_type}', "
        f"User: '{payload.username}', Event Count: {payload.event_count}."
        f" Raw payload snippet: {raw_payload[:200]}"
    )
        
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
        # Or raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No events provided in payload.")
        return _create_batch_success_response(payload.event_type.lower(), 0, payload.user_id) # Or an error response

    if payload.event_type == EVENT_START:
        successful_provision_events = []
        for event in payload.events:
            if _handle_provision_event(event.resource_name, payload.ssh_public_key, event.event_id):
                processed_events_count += 1
                successful_provision_events.append(event)
            else:
                failed_event_details.append({"event_id": event.event_id, "resource_name": event.resource_name, "action": "provision"})
        
        if successful_provision_events: # Only call if at least one succeeded
             _post_batch_provision_actions(successful_provision_events, user_info)

    elif payload.event_type == EVENT_END:
        for event in payload.events:
            if _handle_deprovision_event(event.resource_name, event.event_id):
                processed_events_count += 1
            else:
                failed_event_details.append({"event_id": event.event_id, "resource_name": event.resource_name, "action": "deprovision"})
    else:
        # Handle unknown event type for the entire payload
        logger.warning(f"Received unknown event type '{payload.event_type}' for user {payload.username}.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown event type: '{payload.event_type}'"
        )

    if failed_event_details:
        logger.error(f"Webhook processing for user {payload.username} (Event Type: {payload.event_type}) encountered {len(failed_event_details)} failures out of {payload.event_count} events.")
        # Respond with an error if any event failed, detailing the failures.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing for event type '{payload.event_type}' failed for {len(failed_event_details)} out of {payload.event_count} events. Failures: {failed_event_details}"
        )
    
    # If all events (if any) were processed successfully
    return _create_batch_success_response(payload.event_type.lower(), processed_events_count, payload.user_id)

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
