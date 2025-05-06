import json
from kubernetes import client
from kubernetes.client.rest import ApiException
from .. import config # Use relative import for config

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

    print(f"Patching BareMetalHost '{bmh_name}' in namespace '{config.K8S_NAMESPACE}' with patch: {json.dumps(patch)}", flush=True)

    try:
        api.patch_namespaced_custom_object(
            group=config.BMH_API_GROUP,
            version=config.BMH_API_VERSION,
            namespace=config.K8S_NAMESPACE,
            plural=config.BMH_PLURAL,
            name=bmh_name,
            body=patch
        )
        print(f"Successfully patched BareMetalHost '{bmh_name}'.", flush=True)
        return True
    except ApiException as e:
        print(f"Error patching BareMetalHost '{bmh_name}': {e.reason} (Status: {e.status})", flush=True)
        print(f"Response body: {e.body}", flush=True)
        return False
    except Exception as e:
        print(f"An unexpected error occurred patching BareMetalHost '{bmh_name}': {e}", flush=True)
        return False
