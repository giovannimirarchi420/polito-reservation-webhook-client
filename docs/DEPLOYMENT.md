# Deployment Guide

## Overview

This guide covers deployment strategies for the Polito Reservation Webhook Client across different environments, from local development to production Kubernetes clusters.

## Prerequisites

### General Requirements
- Python 3.10+
- Docker (for containerized deployments)
- Kubernetes cluster with Metal³ operator (for production)
- kubectl configured for cluster access

### Kubernetes Requirements
- Kubernetes 1.25+
- Metal³ operator installed
- RBAC permissions for BareMetalHost management
- Network access to the Kubernetes API server

## Local Development

### 1. Environment Setup

```bash
# Clone repository
git clone <repository-url>
cd polito-reservation-webhook-client

# Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file:

```bash
# Kubernetes Configuration
K8S_NAMESPACE=metal3-system
BMH_API_GROUP=metal3.io
BMH_API_VERSION=v1alpha1
BMH_PLURAL=baremetalhosts

# Images
PROVISION_IMAGE=http://your-server/images/provision.iso
DEPROVISION_IMAGE=  # Optional

# Security
WEBHOOK_SECRET=your-development-secret

# Server
PORT=5001
LOG_LEVEL=DEBUG
```

### 3. Run Application

```bash
# Development mode with auto-reload
uvicorn app.main:app --host 0.0.0.0 --port 5001 --reload

# Production mode
python -m app.main
```

### 4. Test Connectivity

```bash
# Health check
curl http://localhost:5001/healthz

# API documentation
open http://localhost:5001/docs
```

## Docker Deployment

### 1. Build Image

```bash
# Build production image
docker build -t webhook-client:latest .

# Build with custom tag
docker build -t webhook-client:v1.0.0 .
```

### 2. Run Container

#### Development Configuration

```bash
docker run -d \
  --name webhook-client-dev \
  -p 5001:5001 \
  -e K8S_NAMESPACE=metal3-system \
  -e PROVISION_IMAGE=http://your-server/images/provision.iso \
  -e WEBHOOK_SECRET=dev-secret \
  -e LOG_LEVEL=DEBUG \
  -v ~/.kube:/root/.kube:ro \
  webhook-client:latest
```

#### Production Configuration

```bash
docker run -d \
  --name webhook-client \
  -p 5001:5001 \
  --env-file .env.production \
  --restart unless-stopped \
  webhook-client:latest
```

### 3. Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  webhook-client:
    build: .
    ports:
      - "5001:5001"
    environment:
      - K8S_NAMESPACE=metal3-system
      - PROVISION_IMAGE=http://your-server/images/provision.iso
      - WEBHOOK_SECRET=${WEBHOOK_SECRET}
      - LOG_LEVEL=INFO
    volumes:
      - ~/.kube:/root/.kube:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5001/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
```

Run with:
```bash
docker-compose up -d
```

## Kubernetes Deployment

### 1. Prepare Manifests

The `k8s/` directory contains all necessary Kubernetes manifests:

```
k8s/
├── namespace.yaml          # Namespace creation
├── rbac-restrictive.yaml   # RBAC permissions
├── configmap.yaml          # Configuration
├── secret.yaml             # Sensitive configuration
├── deployment.yaml         # Application deployment
├── service.yaml            # Service definition
└── ingress.yaml            # Ingress configuration
```

### 2. Configure Secrets

Edit `k8s/secret.yaml` and update the base64-encoded values:

```bash
# Encode secrets
echo -n "your-webhook-secret" | base64
echo -n "http://your-server/images/provision.iso" | base64

# Update secret.yaml with encoded values
```

### 3. Configure ConfigMap

Edit `k8s/configmap.yaml` for your environment:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: webhook-client-config
  namespace: webhook-client
data:
  K8S_NAMESPACE: "metal3-system"
  BMH_API_GROUP: "metal3.io"
  BMH_API_VERSION: "v1alpha1"
  BMH_PLURAL: "baremetalhosts"
  PORT: "5001"
  LOG_LEVEL: "INFO"
```

### 4. Deploy Application

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Apply RBAC
kubectl apply -f k8s/rbac-restrictive.yaml

# Create configuration
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml

# Deploy application
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Configure ingress (optional)
kubectl apply -f k8s/ingress.yaml
```

### 5. Verify Deployment

```bash
# Check pod status
kubectl get pods -n webhook-client

# Check logs
kubectl logs -f deployment/webhook-client -n webhook-client

# Test health endpoint
kubectl port-forward svc/webhook-client 5001:5001 -n webhook-client
curl http://localhost:5001/healthz
```

## Production Considerations

### 1. Resource Management

Configure appropriate resource limits in `deployment.yaml`:

```yaml
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "200m"
```

### 2. Health Checks

Configure liveness and readiness probes:

```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 5001
  initialDelaySeconds: 30
  periodSeconds: 10
  
readinessProbe:
  httpGet:
    path: /healthz
    port: 5001
  initialDelaySeconds: 5
  periodSeconds: 5
```

### 3. Security Hardening

#### RBAC Configuration

Use minimal RBAC permissions:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: webhook-client-role
  namespace: metal3-system
rules:
- apiGroups: ["metal3.io"]
  resources: ["baremetalhosts"]
  verbs: ["get", "patch"]
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get", "create", "update", "delete"]
```

#### Pod Security

Configure security context:

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 1000
  fsGroup: 1000
  capabilities:
    drop:
    - ALL
  readOnlyRootFilesystem: true
```

### 4. Monitoring and Logging

#### Logging Configuration

```yaml
env:
- name: LOG_LEVEL
  value: "INFO"
- name: LOG_FORMAT
  value: "json"  # For structured logging
```

#### Monitoring Integration

Add monitoring labels and annotations:

```yaml
metadata:
  labels:
    app: webhook-client
    version: v1.0.0
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "5001"
    prometheus.io/path: "/metrics"
```

### 5. High Availability

#### Multiple Replicas

```yaml
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
```

#### Pod Disruption Budget

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: webhook-client-pdb
  namespace: webhook-client
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: webhook-client
```

## Scaling Considerations

### Horizontal Scaling

The service is stateless and can be horizontally scaled:

```bash
# Scale deployment
kubectl scale deployment webhook-client --replicas=5 -n webhook-client

# Auto-scaling (HPA)
kubectl autoscale deployment webhook-client \
  --cpu-percent=70 \
  --min=2 \
  --max=10 \
  -n webhook-client
```

### Load Balancing

Configure appropriate load balancing:

- **Service Type**: ClusterIP for internal access
- **Ingress**: For external access with SSL termination
- **Load Balancer**: For cloud provider integration

## Troubleshooting

### Common Issues

#### 1. Kubernetes Authentication

```bash
# Check service account
kubectl get serviceaccount webhook-client -n webhook-client

# Check RBAC
kubectl auth can-i get baremetalhosts --as=system:serviceaccount:webhook-client:webhook-client -n metal3-system
```

#### 2. Network Connectivity

```bash
# Test internal connectivity
kubectl run test-pod --image=curlimages/curl -it --rm -- \
  curl http://webhook-client.webhook-client.svc.cluster.local:5001/healthz

# Check service endpoints
kubectl get endpoints webhook-client -n webhook-client
```

#### 3. Configuration Issues

```bash
# Check environment variables
kubectl exec deployment/webhook-client -n webhook-client -- env | grep -E "K8S_|BMH_|PROVISION_"

# Check logs for configuration errors
kubectl logs deployment/webhook-client -n webhook-client | grep -i error
```

### Debugging Commands

```bash
# Get detailed pod information
kubectl describe pod <pod-name> -n webhook-client

# Access pod shell
kubectl exec -it <pod-name> -n webhook-client -- /bin/sh

# Check resource usage
kubectl top pods -n webhook-client

# View events
kubectl get events -n webhook-client --sort-by='.lastTimestamp'
```

## Backup and Recovery

### Configuration Backup

```bash
# Backup all configurations
kubectl get all,secrets,configmaps -n webhook-client -o yaml > webhook-client-backup.yaml

# Backup specific resources
kubectl get secret webhook-client-secret -n webhook-client -o yaml > secret-backup.yaml
```

### Disaster Recovery

1. **Redeploy from manifests**: All configuration is in version control
2. **Update secrets**: Regenerate and update sensitive values
3. **Verify connectivity**: Test Kubernetes API access and RBAC
4. **Health checks**: Ensure all endpoints are responding

## Maintenance

### Updates

```bash
# Update image
kubectl set image deployment/webhook-client webhook-client=webhook-client:v1.1.0 -n webhook-client

# Rolling update status
kubectl rollout status deployment/webhook-client -n webhook-client

# Rollback if needed
kubectl rollout undo deployment/webhook-client -n webhook-client
```

### Monitoring

- Monitor pod health and resource usage
- Check application logs regularly
- Monitor Kubernetes API quota usage
- Track webhook processing metrics
