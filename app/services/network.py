"""
Network service module for managing switch configurations.

This module handles network switch operations using netmiko to configure
VLANs and port assignments for batch-provisioned servers.
"""
import hashlib
import logging
import os
import time
from typing import Dict, List, Optional

import yaml
from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException

from app.config import logger

class NetworkConfigurationError(Exception):
    """Raised when there's an error in network configuration."""
    pass


class SwitchManager:
    """Manages network switch configurations using Cisco commands."""
    
    def __init__(self, config_path: str = "app/network_config.yaml"):
        """
        Initialize the SwitchManager.
        
        Args:
            config_path: Path to the network configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.logger = logger
        
    def _load_config(self) -> Dict:
        """
        Load network configuration from YAML file.
        
        Returns:
            Configuration dictionary
            
        Raises:
            NetworkConfigurationError: If config file cannot be loaded
        """
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
                
            # Replace environment variable placeholders
            switch_config = config['switch']
            switch_config['host'] = os.environ.get('SWITCH_HOST', switch_config['host'].replace('{{ SWITCH_HOST | default(\'192.168.1.1\') }}', '192.168.1.1'))
            switch_config['username'] = os.environ.get('SWITCH_USERNAME', switch_config['username'].replace('{{ SWITCH_USERNAME | default(\'admin\') }}', 'admin'))
            switch_config['password'] = os.environ.get('SWITCH_PASSWORD', switch_config['password'].replace('{{ SWITCH_PASSWORD | default(\'admin\') }}', 'admin'))
            
            return config
        except FileNotFoundError:
            raise NetworkConfigurationError(f"Network configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise NetworkConfigurationError(f"Error parsing network configuration: {e}")
    
    def _get_server_ports(self, resource_names: List[str]) -> Dict[str, int]:
        """
        Get switch port numbers for given resource names.
        
        Args:
            resource_names: List of resource names (e.g., ['restart-srv01', 'restart-srv03'])
            
        Returns:
            Dictionary mapping resource names to port numbers
        """
        server_port_mapping = self.config['server_port_mapping']
        ports = {}
        
        for resource_name in resource_names:
            if resource_name in server_port_mapping:
                ports[resource_name] = server_port_mapping[resource_name]
            else:
                self.logger.warning(f"No port mapping found for resource: {resource_name}")
                
        return ports
    
    def _generate_vlan_id(self, resource_names: List[str], user_info: Dict) -> int:
        """
        Generate a unique VLAN ID based on batch resources and user info.
        
        Args:
            resource_names: List of resource names in the batch
            user_info: User information dictionary
            
        Returns:
            Generated VLAN ID
        """
        # Create a deterministic hash based on sorted resource names and username
        username = user_info.get('username', 'unknown')
        sorted_resources = sorted(resource_names)
        hash_input = f"{username}:{':'.join(sorted_resources)}"
        
        # Generate hash and convert to a reasonable VLAN ID range
        hash_value = hashlib.md5(hash_input.encode()).hexdigest()
        vlan_offset = int(hash_value[:4], 16) % 900  # Limit to 900 to avoid high VLAN IDs
        
        base_vlan_id = self.config['vlan']['base_id']
        vlan_id = base_vlan_id + vlan_offset
        
        # Ensure VLAN ID is within valid range (1-4094)
        if vlan_id > 4094:
            vlan_id = (vlan_id % 4094) + 1
            
        return vlan_id
    
    def _connect_to_switch(self) -> ConnectHandler:
        """
        Establish connection to the network switch.
        
        Returns:
            Connected netmiko device instance
            
        Raises:
            NetworkConfigurationError: If connection fails
        """
        try:
            device = ConnectHandler(**self.config['switch'])
            self.logger.info(f"Successfully connected to switch: {self.config['switch']['host']}")
            return device
        except NetmikoTimeoutException as e:
            raise NetworkConfigurationError(f"Timeout connecting to switch: {e}")
        except NetmikoAuthenticationException as e:
            raise NetworkConfigurationError(f"Authentication failed for switch: {e}")
        except Exception as e:
            raise NetworkConfigurationError(f"Failed to connect to switch: {e}")
    
    def _create_vlan(self, device: ConnectHandler, vlan_id: int, vlan_name: str, vlan_description: str) -> bool:
        """
        Create a VLAN on the switch.
        
        Args:
            device: Connected netmiko device
            vlan_id: VLAN ID to create
            vlan_name: Name for the VLAN
            vlan_description: Description for the VLAN
            
        Returns:
            True if successful, False otherwise
        """
        try:
            commands = [
                f"vlan {vlan_id}",
                f"name {vlan_name}",
                f"description {vlan_description}",
                "exit"
            ]
            
            device.enable()  # Enter privileged mode
            output = device.send_config_set(commands)
            device.save_config()  # Save configuration
            
            self.logger.info(f"Created VLAN {vlan_id} ({vlan_name}) on switch")
            self.logger.debug(f"VLAN creation output: {output}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create VLAN {vlan_id}: {e}")
            return False
    
    def _assign_ports_to_vlan(self, device: ConnectHandler, ports: List[int], vlan_id: int) -> bool:
        """
        Assign switch ports to a VLAN.
        
        Args:
            device: Connected netmiko device
            ports: List of port numbers to assign
            vlan_id: VLAN ID to assign ports to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create interface range command for multiple ports
            if len(ports) == 1:
                interface_range = f"interface Twe1/0/{ports[0]}"
            else:
                port_ranges = []
                ports.sort()
                
                # Group consecutive ports into ranges
                start = ports[0]
                end = ports[0]
                
                for port in ports[1:]:
                    if port == end + 1:
                        end = port
                    else:
                        if start == end:
                            port_ranges.append(f"Twe1/0/{start}")
                        else:
                            port_ranges.append(f"Twe1/0/{start}-{end}")
                        start = end = port
                
                # Add the last range
                if start == end:
                    port_ranges.append(f"Twe1/0/{start}")
                else:
                    port_ranges.append(f"Twe1/0/{start}-{end}")
                
                interface_range = f"interface range {','.join(port_ranges)}"
            
            commands = [
                interface_range,
                "switchport mode access",
                f"switchport access vlan {vlan_id}",
                "no shutdown",
                "exit"
            ]
            
            device.enable()  # Enter privileged mode
            output = device.send_config_set(commands)
            device.save_config()  # Save configuration
            
            self.logger.info(f"Assigned ports {ports} to VLAN {vlan_id}")
            self.logger.debug(f"Port assignment output: {output}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to assign ports {ports} to VLAN {vlan_id}: {e}")
            return False
    
    def configure_batch_network(self, resource_names: List[str], user_info: Dict) -> bool:
        """
        Configure network switch for a batch of provisioned servers.
        
        This method:
        1. Creates a unique VLAN for the batch
        2. Assigns all server ports to the VLAN
        3. Enables the ports
        
        Args:
            resource_names: List of resource names that were provisioned
            user_info: User information dictionary
            
        Returns:
            True if configuration was successful, False otherwise
        """
        if not resource_names:
            self.logger.warning("No resource names provided for network configuration")
            return True
        
        try:
            # Get port mapping for resources
            server_ports = self._get_server_ports(resource_names)
            if not server_ports:
                self.logger.warning("No valid port mappings found for any resources")
                return True
            
            # Generate VLAN ID and name
            vlan_id = self._generate_vlan_id(resource_names, user_info)
            username = user_info.get('username', 'unknown')
            timestamp = int(time.time())
            vlan_name = f"{self.config['vlan']['name_prefix']}_{username}_{timestamp}"
            vlan_description = f"{self.config['vlan']['description_prefix']} - User: {username}, Resources: {len(server_ports)}"
            
            # Connect to switch
            device = self._connect_to_switch()
            
            try:
                # Create VLAN
                if not self._create_vlan(device, vlan_id, vlan_name, vlan_description):
                    return False
                
                # Assign ports to VLAN
                ports = list(server_ports.values())
                if not self._assign_ports_to_vlan(device, ports, vlan_id):
                    return False
                
                self.logger.info(
                    f"Successfully configured network for batch: "
                    f"VLAN {vlan_id} with ports {ports} for user {username}"
                )
                return True
                
            finally:
                device.disconnect()
                self.logger.info("Disconnected from switch")
                
        except NetworkConfigurationError as e:
            self.logger.error(f"Network configuration error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during network configuration: {e}")
            return False


# Global instance for use in other modules
_switch_manager = None

def get_switch_manager() -> SwitchManager:
    """
    Get the global SwitchManager instance.
    
    Returns:
        SwitchManager instance
    """
    global _switch_manager
    if _switch_manager is None:
        _switch_manager = SwitchManager()
    return _switch_manager
