import json
from kubernetes import client
from kubernetes.client.rest import ApiException
from .. import config # Use relative import for config

# Get the logger from config
logger = config.logger

METAL3_CR_NAME = "BareMetalHost"  # The name of the CRD for BareMetalHost

def patch_baremetalhost(bmh_name: str, image_url: str | None):
    """Patch the BareMetalHost CR with the specified image."""
    api = client.CustomObjectsApi()

    # Determine the patch based on whether an image_url is provided
    if image_url:
        patch = {
            "spec": {
                "image": {
                    "url": image_url,
                    # Add checksum and type if needed by your Metal3 setup
                    # "checksum": "...",
                    # "type": "..."
                }
            }
        }
    else: # Handle deprovisioning (clearing the image)
        patch = {
            "spec": {
                "image": None
            }
        }
        # Alternative: JSON Patch to remove the key if required by Metal3
        # patch = [{"op": "remove", "path": "/spec/image"}]

    try:
        logger.info(f"Attempting to patch BareMetalHost '{bmh_name}' in namespace '{config.K8S_NAMESPACE}' with image '{image_url}'.")
        api.patch_namespaced_custom_object(
            group=config.BMH_API_GROUP,
            version=config.BMH_API_VERSION,
            namespace=config.K8S_NAMESPACE,
            plural=config.BMH_PLURAL,
            name=bmh_name,
            body=patch
        )
        logger.info(f"Successfully patched BareMetalHost '{bmh_name}'.")
        return True
    except ApiException as e:
        logger.error(f"Error patching BareMetalHost '{bmh_name}': {e.reason} (Status: {e.status}). Body: {e.body}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred while patching BareMetalHost '{bmh_name}': {str(e)}")
        return False
