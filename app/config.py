import os
from kubernetes import config as kube_config # Alias to avoid name clash

# Load Kubernetes configuration
def load_kubernetes_config():
    try:
        kube_config.load_incluster_config()
        print("Loaded in-cluster Kubernetes config.", flush=True)
    except kube_config.ConfigException:
        try:
            kube_config.load_kube_config()
            print("Loaded local Kubernetes config (kubeconfig).", flush=True)
        except kube_config.ConfigException:
            print("Could not load any Kubernetes configuration.", flush=True)
            # Depending on requirements, you might exit or handle this differently

# Load configuration from environment variables
K8S_NAMESPACE = os.environ.get("K8S_NAMESPACE", "default")
BMH_API_GROUP = os.environ.get("BMH_API_GROUP", "metal3.io")
BMH_API_VERSION = os.environ.get("BMH_API_VERSION", "v1alpha1")
BMH_PLURAL = os.environ.get("BMH_PLURAL", "baremetalhosts")
PROVISION_IMAGE = os.environ.get("PROVISION_IMAGE", "default-provision-image-url")
DEPROVISION_IMAGE = os.environ.get("DEPROVISION_IMAGE", "")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET")
PORT = 8088
# Initialize Kubernetes config on load
load_kubernetes_config()
