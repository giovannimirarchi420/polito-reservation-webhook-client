# Network Configuration

This document describes the network configuration feature that automatically configures switch VLANs when servers are batch-provisioned.

## Overview

The network service automatically configures network switch settings when a batch of servers is provisioned. It creates VLANs and assigns server ports to establish network connectivity between the provisioned servers.

## Configuration

### Environment Variables

The following environment variables control network configuration:

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `NETWORK_CONFIG_ENABLED` | boolean | `true` | Enable/disable automatic network configuration |
| `SWITCH_HOST` | string | `192.168.1.1` | IP address or hostname of the network switch |
| `SWITCH_USERNAME` | string | `admin` | Username for switch authentication |
| `SWITCH_PASSWORD` | string | `admin` | Password for switch authentication |

### Network Configuration File

The network service uses `app/network_config.yaml` to define:

- Switch connection parameters
- Server-to-port mapping
- VLAN configuration settings

```yaml
switch:
  host: "{{ SWITCH_HOST | default('192.168.1.1') }}"
  username: "{{ SWITCH_USERNAME | default('admin') }}"
  password: "{{ SWITCH_PASSWORD | default('admin') }}"
  device_type: "cisco_ios"
  port: 22
  timeout: 30

server_port_mapping:
  restart-srv01: 1
  restart-srv02: 2
  # ... up to restart-srv15: 15

vlan:
  base_id: 100
  name_prefix: "BATCH_VLAN"
  description_prefix: "Auto-created VLAN for batch provisioning"
```

## How It Works

### Batch Provisioning Process

1. **Resource Provisioning**: Servers are provisioned through the normal webhook process
2. **Post-Batch Actions**: After all servers in a batch are provisioned, the `_post_batch_provision_actions` function is called
3. **Network Configuration**: The function:
   - Connects to the configured network switch
   - Creates a unique VLAN for the batch
   - Assigns all server ports to the VLAN
   - Enables the ports

### VLAN Creation

VLANs are created with the following characteristics:

- **VLAN ID**: Generated based on a hash of username and resource names to ensure uniqueness
- **Name**: Format: `BATCH_VLAN_{username}_{timestamp}`
- **Description**: Includes user information and resource count

### Port Assignment

The system maps resource names to switch ports:

- Resource names follow the pattern: `restart-srv01`, `restart-srv02`, ..., `restart-srv15`
- The number in the resource name corresponds to the switch port number
- Example: `restart-srv05` maps to switch port 5

### Cisco Commands

The service uses standard Cisco IOS commands:

```
# Create VLAN
vlan 101
name BATCH_VLAN_john_1638360000
description Auto-created VLAN for batch provisioning - User: john, Resources: 3
exit

# Assign ports to VLAN
interface range fa0/1,fa0/3,fa0/5
switchport mode access
switchport access vlan 101
no shutdown
exit
```

## Security Considerations

### Credentials Management

Switch credentials should be managed securely:

1. **Environment Variables**: Use environment variables for credentials
2. **Kubernetes Secrets**: Store credentials in Kubernetes secrets for production
3. **Access Control**: Limit switch access to the minimum required permissions

### Network Isolation

The VLAN configuration provides network isolation:

- Each batch gets its own VLAN
- Servers in different batches cannot communicate directly
- Additional firewall rules may be needed for internet access

## Monitoring and Troubleshooting

### Logging

The network service provides comprehensive logging:

```python
logger.info("Successfully configured network for batch: VLAN 101 with ports [1, 3, 5] for user john")
logger.error("Failed to connect to switch: Authentication failed")
```

### Error Handling

The service handles various error conditions:

- **Connection Failures**: Timeout, authentication errors
- **Configuration Errors**: Invalid VLAN IDs, port conflicts
- **Switch Errors**: Command execution failures

### Health Checks

To verify network configuration:

1. **Switch Console**: Check VLAN and port configuration directly on the switch
2. **Ping Tests**: Test connectivity between servers in the same batch
3. **Log Analysis**: Review application logs for configuration status

## Deployment

### Production Configuration

For production deployment:

1. **Update ConfigMap** with switch credentials:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: webhook-client-config
data:
  NETWORK_CONFIG_ENABLED: "true"
  SWITCH_HOST: "10.0.1.1"
```

2. **Create Secret** for sensitive data:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: webhook-client-secrets
data:
  SWITCH_USERNAME: <base64-encoded-username>
  SWITCH_PASSWORD: <base64-encoded-password>
```

3. **Update Deployment** to use the secret:
```yaml
env:
  - name: SWITCH_USERNAME
    valueFrom:
      secretKeyRef:
        name: webhook-client-secrets
        key: SWITCH_USERNAME
  - name: SWITCH_PASSWORD
    valueFrom:
      secretKeyRef:
        name: webhook-client-secrets
        key: SWITCH_PASSWORD
```

### Testing

Test the network configuration:

1. **Unit Tests**: Test VLAN ID generation and port mapping
2. **Integration Tests**: Test switch connection and command execution
3. **End-to-End Tests**: Test full batch provisioning with network configuration

## Limitations

- Supports Cisco IOS switches only
- Maximum 15 servers (ports 1-15)
- Single switch configuration
- No automatic VLAN cleanup on deprovisioning

## Future Enhancements

Potential improvements:

1. **Multi-Switch Support**: Support for multiple switches
2. **Advanced VLAN Management**: VLAN cleanup, reuse, and advanced routing
3. **Other Switch Types**: Support for other vendor switches
4. **Dynamic Port Discovery**: Automatic server-to-port mapping
5. **Network Monitoring**: Integration with network monitoring tools
