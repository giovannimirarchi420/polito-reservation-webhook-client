import hmac
import hashlib
import base64
from .. import config # Use relative import for config

# Get the logger from config
logger = config.logger

def verify_signature(payload_body, signature_header):
    """Verify the webhook signature if a secret is configured."""
    if not config.WEBHOOK_SECRET:
        logger.info("Webhook secret not configured. Skipping signature verification.")
        return True # No secret, no verification needed

    if not signature_header:
        logger.warning("Missing X-Webhook-Signature header.")
        return False

    try:
        hash_object = hmac.new(config.WEBHOOK_SECRET.encode('utf-8'), msg=payload_body, digestmod=hashlib.sha256)
        expected_signature = base64.b64encode(hash_object.digest()).decode('utf-8')

        logger.debug(f"Received Signature: {signature_header}")
        logger.debug(f"Expected Signature: {expected_signature}")

        if hmac.compare_digest(signature_header, expected_signature):
            logger.info("Signature verified successfully.")
            return True
        else:
            logger.warning("Signature verification failed.")
            return False
    except Exception as e:
        logger.error(f"Error during signature verification: {e}")
        return False
