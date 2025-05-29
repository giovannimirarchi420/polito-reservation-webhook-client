"""
Webhook API endpoints for handling reservation events.

This module provides FastAPI router with endpoints for processing webhook events
related to resource provisioning and deprovisioning.
"""
from typing import Optional

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
    
    if not security.verify_signature(payload_raw, signature):
        logger.warning("Webhook signature verification failed.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Signature verification failed"
        )
    
    return payload_raw


def _create_success_response(resource_name: str, action: str) -> JSONResponse:
    """Create a standardized success response."""
    message = f"{action.capitalize()} initiated for {resource_name}"
    response_data = {"status": "success", "message": message}
    logger.debug(f"Response data: {response_data}")
    return JSONResponse(response_data)


def _raise_provisioning_error(resource_name: str, action: str) -> None:
    """Raise a standardized provisioning error."""
    error_message = f"Failed to initiate {action} for {resource_name}"
    logger.error(f"[{action.upper()}] {error_message}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=error_message
    )


def _handle_provision_event(resource_name: str, ssh_public_key: Optional[str]) -> JSONResponse:
    """
    Handle provisioning event for a resource.
    
    Args:
        resource_name: Name of the resource to provision
        ssh_public_key: SSH public key for the resource
        
    Returns:
        JSONResponse with operation result
        
    Raises:
        HTTPException: If provisioning fails
    """
    logger.info(
        f"[{EVENT_START}] Processing event for resource '{resource_name}'. "
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
        logger.info(f"[{EVENT_START}] Successfully initiated provisioning for resource '{resource_name}'.")
        return _create_success_response(resource_name, "provisioning")
    else:
        _raise_provisioning_error(resource_name, "provisioning")


def _handle_deprovision_event(resource_name: str) -> JSONResponse:
    """
    Handle deprovisioning event for a resource.
    
    Args:
        resource_name: Name of the resource to deprovision
        
    Returns:
        JSONResponse with operation result
        
    Raises:
        HTTPException: If deprovisioning fails
    """
    deprovision_target = config.DEPROVISION_IMAGE if config.DEPROVISION_IMAGE else None
    logger.info(
        f"[{EVENT_END}] Processing event for resource '{resource_name}'. "
        f"Attempting to deprovision with target '{deprovision_target}'."
    )
    
    success = kubernetes.patch_baremetalhost(resource_name, deprovision_target)
    
    if success:
        logger.info(f"[{EVENT_END}] Successfully initiated deprovisioning for resource '{resource_name}'.")
        return _create_success_response(resource_name, "deprovisioning")
    else:
        _raise_provisioning_error(resource_name, "deprovisioning")


def _handle_unknown_event(event_type: str, resource_name: str) -> JSONResponse:
    """
    Handle unknown event type.
    
    Args:
        event_type: The unknown event type
        resource_name: Name of the resource
        
    Returns:
        JSONResponse indicating the event was ignored
    """
    logger.warning(
        f"[UNKNOWN_EVENT] Received unhandled event type '{event_type}' "
        f"for resource '{resource_name}'. Ignoring."
    )
    response_data = {"status": "ignored", "message": f"Event type '{event_type}' not handled"}
    logger.debug(f"Response data: {response_data}")
    return JSONResponse(response_data, status_code=200)


@router.post("/webhook")
async def handle_webhook(
    payload: models.EventWebhookPayload, 
    request: Request, 
    x_webhook_signature: Optional[str] = Header(None)
) -> JSONResponse:
    """
    Handle incoming webhook events for resource provisioning/deprovisioning.
    
    Args:
        payload: Webhook payload containing event information
        request: FastAPI request object
        x_webhook_signature: Webhook signature for verification
        
    Returns:
        JSONResponse with operation result
        
    Raises:
        HTTPException: If signature verification or operation fails
    """
    logger.info(f"Request Payload: {payload.model_dump_json(by_alias=True)}")
    
    # Verify webhook signature
    await _verify_webhook_signature(request, x_webhook_signature)
    
    logger.info(
        f"Webhook signature verified. Event Type: '{payload.event_type}', "
        f"Resource Name: '{payload.resource_name}'."
    )
    
    # Route event to appropriate handler
    if payload.event_type == EVENT_START:
        return _handle_provision_event(payload.resource_name, payload.ssh_public_key)
    elif payload.event_type == EVENT_END:
        return _handle_deprovision_event(payload.resource_name)
    else:
        return _handle_unknown_event(payload.event_type, payload.resource_name)


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
