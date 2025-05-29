# Architecture Documentation

## Overview

The Polito Reservation Webhook Client is designed following clean architecture principles with clear separation of concerns, dependency inversion, and modular design patterns.

## Architecture Layers

### 1. API Layer (`app/api.py`)

The presentation layer handles HTTP requests and responses.

**Responsibilities:**
- HTTP request/response handling
- Input validation
- Authentication and authorization
- Error handling and formatting
- Route definitions

**Key Components:**
- **Router**: FastAPI router with endpoint definitions
- **Handler Functions**: Event-specific request handlers
- **Helper Functions**: Reusable utilities for response formatting

**Design Patterns:**
- **Controller Pattern**: Separates HTTP concerns from business logic
- **Decorator Pattern**: Used for dependency injection and middleware

### 2. Service Layer (`app/services/`)

Contains business logic and external service integrations.

#### Security Service (`security.py`)

**Purpose**: Handles webhook signature verification and security concerns.

**Key Classes:**
- `SecurityError`: Custom exception for security-related errors
- `WebhookSecurity`: Main security service class

**Features:**
- HMAC-SHA256 signature generation and verification
- Constant-time comparison to prevent timing attacks
- Configurable secret management

#### Kubernetes Service (`kubernetes.py`)

**Purpose**: Manages Kubernetes resource operations.

**Key Classes:**
- `KubernetesError`: Custom exception for K8s operations
- `UserDataSecretManager`: Handles cloud-config secrets
- `BareMetalHostManager`: Manages BareMetalHost resources

**Features:**
- Resource patching with strategic merge
- Secret lifecycle management
- Error handling and retry logic
- Configuration-driven resource management

### 3. Model Layer (`app/models.py`)

Defines data structures and validation rules.

**Key Models:**
- `WebhookPayload`: Incoming webhook data structure
- `WebhookResponse`: Standardized response format
- `ErrorResponse`: Error response structure

**Features:**
- Pydantic v2 validation
- JSON schema generation
- Type safety and serialization
- Documentation and examples

### 4. Configuration Layer (`app/config.py`)

Centralized configuration management.

**Key Classes:**
- `ConfigurationError`: Configuration-related exceptions
- `LoggingConfig`: Logging setup and management
- `KubernetesConfig`: K8s client configuration
- `AppConfig`: Main application configuration

**Features:**
- Environment variable management
- Configuration validation
- Default value handling
- Type-safe configuration access

## Design Principles Applied

### 1. Single Responsibility Principle (SRP)

Each class and module has a single, well-defined responsibility:

- `WebhookSecurity`: Only handles security concerns
- `BareMetalHostManager`: Only manages BMH resources
- `UserDataSecretManager`: Only handles secret operations

### 2. Open/Closed Principle (OCP)

Classes are open for extension but closed for modification:

- Service interfaces allow for easy implementation swapping
- Configuration classes can be extended without modifying core logic
- Handler functions can be added without changing existing ones

### 3. Dependency Inversion Principle (DIP)

High-level modules don't depend on low-level modules:

- API layer depends on service abstractions, not implementations
- Services depend on configuration interfaces
- Business logic is isolated from infrastructure concerns

### 4. Interface Segregation Principle (ISP)

Clients depend only on the interfaces they use:

- Separate managers for different resource types
- Focused service interfaces
- Minimal dependencies between components

## Data Flow

```
┌─────────────────┐
│   HTTP Request  │
└─────────┬───────┘
          │
┌─────────▼───────┐
│   API Router    │  ← Handles routing and validation
└─────────┬───────┘
          │
┌─────────▼───────┐
│ Event Handlers  │  ← Process specific event types
└─────────┬───────┘
          │
┌─────────▼───────┐
│ Security Service│  ← Verify webhook signatures
└─────────┬───────┘
          │
┌─────────▼───────┐
│ K8s Services    │  ← Manage Kubernetes resources
└─────────┬───────┘
          │
┌─────────▼───────┐
│   HTTP Response │
└─────────────────┘
```

## Error Handling Strategy

### Custom Exception Hierarchy

```python
Exception
├── ConfigurationError      # Configuration issues
├── SecurityError          # Authentication/authorization
└── KubernetesError        # Kubernetes operations
    ├── ResourceNotFound   # Resource doesn't exist
    ├── PatchError         # Failed to patch resource
    └── SecretError        # Secret management issues
```

### Error Propagation

1. **Service Layer**: Raises domain-specific exceptions
2. **API Layer**: Catches exceptions and formats HTTP responses
3. **Logging**: All errors are logged with appropriate context
4. **Client**: Receives structured error responses

## Security Considerations

### Authentication

- HMAC-SHA256 signature verification
- Shared secret management
- Constant-time comparison

### Authorization

- Kubernetes RBAC integration
- Service account token authentication
- Minimal permission principle

### Data Protection

- Sensitive data handled securely
- No secret logging
- Secure secret storage in Kubernetes

## Scalability Considerations

### Stateless Design

- No persistent state in the application
- Kubernetes client connection pooling
- Session-less request handling

### Resource Management

- Efficient Kubernetes API usage
- Strategic merge patching
- Connection reuse

### Monitoring

- Health check endpoints
- Structured logging
- Error metrics collection

## Testing Strategy

### Unit Testing

- Test individual components in isolation
- Mock external dependencies
- Test error conditions and edge cases

### Integration Testing

- Test service interactions
- Test Kubernetes integration
- Test webhook signature verification

### End-to-End Testing

- Test complete workflow
- Test with real Kubernetes cluster
- Test error recovery scenarios

## Deployment Considerations

### Container Design

- Multi-stage Docker build
- Minimal base image
- Non-root user execution

### Kubernetes Deployment

- Resource limits and requests
- Health checks and readiness probes
- RBAC configuration

### Configuration Management

- Environment-based configuration
- Secret management through K8s secrets
- ConfigMap for non-sensitive configuration
