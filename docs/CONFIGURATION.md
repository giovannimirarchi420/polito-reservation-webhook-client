# Configuration Reference

## Overview

This document provides a comprehensive reference for all configuration options available in the Polito Reservation Webhook Client.

## Configuration Architecture

The service uses a hierarchical configuration system:

```
Environment Variables
        ↓
Configuration Classes
        ↓
Application Components
```

### Configuration Classes

1. **`AppConfig`**: Main application configuration container
2. **`LoggingConfig`**: Logging setup and management
3. **`KubernetesConfig`**: Kubernetes client configuration

## Environment Variables

### Core Configuration

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `PORT` | integer | No | `5001` | HTTP server listening port |
| `LOG_LEVEL` | string | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |

### Kubernetes Configuration

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `K8S_NAMESPACE` | string | No | `default` | Target namespace for BareMetalHost resources |
| `BMH_API_GROUP` | string | No | `metal3.io` | API group for BareMetalHost custom resources |
| `BMH_API_VERSION` | string | No | `v1alpha1` | API version for BareMetalHost resources |
| `BMH_PLURAL` | string | No | `baremetalhosts` | Plural name for BareMetalHost resources |
| `KUBECONFIG` | string | No | `~/.kube/config` | Path to kubeconfig file (local development) |

### Resource Management

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `PROVISION_IMAGE` | string | Yes | None | Image URL for provisioning operations |
| `DEPROVISION_IMAGE` | string | No | None | Image URL for deprovisioning (optional) |
| `USER_DATA_SECRET_PREFIX` | string | No | `user-data` | Prefix for generated user data secrets |

### Security Configuration

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `WEBHOOK_SECRET` | string | No | None | Shared secret for HMAC signature verification |
| `SIGNATURE_HEADER` | string | No | `X-Webhook-Signature` | HTTP header name for webhook signatures |

### Advanced Configuration

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `REQUEST_TIMEOUT` | integer | No | `30` | Request timeout in seconds |
| `MAX_RETRIES` | integer | No | `3` | Maximum retry attempts for failed operations |
| `RETRY_BACKOFF` | float | No | `1.0` | Backoff multiplier for retry attempts |

## Configuration Examples

### Development Environment

```bash
# .env.development
PORT=5001
LOG_LEVEL=DEBUG

# Kubernetes
K8S_NAMESPACE=metal3-dev
PROVISION_IMAGE=http://dev-server/images/provision.iso

# Security (optional for development)
WEBHOOK_SECRET=dev-secret-key

# Local kubeconfig
KUBECONFIG=/Users/developer/.kube/config
```

### Production Environment

```yaml
# Kubernetes ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: webhook-client-config
  namespace: webhook-client
data:
  PORT: "5001"
  LOG_LEVEL: "INFO"
  K8S_NAMESPACE: "metal3-system"
  BMH_API_GROUP: "metal3.io"
  BMH_API_VERSION: "v1alpha1"
  BMH_PLURAL: "baremetalhosts"
  USER_DATA_SECRET_PREFIX: "bmh-user-data"
  REQUEST_TIMEOUT: "30"
  MAX_RETRIES: "3"
  RETRY_BACKOFF: "2.0"

---
# Kubernetes Secret
apiVersion: v1
kind: Secret
metadata:
  name: webhook-client-secret
  namespace: webhook-client
type: Opaque
data:
  WEBHOOK_SECRET: <base64-encoded-secret>
  PROVISION_IMAGE: <base64-encoded-url>
  DEPROVISION_IMAGE: <base64-encoded-url>
```

### Docker Environment

```bash
# docker-compose.yml environment section
environment:
  - PORT=5001
  - LOG_LEVEL=INFO
  - K8S_NAMESPACE=metal3-system
  - PROVISION_IMAGE=http://image-server/provision.iso
  - WEBHOOK_SECRET=production-secret
```

## Configuration Classes Reference

### AppConfig

```python
class AppConfig:
    """Main application configuration."""
    
    def __init__(self):
        self.port: int = int(os.getenv("PORT", "5001"))
        self.webhook_secret: Optional[str] = os.getenv("WEBHOOK_SECRET")
        self.provision_image: str = os.getenv("PROVISION_IMAGE", "")
        self.deprovision_image: Optional[str] = os.getenv("DEPROVISION_IMAGE")
        self.request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
        self.max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
        self.retry_backoff: float = float(os.getenv("RETRY_BACKOFF", "1.0"))
        
        # Initialize sub-configurations
        self.kubernetes = KubernetesConfig()
        self.logging = LoggingConfig()
```

#### Properties

- **`port`**: HTTP server port
- **`webhook_secret`**: Optional secret for signature verification
- **`provision_image`**: Required image URL for provisioning
- **`deprovision_image`**: Optional image URL for deprovisioning
- **`request_timeout`**: Timeout for HTTP requests
- **`max_retries`**: Maximum retry attempts
- **`retry_backoff`**: Backoff multiplier for retries

### KubernetesConfig

```python
class KubernetesConfig:
    """Kubernetes client configuration."""
    
    def __init__(self):
        self.namespace: str = os.getenv("K8S_NAMESPACE", "default")
        self.api_group: str = os.getenv("BMH_API_GROUP", "metal3.io")
        self.api_version: str = os.getenv("BMH_API_VERSION", "v1alpha1")
        self.plural: str = os.getenv("BMH_PLURAL", "baremetalhosts")
        self.user_data_secret_prefix: str = os.getenv("USER_DATA_SECRET_PREFIX", "user-data")
```

#### Properties

- **`namespace`**: Target namespace for operations
- **`api_group`**: CRD API group
- **`api_version`**: CRD API version
- **`plural`**: Resource plural name
- **`user_data_secret_prefix`**: Prefix for generated secrets

### LoggingConfig

```python
class LoggingConfig:
    """Logging configuration."""
    
    def __init__(self):
        self.level: str = os.getenv("LOG_LEVEL", "INFO")
```

#### Properties

- **`level`**: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Configuration Validation

### Required Configuration

The service validates required configuration on startup:

```python
def validate_config(config: AppConfig) -> None:
    """Validate configuration completeness."""
    errors = []
    
    if not config.provision_image:
        errors.append("PROVISION_IMAGE is required")
    
    if config.port < 1 or config.port > 65535:
        errors.append("PORT must be between 1 and 65535")
    
    if config.max_retries < 0:
        errors.append("MAX_RETRIES must be non-negative")
    
    if errors:
        raise ConfigurationError(f"Configuration errors: {', '.join(errors)}")
```

### Environment-Specific Validation

#### Development

```python
# Less strict validation for development
if config.webhook_secret is None:
    logger.warning("WEBHOOK_SECRET not set - signature verification disabled")
```

#### Production

```python
# Strict validation for production
if not config.webhook_secret:
    raise ConfigurationError("WEBHOOK_SECRET is required in production")

if not config.provision_image.startswith(("http://", "https://")):
    raise ConfigurationError("PROVISION_IMAGE must be a valid URL")
```

## Configuration Best Practices

### 1. Security

- **Never commit secrets**: Use environment variables or Kubernetes secrets
- **Use strong secrets**: Generate cryptographically secure webhook secrets
- **Validate URLs**: Ensure image URLs are properly formatted and accessible

```bash
# Generate secure webhook secret
openssl rand -hex 32
```

### 2. Environment Separation

- **Different configs per environment**: Separate development, staging, and production
- **Use configuration templates**: Parameterize environment-specific values
- **Version configuration**: Track configuration changes

### 3. Validation

- **Validate on startup**: Fail fast with clear error messages
- **Document defaults**: Make default values explicit and documented
- **Test configuration**: Include configuration validation in tests

### 4. Monitoring

- **Log configuration**: Log non-sensitive configuration on startup
- **Monitor changes**: Track configuration updates
- **Health checks**: Include configuration in health check responses

## Configuration Templates

### Kubernetes Deployment Template

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webhook-client
  namespace: webhook-client
spec:
  template:
    spec:
      containers:
      - name: webhook-client
        env:
        # From ConfigMap
        - name: PORT
          valueFrom:
            configMapKeyRef:
              name: webhook-client-config
              key: PORT
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: webhook-client-config
              key: LOG_LEVEL
        - name: K8S_NAMESPACE
          valueFrom:
            configMapKeyRef:
              name: webhook-client-config
              key: K8S_NAMESPACE
        
        # From Secret
        - name: WEBHOOK_SECRET
          valueFrom:
            secretKeyRef:
              name: webhook-client-secret
              key: WEBHOOK_SECRET
        - name: PROVISION_IMAGE
          valueFrom:
            secretKeyRef:
              name: webhook-client-secret
              key: PROVISION_IMAGE
```

### Docker Compose Template

```yaml
version: '3.8'
services:
  webhook-client:
    build: .
    environment:
      # Override these in .env file
      - PORT=${PORT:-5001}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - K8S_NAMESPACE=${K8S_NAMESPACE:-default}
      - PROVISION_IMAGE=${PROVISION_IMAGE}
      - WEBHOOK_SECRET=${WEBHOOK_SECRET}
    env_file:
      - .env.local
```

## Configuration Migration

### Version 1.0 to 1.1

```bash
# Added new configuration options
USER_DATA_SECRET_PREFIX=bmh-user-data
REQUEST_TIMEOUT=30
MAX_RETRIES=3
RETRY_BACKOFF=2.0

# Deprecated (still supported)
# WEBHOOK_SIGNATURE_HEADER (use SIGNATURE_HEADER instead)
```

### Migration Script

```python
def migrate_config():
    """Migrate configuration from old to new format."""
    # Handle deprecated environment variables
    old_header = os.getenv("WEBHOOK_SIGNATURE_HEADER")
    if old_header and not os.getenv("SIGNATURE_HEADER"):
        os.environ["SIGNATURE_HEADER"] = old_header
        logger.warning("WEBHOOK_SIGNATURE_HEADER is deprecated, use SIGNATURE_HEADER")
```

## Troubleshooting Configuration

### Common Issues

1. **Missing required variables**:
   ```
   ConfigurationError: PROVISION_IMAGE is required
   ```
   Solution: Set the PROVISION_IMAGE environment variable

2. **Invalid port numbers**:
   ```
   ConfigurationError: PORT must be between 1 and 65535
   ```
   Solution: Set PORT to a valid port number

3. **Kubernetes connection issues**:
   ```
   ConfigurationError: Unable to load Kubernetes configuration
   ```
   Solution: Check KUBECONFIG path or in-cluster configuration

### Debug Configuration

```bash
# Enable debug logging to see configuration loading
LOG_LEVEL=DEBUG python -m app.main

# Check environment variables
env | grep -E "PORT|LOG_|K8S_|BMH_|PROVISION_|WEBHOOK_"

# Validate Kubernetes configuration
kubectl cluster-info
kubectl auth can-i get baremetalhosts -n metal3-system
```

### Configuration Dump

```python
# Add debug endpoint to dump non-sensitive configuration
@app.get("/debug/config")
async def debug_config():
    """Debug endpoint to show current configuration."""
    return {
        "port": config.port,
        "log_level": config.logging.level,
        "kubernetes": {
            "namespace": config.kubernetes.namespace,
            "api_group": config.kubernetes.api_group,
            "api_version": config.kubernetes.api_version,
        },
        # Don't include sensitive values
        "webhook_secret_configured": bool(config.webhook_secret),
        "provision_image_configured": bool(config.provision_image),
    }
```
