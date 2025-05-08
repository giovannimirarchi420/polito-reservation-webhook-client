import os
from kubernetes import config as kube_config # Alias to avoid name clash
import logging # Add logging import

# Logging setup
def setup_logging():
    """Sets up a basic logger."""
    logger = logging.getLogger("webhook_client")
    
    # Get log level from environment variable, default to INFO
    log_level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_name, logging.INFO)
    logger.setLevel(log_level)
    
    handler = logging.StreamHandler() # Log to stdout/stderr
    # More detailed formatter for production
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(module)s:%(lineno)d] - %(message)s')
    handler.setFormatter(formatter)
    
    if not logger.handlers: # Avoid adding multiple handlers if reloaded
        logger.addHandler(handler)
    return logger

logger = setup_logging() # Initialize logger

# Load Kubernetes configuration
def load_kubernetes_config():
    try:
        kube_config.load_incluster_config()
        logger.info("Loaded in-cluster Kubernetes config.")
    except kube_config.ConfigException:
        try:
            kube_config.load_kube_config()
            logger.info("Loaded local Kubernetes config (kubeconfig).")
        except kube_config.ConfigException:
            logger.error("Could not load any Kubernetes configuration.")
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
