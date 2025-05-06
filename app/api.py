from fastapi import APIRouter, Request, Header, HTTPException, status
from fastapi.responses import JSONResponse

from . import config, models # Relative imports
from .services import security, kubernetes # Relative imports

router = APIRouter()

@router.post("/webhook")
async def handle_webhook(payload: models.EventWebhookPayload, request: Request, x_webhook_signature: str | None = Header(None)):
    print("Webhook received request.", flush=True)

    # Read raw body for signature verification
    payload_raw = await request.body()

    # Verify signature
    if not security.verify_signature(payload_raw, x_webhook_signature):
        print("Signature verification failed.", flush=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Signature verification failed"
        )

    print(f"Received verified payload: {payload.dict(by_alias=True)}", flush=True)

    resource_name = payload.resource_name

    if payload.event_type == 'EVENT_START':
        print(f"Processing EVENT_START for resource: {resource_name}", flush=True)
        success = kubernetes.patch_baremetalhost(resource_name, config.PROVISION_IMAGE)
        if success:
            return JSONResponse({"status": "success", "message": f"Provisioning initiated for {resource_name}"})
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to initiate provisioning for {resource_name}"
            )

    elif payload.event_type == 'EVENT_END':
        print(f"Processing EVENT_END for resource: {resource_name}", flush=True)
        # Use DEPROVISION_IMAGE if set, otherwise pass None to clear the image field
        deprovision_target = config.DEPROVISION_IMAGE if config.DEPROVISION_IMAGE else None
        success = kubernetes.patch_baremetalhost(resource_name, deprovision_target)
        if success:
            return JSONResponse({"status": "success", "message": f"Deprovisioning initiated for {resource_name}"})
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to initiate deprovisioning for {resource_name}"
            )

    else:
        print(f"Ignoring unknown event type: {payload.event_type}", flush=True)
        return JSONResponse({"status": "ignored", "message": f"Event type '{payload.event_type}' not handled"}, status_code=200)

# Health check endpoint (optional but recommended)
@router.get("/healthz")
def health_check():
    return {"status": "ok"}
