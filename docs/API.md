# API Documentation

## Overview

The Webhook Client provides a RESTful API for managing BareMetalHost resources through webhook events. The API is built with FastAPI and provides automatic OpenAPI documentation.

## Base URL

- **Development**: `http://localhost:5001`
- **Production**: Configured via ingress/load balancer

## Authentication

### Webhook Signature Verification

All webhook requests must include a signature header when `WEBHOOK_SECRET` is configured:

```
X-Webhook-Signature: <hmac_hex_digest>
```

**Signature Generation:**
```python
import hmac
import hashlib

def generate_signature(payload: bytes, secret: str) -> str:
    if not self.secret:
        raise SignatureVerificationError("Webhook secret not configured")

    hash_object = hmac.new(
        self.secret.encode('utf-8'),
        msg=payload,
        digestmod=hashlib.sha256
    )
    return base64.b64encode(hash_object.digest()).decode('utf-8') # signature
```

## Endpoints

### POST /webhook

Processes reservation lifecycle events and manages corresponding Kubernetes resources.

#### Request

**Headers:**
```
Content-Type: application/json
X-Webhook-Signature: <signature> (required if WEBHOOK_SECRET set)
```

**Body Schema:**

The webhook supports both batch and single event formats. For detailed examples, see `webhook-payload-examples.md`.

**Batch Format (Recommended):**
```json
{
    "eventType": "EVENT_START | EVENT_END",
    "timestamp": "2025-06-08T14:30:00.000+02:00",
    "eventCount": 3,
    "userId": "string",
    "username": "string",
    "email": "string",
    "sshPublicKey": "string",
    "events": [
        {
            "eventId": "string",
            "eventTitle": "string",
            "eventDescription": "string",
            "eventStart": "2025-06-08T15:00:00.000+02:00",
            "eventEnd": "2025-06-08T17:00:00.000+02:00",
            "resourceId": 0,
            "resourceName": "string",
            "resourceType": "string",
            "resourceSpecs": "string",
            "resourceLocation": "string",
            "siteId": "string",
            "siteName": "string"
        }
    ],
    "activeResources": [
        {
            "eventId": "string",
            "eventTitle": "string",
            "eventDescription": "string",
            "eventStart": "2025-06-08T13:00:00.000+02:00",
            "eventEnd": "2025-06-08T19:00:00.000+02:00",
            "resourceId": 0,
            "resourceName": "string",
            "resourceType": "string",
            "resourceSpecs": "string",
            "resourceLocation": "string",
            "siteId": "string",
            "siteName": "string"
        }
    ]
}
```

**Single Event Format (Backward Compatibility):**
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

**Notes:**
- `activeResources`: Optional field containing resources currently in use by the user (only present in batch format)
- `activeResources` can be `null` or empty if the user has no currently active resources
- Events in `activeResources` are always different from those in `events` (no duplicates)

#### Response

**Success (200 OK):**
```json
{
  "status": "success",
  "message": "Resource provisioned successfully",
  "resourceName": "bmh-node-001",
  "eventType": "EVENT_START",
  "timestamp": "2024-01-15T14:30:00Z"
}
```

**Error (4xx/5xx):**
```json
{
  "detail": "Detailed error message",
  "error_type": "KubernetesError",
  "resource_name": "bmh-node-001",
  "timestamp": "2024-01-15T14:30:00Z"
}
```

#### Examples

**Provision Request:**
```bash
curl -X POST http://localhost:5001/webhook \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: abc123..." \
  -d '{
    "eventType": "EVENT_START",
    "resourceName": "bmh-node-001",
    "userData": "I2Nsb3VkLWNvbmZpZwp1c2VyczoKICAtIG5hbWU6IGRlZmF1bHQ=",
    "timestamp": "2024-01-15T14:30:00Z"
  }'
```

**Deprovision Request:**
```bash
curl -X POST http://localhost:5001/webhook \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: def456..." \
  -d '{
    "eventType": "EVENT_END",
    "resourceName": "bmh-node-001",
    "timestamp": "2024-01-15T16:30:00Z"
  }'
```

### GET /healthz

Health check endpoint for monitoring and load balancers.

#### Request

```
GET /healthz
```

No parameters or headers required.

#### Response

**Success (200 OK):**
```json
{
  "status": "ok",
  "timestamp": "2024-01-15T14:30:00Z"
}
```

#### Example

```bash
curl http://localhost:5001/healthz
```

## Error Codes

| Status Code | Error Type | Description |
|-------------|------------|-------------|
| 400 | ValidationError | Invalid request payload or missing required fields |
| 401 | SecurityError | Invalid or missing webhook signature |
| 404 | ResourceNotFound | BareMetalHost resource not found in cluster |
| 422 | ValidationError | Request validation failed |
| 500 | KubernetesError | Kubernetes operation failed |
| 500 | ConfigurationError | Service configuration error |

## Rate Limiting

Currently, no rate limiting is implemented. Consider implementing rate limiting in production environments through:

- Ingress controller rate limiting
- Application-level rate limiting
- Kubernetes NetworkPolicies

## Monitoring

### Metrics

The service provides structured logging for monitoring:

- Request/response logging
- Error tracking
- Performance metrics
- Resource operation tracking

### Health Checks

The `/healthz` endpoint provides basic health status. For production deployments, consider implementing:

- Readiness probes
- Liveness probes
- Dependency health checks

## OpenAPI Documentation

The service provides automatic API documentation:

- **Swagger UI**: `http://localhost:5001/docs`
- **ReDoc**: `http://localhost:5001/redoc`
- **OpenAPI JSON**: `http://localhost:5001/openapi.json`