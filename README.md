# Polito Reservation Webhook Client

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-latest-green.svg?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Client-blue.svg?logo=kubernetes)](https://kubernetes.io/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg?logo=docker)](https://www.docker.com/)

A production-ready FastAPI microservice that manages Kubernetes BareMetalHost resources through webhook events. This service is designed with clean architecture principles, comprehensive error handling, and enterprise-grade security features.

> **Project Context:** This service is part of the Politecnico di Torino resource reservation system, enabling automated infrastructure provisioning and deprovisioning based on reservation lifecycle events.

## 🏗️ Architecture Overview

The webhook client follows clean architecture principles with clear separation of concerns:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Layer     │────│  Service Layer  │────│ Infrastructure  │
│   (FastAPI)     │    │   (Business)    │    │  (Kubernetes)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
   ┌────────────┐         ┌─────────────┐        ┌─────────────┐
   │ Webhook    │         │ Security    │        │   BMH       │
   │ Handlers   │         │ Service     │        │ Management  │
   └────────────┘         └─────────────┘        └─────────────┘
```

### Core Components

1. **API Layer** (`app/api.py`): Handles HTTP requests and webhook signature validation
2. **Service Layer** (`app/services/`): Contains business logic and external integrations
3. **Models** (`app/models.py`): Data validation and serialization using Pydantic
4. **Configuration** (`app/config.py`): Centralized configuration management

## 🎯 Features & Capabilities

### Event Processing
- **Webhook Reception**: Secure endpoint for receiving reservation lifecycle events
- **Event Types**: Handles `EVENT_START` (provisioning), `EVENT_END` (deprovisioning), and `EVENT_DELETED` (emergency deprovisioning)
- **Batch Processing**: Supports processing multiple events in a single webhook call for efficiency
- **Active Resources Tracking**: Tracks and reports user's currently active resources
- **Asynchronous Processing**: Non-blocking event handling with proper error recovery
- **Provisioning Wait**: Waits for BareMetalHost provisioning completion (similar to `kubectl wait`)
- **Automatic Notifications**: Sends HTTP notifications when provisioning completes
- **Webhook Logging**: Comprehensive logging of webhook events to external systems

### Security Features
- **HMAC-SHA256 Signature Verification**: Webhook payload authentication
- **Constant-Time Comparison**: Prevents timing attack vulnerabilities
- **Custom Security Service**: Modular security implementation with WebhookSecurity class

### Kubernetes Integration
- **BareMetalHost Management**: Direct interaction with Metal³ BareMetalHost CRDs
- **UserData Secret Management**: Automated cloud-config secret lifecycle
- **Resource Patching**: Strategic merge patching for optimal performance
- **Status Monitoring**: Real-time monitoring of provisioning state transitions
- **RBAC Support**: Fine-grained permission management

### Network Configuration
- **Automated Switch Configuration**: Automatic VLAN creation and port assignment for batch provisioning
- **Network Isolation**: Creates unique VLANs for each batch of provisioned servers
- **Switch Integration**: Supports Cisco IOS switches via SSH/Netmiko
- **Configurable Mappings**: Server-to-port mapping via YAML configuration

### Observability & Monitoring
- **Structured Logging**: Comprehensive logging with configurable levels
- **Health Checks**: Built-in health monitoring endpoints
- **Error Tracking**: Custom exception handling with detailed error contexts
- **Request Filtering**: Health check log filtering to reduce noise

### Production Features
- **Configuration Management**: Environment-based configuration with validation
- **Docker Support**: Production-ready containerization
- **Kubernetes Deployment**: Complete K8s manifests with RBAC
- **Graceful Shutdown**: Proper resource cleanup and connection handling

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Web Framework** | FastAPI 0.104+ | High-performance async API framework |
| **ASGI Server** | Uvicorn | Production ASGI server with reload support |
| **Validation** | Pydantic v2 | Data validation and serialization |
| **Kubernetes Client** | kubernetes-client | Official K8s Python client |
| **Security** | HMAC-SHA256 | Webhook signature verification |
| **Logging** | Python logging | Structured logging with custom filters |
| **Containerization** | Docker | Production-ready container images |
| **Orchestration** | Kubernetes | Cloud-native deployment |

### Dependencies
```python
fastapi>=0.70.0
uvicorn[standard]>=0.15.0
kubernetes>=20.0
pydantic
PyYAML>=6.0
netmiko>=4.3.0
requests>=2.25.0
```

## ⚙️ Configuration

The service uses a class-based configuration system with environment variable support and validation.

### Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `K8S_NAMESPACE` | string | `default` | Kubernetes namespace for BareMetalHost resources |
| `BMH_API_GROUP` | string | `metal3.io` | API group for BareMetalHost CRDs |
| `BMH_API_VERSION` | string | `v1alpha1` | API version for BareMetalHost CRDs |
| `BMH_PLURAL` | string | `baremetalhosts` | Plural name for BareMetalHost CRDs |
| `PROVISION_IMAGE` | string | `default-provision-image-url` | Image URL for provisioning operations |
| `PROVISION_CHECKSUM` | string | *(optional)* | Checksum URL for provision image verification |
| `PROVISION_CHECKSUM_TYPE` | string | `sha256` | Checksum type (sha256, md5, etc.) |
| `DEPROVISION_IMAGE` | string | *(empty)* | Optional image URL for deprovisioning |
| `WEBHOOK_SECRET` | string | *(optional)* | Shared secret for HMAC signature verification |
| `PORT` | integer | `8080` | Server listening port |
| `LOG_LEVEL` | string | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `DISABLE_HEALTHZ_LOGS` | boolean | `true` | Filter out health check logs from access logs |
| `PROVISIONING_TIMEOUT` | integer | `600` | Timeout in seconds for provisioning operations |
| `NOTIFICATION_ENDPOINT` | string | *(optional)* | External endpoint for provisioning notifications |
| `NOTIFICATION_TIMEOUT` | integer | `30` | Timeout in seconds for notification requests |
| `WEBHOOK_LOG_ENDPOINT` | string | *(optional)* | External endpoint for webhook event logging |
| `WEBHOOK_LOG_TIMEOUT` | integer | `30` | Timeout in seconds for webhook log requests |
| `NETWORK_CONFIG_ENABLED` | boolean | `true` | Enable automatic network switch configuration |
| `SWITCH_HOST` | string | *(optional)* | Network switch hostname or IP address |
| `SWITCH_USERNAME` | string | *(optional)* | Username for network switch authentication |
| `SWITCH_PASSWORD` | string | *(optional)* | Password for network switch authentication |

### Configuration Classes

```python
# Configuration is managed through dedicated classes:
- LoggingConfig: Handles logging setup and filters
- KubernetesConfig: Manages K8s client configuration  
- AppConfig: Main application configuration container
- HealthzFilter: Filters health check requests from logs
```

### Network Configuration

The service supports automatic network switch configuration for batch provisioning. Configuration is managed through `app/network_config.yaml`:

```yaml
switch:
  host: "{{ SWITCH_HOST }}"
  username: "{{ SWITCH_USERNAME }}"
  password: "{{ SWITCH_PASSWORD }}"
  device_type: "cisco_ios"

server_port_mapping:
  restart-srv01: 1
  restart-srv02: 2
  # ... mapping continues

vlan:
  base_id: 100
  name_prefix: "BATCH_VLAN"
```

### Kubernetes Authentication

The service automatically configures Kubernetes authentication:

1. **In-Cluster**: Uses service account token when running in K8s
2. **Local Development**: Falls back to `~/.kube/config`
3. **Custom Config**: Supports custom kubeconfig paths via environment

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- pip package manager
- Access to a Kubernetes cluster with Metal³ operator
- Docker (for containerized deployment)

### Local Development Setup

1. **Clone and Setup Environment**
   ```bash
   git clone <repository-url>
   cd polito-reservation-webhook-client
   
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # venv\Scripts\activate   # On Windows
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   # Essential configuration
   export K8S_NAMESPACE="metal3-system"
   export PROVISION_IMAGE="http://your-server/images/provision.iso"
   export PROVISION_CHECKSUM="http://your-server/images/provision.iso.sha256sum"
   export WEBHOOK_SECRET="your-secure-secret-key"
   export NOTIFICATION_ENDPOINT="https://your-domain.com/api/notifications/webhook"
   export WEBHOOK_LOG_ENDPOINT="https://your-domain.com/api/webhooks/log"
   export NETWORK_CONFIG_ENABLED="true"
   export SWITCH_HOST="192.168.1.1"
   export LOG_LEVEL="DEBUG"  # For development
   ```

4. **Run the Application**
   ```bash
   # Development with auto-reload
   uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
   
   # Production mode
   python -m app.main
   ```

### Docker Deployment

1. **Build Container Image**
   ```bash
   docker build -t webhook-client:latest .
   ```

2. **Run Container**
   ```bash
   docker run -d \
     --name webhook-client \
     -p 8080:8080 \
     -e K8S_NAMESPACE="metal3-system" \
     -e PROVISION_IMAGE="http://your-server/images/provision.iso" \
     -e PROVISION_CHECKSUM="http://your-server/images/provision.iso.sha256sum" \
     -e WEBHOOK_SECRET="your-secure-secret-key" \
     -e NOTIFICATION_ENDPOINT="https://your-domain.com/api/notifications/webhook" \
     -e WEBHOOK_LOG_ENDPOINT="https://your-domain.com/api/webhooks/log" \
     -e NETWORK_CONFIG_ENABLED="true" \
     -v ~/.kube:/root/.kube:ro \
     webhook-client:latest
   ```

### Kubernetes Deployment

Deploy using the provided manifests:

```bash
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

## 📡 API Reference

### Webhook Endpoint

**`POST /webhook`**

Receives and processes reservation lifecycle events. Supports both batch and single event formats.

**Supported Event Types:**
- `EVENT_START`: Initiates resource provisioning
- `EVENT_END`: Initiates resource deprovisioning  
- `EVENT_DELETED`: Emergency deprovisioning for deleted reservations

**Request Headers:**
- `Content-Type: application/json`
- `X-Webhook-Signature: sha256=<hmac_signature>` (required if WEBHOOK_SECRET is configured)

**Request Body (Batch Format - Recommended):**
```json
{
  "eventType": "EVENT_START | EVENT_END",
  "timestamp": "2025-06-08T14:30:00.000+02:00",
  "eventCount": 3,
  "webhookId": "webhook-123-456",
  "userId": "keycloak-user-id-123",
  "username": "giovanni.mirarchi",
  "email": "giovanni.mirarchi@example.com",
  "sshPublicKey": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQC...",
  "events": [
    {
      "eventId": "101",
      "eventTitle": "Server Maintenance Lab A",
      "eventDescription": "Maintenance work on lab servers",
      "eventStart": "2025-06-08T15:00:00.000+02:00",
      "eventEnd": "2025-06-08T17:00:00.000+02:00",
      "resourceId": 1,
      "resourceName": "Lab Server A1",
      "resourceType": "Server",
      "resourceSpecs": "Intel Xeon E5-2690, 32GB RAM, 1TB SSD",
      "resourceLocation": "Building A, Room 101",
      "siteId": "site-polito-torino",
      "siteName": "Politecnico di Torino"
    }
  ],
  "activeResources": [
    {
      "eventId": "95",
      "eventTitle": "Ongoing Database Maintenance",
      "eventDescription": "Regular maintenance on production database",
      "eventStart": "2025-06-08T13:00:00.000+02:00",
      "eventEnd": "2025-06-08T19:00:00.000+02:00",
      "resourceId": 8,
      "resourceName": "Production DB Server",
      "resourceType": "Database",
      "resourceSpecs": "PostgreSQL 15, 128GB RAM, NVMe SSD",
      "resourceLocation": "Data Center, Rack 3",
      "siteId": "site-polito-torino",
      "siteName": "Politecnico di Torino"
    }
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Batch event_start initiated for 3 events for user keycloak-user-id-123.",
  "timestamp": "2025-06-16T12:00:00Z"
}
```

**EVENT_DELETED Format:**
```json
{
  "eventType": "EVENT_DELETED",
  "timestamp": "2025-06-16T14:30:00.000+02:00",
  "webhookId": "webhook-789-012",
  "data": {
    "id": 12345,
    "start": "2025-06-16T15:00:00.000+02:00",
    "end": "2025-06-16T18:00:00.000+02:00",
    "resource": {
      "name": "Lab Server A1"
    },
    "keycloakId": "user-id-123"
  }
}
```

**Key Features:**
- **Batch Processing**: Multiple events processed in a single request for efficiency
- **Active Resources**: Shows user's currently active resources for context
- **Emergency Deprovisioning**: `EVENT_DELETED` immediately deprovisions active reservations
- **Backward Compatibility**: Supports both batch and single event formats
- **Network Automation**: Automatic VLAN creation and port assignment for batch provisioning
- **Comprehensive Logging**: All webhook events are logged to external systems

**Error Response:**
```json
{
  "detail": "Processing for event type 'EVENT_START' failed for 1 out of 3 events. Failures: [{'event_id': '102', 'resource_name': 'DB Cluster Node 1', 'action': 'provision'}]",
  "timestamp": "2025-06-16T12:00:00Z"
}
```

### Health Check Endpoint

**`GET /healthz`**

Simple health check for monitoring and load balancers.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2025-06-16T12:00:00Z"
}
```

### API Documentation

- **Swagger UI**: `http://host:port/docs`
- **ReDoc**: `http://host:port/redoc`
- **OpenAPI Spec**: `http://host:port/openapi.json`

## 🔧 Advanced Features

### Batch Processing

The webhook client supports efficient batch processing of multiple events:

- **Single Request**: Multiple events from the same user processed together
- **Network Automation**: Automatic VLAN creation for batch-provisioned servers
- **Active Resource Tracking**: Reports user's currently active resources
- **Atomic Operations**: All events in a batch succeed or fail together

### Network Configuration

Automatic network switch configuration for provisioned servers:

- **VLAN Creation**: Unique VLANs created for each batch of servers
- **Port Assignment**: Automatic assignment of server ports to VLANs
- **Switch Support**: Cisco IOS switches via SSH/Netmiko
- **Configuration File**: `app/network_config.yaml` for server-port mappings

### Webhook Logging

Comprehensive logging of all webhook events to external systems:

- **Event Tracking**: All webhook events logged with detailed metadata
- **Success/Failure Logging**: Both successful and failed operations tracked
- **External Integration**: Logs sent to configurable external endpoints
- **Retry Logic**: Built-in retry mechanism for failed log deliveries

### Emergency Deprovisioning

`EVENT_DELETED` support for immediate resource deprovisioning:

- **Active Reservation Check**: Only deprovisions if reservation is currently active
- **Timestamp Validation**: Compares current time with reservation start/end times
- **Immediate Action**: Bypasses normal workflow for emergency situations


## 📚 Documentation

Comprehensive documentation is available in the `docs/` directory:

- **[Architecture Guide](docs/ARCHITECTURE.md)**: System design and component relationships
- **[API Reference](docs/API.md)**: Complete API documentation with examples
- **[Network Configuration](docs/NETWORK_CONFIGURATION.md)**: Automatic switch configuration setup
- **[Configuration Reference](docs/CONFIGURATION.md)**: Complete configuration guide
- **[Deployment Guide](docs/DEPLOYMENT.md)**: Production deployment instructions
- **[Development Guide](docs/DEVELOPMENT.md)**: Developer setup and contribution guidelines
- **[Troubleshooting Guide](docs/TROUBLESHOOTING.md)**: Common issues and solutions

### Additional Resources

- **[Webhook Payload Examples](webhook-payload-examples.md)**: Detailed payload format examples
- **[Webhook Log Endpoint](webhook-log-endpoint.md)**: External webhook logging integration

### API Documentation
- **Swagger UI**: Interactive API documentation at `/docs`
- **ReDoc**: Alternative documentation interface at `/redoc`
- **OpenAPI Specification**: Machine-readable spec at `/openapi.json`

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For questions, issues, or contributions:

1. **GitHub Issues**: Report bugs and request features
2. **Documentation**: Check the comprehensive docs in `/docs`
3. **API Documentation**: Visit `/docs` endpoint for interactive API reference