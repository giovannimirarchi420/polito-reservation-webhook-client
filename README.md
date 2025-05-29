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
- **Event Types**: Handles `EVENT_START` (provisioning) and `EVENT_END` (deprovisioning)
- **Asynchronous Processing**: Non-blocking event handling with proper error recovery

### Security Features
- **HMAC-SHA256 Signature Verification**: Webhook payload authentication
- **Constant-Time Comparison**: Prevents timing attack vulnerabilities
- **Custom Security Service**: Modular security implementation with WebhookSecurity class

### Kubernetes Integration
- **BareMetalHost Management**: Direct interaction with Metal³ BareMetalHost CRDs
- **UserData Secret Management**: Automated cloud-config secret lifecycle
- **Resource Patching**: Strategic merge patching for optimal performance
- **RBAC Support**: Fine-grained permission management

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
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
kubernetes>=28.1.0
pydantic>=2.5.0
python-multipart>=0.0.6
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
| `DEPROVISION_IMAGE` | string | *(empty)* | Optional image URL for deprovisioning |
| `WEBHOOK_SECRET` | string | *(optional)* | Shared secret for HMAC signature verification |
| `PORT` | integer | `5001` | Server listening port |
| `LOG_LEVEL` | string | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

### Configuration Classes

```python
# Configuration is managed through dedicated classes:
- LoggingConfig: Handles logging setup and filters
- KubernetesConfig: Manages K8s client configuration  
- AppConfig: Main application configuration container
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
   # Copy and customize environment configuration
   cp .env.example .env
   
   # Essential configuration
   export K8S_NAMESPACE="metal3-system"
   export PROVISION_IMAGE="http://your-server/images/provision.iso"
   export WEBHOOK_SECRET="your-secure-secret-key"
   export LOG_LEVEL="DEBUG"  # For development
   ```

4. **Run the Application**
   ```bash
   # Development with auto-reload
   uvicorn app.main:app --host 0.0.0.0 --port 5001 --reload
   
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
     -p 5001:5001 \
     -e K8S_NAMESPACE="metal3-system" \
     -e PROVISION_IMAGE="http://your-server/images/provision.iso" \
     -e WEBHOOK_SECRET="your-secure-secret-key" \
     -v ~/.kube:/root/.kube:ro \
     webhook-client:latest
   ```

### Kubernetes Deployment

Deploy using the provided manifests:

```bash
# Apply namespace and RBAC
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/rbac-restrictive.yaml

# Create secrets and config
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/configmap.yaml

# Deploy application
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

## 📡 API Reference

### Webhook Endpoint

**`POST /webhook`**

Receives and processes reservation lifecycle events.

**Request Headers:**
- `Content-Type: application/json`
- `X-Webhook-Signature: sha256=<hmac_signature>` (required if WEBHOOK_SECRET is configured)

**Request Body:**
```json
{
    "eventType": "EVENT_START | EVENT_END",
    "timestamp": "2019-08-24T14:15:22Z",
    "eventId": "string",
    "userId": "string",
    "username": "string",
    "email": "string",
    "sshPublicKey": "string",
    "eventTitle": "string",
    "eventDescription": "string",
    "eventStart": "2019-08-24T14:15:22Z",
    "eventEnd": "2019-08-24T14:15:22Z",
    "resourceId": 0,
    "resourceName": "string",
    "resourceType": "string",
    "resourceSpecs": "string",
    "resourceLocation": "string",
    "siteId": "string",
    "siteName": "string"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Resource provisioned successfully",
  "resourceName": "bmh-resource-001",
  "eventType": "EVENT_START",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**Error Response:**
```json
{
  "detail": "Error description",
  "error_type": "KubernetesError",
  "resource_name": "bmh-resource-001",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Health Check Endpoint

**`GET /healthz`**

Simple health check for monitoring and load balancers.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### API Documentation

- **Swagger UI**: `http://host:port/docs`
- **ReDoc**: `http://localhost:port/redoc`
- **OpenAPI Spec**: `http://localhost:port/openapi.json`


## 📚 Documentation

Comprehensive documentation is available in the `docs/` directory:

- **[Architecture Guide](docs/ARCHITECTURE.md)**: System design and component relationships
- **[API Reference](docs/API.md)**: Complete API documentation with examples
- **[Deployment Guide](docs/DEPLOYMENT.md)**: Production deployment instructions
- **[Development Guide](docs/DEVELOPMENT.md)**: Developer setup and contribution guidelines

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