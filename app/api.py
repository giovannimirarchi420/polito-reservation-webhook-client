from fastapi import APIRouter, Request, Header, HTTPException, status
from fastapi.responses import JSONResponse

from . import config, models # Relative imports
from .services import security, kubernetes # Relative imports

# Get the logger from config
logger = config.logger

router = APIRouter()

@router.post("/webhook")
async def handle_webhook(payload: models.EventWebhookPayload, request: Request, x_webhook_signature: str | None = Header(None)):
    logger.info(f"Request Payload: {payload.model_dump_json(by_alias=True)}") # Log request payload

    # Read raw body for signature verification
    payload_raw = await request.body()

    # Verify signature
    if not security.verify_signature(payload_raw, x_webhook_signature):
        logger.warning("Webhook signature verification failed.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Signature verification failed"
        )

    logger.info(f"Webhook signature verified. Event Type: '{payload.event_type}', Resource Name: '{payload.resource_name}'.")

    resource_name = payload.resource_name

    if payload.event_type == 'EVENT_START':
        logger.info(f"[EVENT_START] Processing event for resource '{resource_name}'. Attempting to provision with image '{config.PROVISION_IMAGE}'.")
        success = kubernetes.patch_baremetalhost(resource_name, config.PROVISION_IMAGE)
        if success:
            logger.info(f"[EVENT_START] Successfully initiated provisioning for resource '{resource_name}'.")
            response_data = {"status": "success", "message": f"Provisioning initiated for {resource_name}"}
            logger.debug(f"Response data: {response_data}") # Log response
            return JSONResponse(response_data)
        else:
            logger.error(f"[EVENT_START] Failed to initiate provisioning for resource '{resource_name}' with image '{config.PROVISION_IMAGE}'.")
            # Log error response before raising HTTPException
            error_response_data = {"detail": f"Failed to initiate provisioning for {resource_name}"}
            logger.debug(f"Error response data: {error_response_data}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to initiate provisioning for {resource_name}"
            )

    elif payload.event_type == 'EVENT_END':
        deprovision_target = config.DEPROVISION_IMAGE if config.DEPROVISION_IMAGE else None
        logger.info(f"[EVENT_END] Processing event for resource '{resource_name}'. Attempting to deprovision with target '{deprovision_target}'.")
        success = kubernetes.patch_baremetalhost(resource_name, deprovision_target)
        if success:
            logger.info(f"[EVENT_END] Successfully initiated deprovisioning for resource '{resource_name}'.")
            response_data = {"status": "success", "message": f"Deprovisioning initiated for {resource_name}"}
            logger.debug(f"Response data: {response_data}") # Log response
            return JSONResponse(response_data)
        else:
            logger.error(f"[EVENT_END] Failed to initiate deprovisioning for resource '{resource_name}' with target '{deprovision_target}'.")
            # Log error response before raising HTTPException
            error_response_data = {"detail": f"Failed to initiate deprovisioning for {resource_name}"}
            logger.debug(f"Error response data: {error_response_data}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to initiate deprovisioning for {resource_name}"
            )

    else:
        logger.warning(f"[UNKNOWN_EVENT] Received unhandled event type '{payload.event_type}' for resource '{payload.resource_name}'. Ignoring.")
        response_data = {"status": "ignored", "message": f"Event type '{payload.event_type}' not handled"}
        logger.debug(f"Response data: {response_data}") # Log response
        return JSONResponse(response_data, status_code=200)

# Health check endpoint (optional but recommended)
@router.get("/healthz")
def health_check():
    response_data = {"status": "ok"}
    logger.debug(f"Health check response: {response_data}") # Log health check response
    return response_data
