"""
Kubernetes service for managing BareMetalHost resources.

This module provides functionality to interact with Kubernetes API
to manage BareMetalHost custom resources and related secrets.
"""
import base64
from typing import Optional

import yaml
from kubernetes import client
from kubernetes.client.rest import ApiException

from .. import config

logger = config.logger

# Cloud-config template for user data
CLOUD_CONFIG_TEMPLATE = {
    "ssh_pwauth": True,
    "groups": ["admingroup", "cloud-users"],
    "users": [
        {
            "name": "restart.admin",
            "groups": "admingroup",
            "lock_passwd": False,
            "passwd": "$6$/O/rvHuhqfc00hDw$3X4ILugPTXw9JTtgWNh16oeFqLcsMOaPwzk7TBxtwm5QXa2vALMC2W7/JToC99ngxpKla80QpVAEs3jA8I0rk0",
            "sudo": "ALL=(ALL) NOPASSWD:ALL",
        },
        {
            "name": "prognose",  # New user for external access
            "groups": "cloud-users",
            "lock_passwd": True,  # Lock password, access only via SSH key
            "sudo": "ALL=(ALL) NOPASSWD:ALL",  # No sudo privileges for external user
            "ssh_authorized_keys": []  # Will be populated dynamically
        }
    ]
}


class KubernetesError(Exception):
    """Custom exception for Kubernetes operations."""
    pass


class UserDataSecretManager:
    """Manages user data secrets for BareMetalHost resources."""
    
    def __init__(self, api_client: Optional[client.CoreV1Api] = None):
        self.api = api_client or client.CoreV1Api()
    
    def _generate_cloud_config(self, ssh_key: str) -> str:
        """
        Generate cloud-config YAML with the provided SSH key.
        
        Args:
            ssh_key: SSH public key to include in the cloud-config
            
        Returns:
            Cloud-config as YAML string
        """
        cloud_config = CLOUD_CONFIG_TEMPLATE.copy()
        # Ensure users list is deep copied if further modifications are needed that could affect the template
        cloud_config["users"] = [user.copy() for user in CLOUD_CONFIG_TEMPLATE["users"]]

        # Find the "prognose" and add the ssh_key
        for user in cloud_config["users"]:
            if user["name"] == "prognose":
                user["ssh_authorized_keys"] = [ssh_key]
                break
        
        return "#cloud-config\\n" + yaml.dump(cloud_config, default_flow_style=False)
    
    def _encode_cloud_config(self, cloud_config: str) -> str:
        """
        Encode cloud-config to base64.
        
        Args:
            cloud_config: Cloud-config as string
            
        Returns:
            Base64 encoded cloud-config
        """
        return base64.b64encode(cloud_config.encode('utf-8')).decode('utf-8')
    
    def _create_secret_object(self, secret_name: str, cloud_config_b64: str) -> client.V1Secret:
        """
        Create a Kubernetes Secret object.
        
        Args:
            secret_name: Name of the secret
            cloud_config_b64: Base64 encoded cloud-config
            
        Returns:
            V1Secret object
        """
        return client.V1Secret(
            api_version="v1",
            kind="Secret",
            metadata=client.V1ObjectMeta(
                name=secret_name,
                namespace=config.K8S_NAMESPACE
            ),
            type="Opaque",
            data={"userData": cloud_config_b64}
        )
    
    def create_or_update(self, bmh_name: str, ssh_key: str) -> bool:
        """
        Create or update a user data secret for the BareMetalHost.
        
        Args:
            bmh_name: Name of the BareMetalHost
            ssh_key: SSH public key to include
            
        Returns:
            True if successful, False otherwise
        """
        secret_name = f"{bmh_name}-userdata"
        
        try:
            # Generate and encode cloud-config
            cloud_config = self._generate_cloud_config(ssh_key)
            cloud_config_b64 = self._encode_cloud_config(cloud_config)
            
            # Create secret object
            secret = self._create_secret_object(secret_name, cloud_config_b64)
            
            # Try to create the secret
            try:
                self.api.create_namespaced_secret(namespace=config.K8S_NAMESPACE, body=secret)
                logger.info(f"Created secret '{secret_name}' in namespace '{config.K8S_NAMESPACE}'.")
                return True
                
            except ApiException as e:
                if e.status == 409:  # Secret already exists, update it
                    self.api.patch_namespaced_secret(
                        name=secret_name, 
                        namespace=config.K8S_NAMESPACE, 
                        body=secret
                    )
                    logger.info(f"Updated existing secret '{secret_name}' in namespace '{config.K8S_NAMESPACE}'.")
                    return True
                else:
                    logger.error(
                        f"Error creating secret '{secret_name}': {e.reason} "
                        f"(Status: {e.status}). Body: {e.body}"
                    )
                    return False
                    
        except Exception as e:
            logger.error(f"Unexpected error while managing secret '{secret_name}': {str(e)}")
            return False


class BareMetalHostManager:
    """Manages BareMetalHost custom resources."""
    
    def __init__(self, api_client: Optional[client.CustomObjectsApi] = None):
        self.api = api_client or client.CustomObjectsApi()
        self.secret_manager = UserDataSecretManager()
    
    def _create_provision_patch(
        self, 
        image_url: str, 
        bmh_name: str,
        checksum: Optional[str] = None, 
        checksum_type: Optional[str] = None
    ) -> dict:
        """
        Create a patch for provisioning a BareMetalHost.
        
        Args:
            image_url: URL of the image to provision
            checksum: Image checksum
            checksum_type: Type of checksum (e.g., 'sha256')
            
        Returns:
            Patch dictionary for provisioning
        """
        return {
            "spec": {
                "image": {
                    "url": image_url,
                    "checksum": checksum,
                    "checksumType": checksum_type
                },
                "userData": {
                    "name": f"{bmh_name}-userdata",
                    "namespace": config.K8S_NAMESPACE
                }
            }
        }
    
    def _create_deprovision_patch(self) -> dict:
        """
        Create a patch for deprovisioning a BareMetalHost.
        
        Returns:
            Patch dictionary for deprovisioning
        """
        return {
            "spec": {
                "image": None,
                "userData": None
            }
        }
    
    def _apply_patch(self, bmh_name: str, patch: dict, operation: str) -> bool:
        """
        Apply a patch to a BareMetalHost resource.
        
        Args:
            bmh_name: Name of the BareMetalHost
            patch: Patch to apply
            operation: Description of the operation (for logging)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(
                f"Attempting to {operation} BareMetalHost '{bmh_name}' "
                f"in namespace '{config.K8S_NAMESPACE}'."
            )
            
            response = self.api.patch_namespaced_custom_object(
                group=config.BMH_API_GROUP,
                version=config.BMH_API_VERSION,
                namespace=config.K8S_NAMESPACE,
                plural=config.BMH_PLURAL,
                name=bmh_name,
                body=patch
            )

            logger.debug(
                f"Patch response for BareMetalHost '{bmh_name}': {response}"
            )
            
            logger.info(f"Successfully {operation}ed BareMetalHost '{bmh_name}'.")
            return True
            
        except ApiException as e:
            logger.error(
                f"Error {operation}ing BareMetalHost '{bmh_name}': {e.reason} "
                f"(Status: {e.status}). Body: {e.body}"
            )
            return False
            
        except Exception as e:
            logger.error(f"Unexpected error while {operation}ing BareMetalHost '{bmh_name}': {str(e)}")
            return False
    
    def provision(
        self, 
        bmh_name: str, 
        image_url: str, 
        ssh_key: Optional[str] = None,
        checksum: Optional[str] = None, 
        checksum_type: Optional[str] = None
    ) -> bool:
        """
        Provision a BareMetalHost with the specified image.
        
        Args:
            bmh_name: Name of the BareMetalHost
            image_url: URL of the image to provision
            ssh_key: SSH public key for user access
            checksum: Image checksum
            checksum_type: Type of checksum
            
        Returns:
            True if successful, False otherwise
        """
        # Create or update user data secret if SSH key is provided
        if ssh_key:
            if not self.secret_manager.create_or_update(bmh_name, ssh_key):
                logger.error(f"Failed to create userdata secret for BareMetalHost '{bmh_name}'. Aborting provision.")
                return False
        
        # Create and apply provision patch
        patch = self._create_provision_patch(image_url, bmh_name, checksum, checksum_type)
        return self._apply_patch(bmh_name, patch, "provision")
    
    def deprovision(self, bmh_name: str) -> bool:
        """
        Deprovision a BareMetalHost by clearing its image configuration.
        
        Args:
            bmh_name: Name of the BareMetalHost
            
        Returns:
            True if successful, False otherwise
        """
        patch = self._create_deprovision_patch()
        return self._apply_patch(bmh_name, patch, "deprovision")


# Singleton instance for backward compatibility
_bmh_manager = BareMetalHostManager()


def patch_baremetalhost(
    bmh_name: str, 
    image_url: Optional[str] = None, 
    ssh_key: Optional[str] = None, 
    checksum: Optional[str] = None, 
    checksum_type: Optional[str] = None
) -> bool:
    """
    Patch a BareMetalHost for provisioning or deprovisioning.
    
    This function maintains backward compatibility with the existing API.
    
    Args:
        bmh_name: Name of the BareMetalHost
        image_url: URL of the image to provision (None for deprovisioning)
        ssh_key: SSH public key for user access
        checksum: Image checksum
        checksum_type: Type of checksum
        
    Returns:
        True if successful, False otherwise
    """
    if image_url:
        return _bmh_manager.provision(bmh_name, image_url, ssh_key, checksum, checksum_type)
    else:
        return _bmh_manager.deprovision(bmh_name)


# Legacy function alias for backward compatibility
create_userdata_secret = lambda bmh_name, ssh_key: _bmh_manager.secret_manager.create_or_update(bmh_name, ssh_key)
