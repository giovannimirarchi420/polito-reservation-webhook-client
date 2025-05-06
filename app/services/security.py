import hmac
import hashlib
import base64
from .. import config # Use relative import for config

def verify_signature(payload_body, signature_header):
    """Verify the webhook signature if a secret is configured."""
    if not config.WEBHOOK_SECRET:
        print("Webhook secret not configured. Skipping signature verification.")
        return True # No secret, no verification needed

    if not signature_header:
        print("Missing X-Webhook-Signature header.")
        return False

    try:
        hash_object = hmac.new(config.WEBHOOK_SECRET.encode('utf-8'), msg=payload_body, digestmod=hashlib.sha256)
        expected_signature = base64.b64encode(hash_object.digest()).decode('utf-8')

        print(f"Received Signature: {signature_header}")
        print(f"Expected Signature: {expected_signature}")

        if hmac.compare_digest(signature_header, expected_signature):
            print("Signature verified successfully.")
            return True
        else:
            print("Signature verification failed.")
            return False
    except Exception as e:
        print(f"Error during signature verification: {e}", flush=True)
        return False
