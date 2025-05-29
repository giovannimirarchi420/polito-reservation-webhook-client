# Development Guide

## Overview

This guide provides comprehensive information for developers working on the Polito Reservation Webhook Client, including setup, code organization, testing strategies, and contribution guidelines.

## Development Environment Setup

### Prerequisites

- Python 3.10 or higher
- pip package manager
- Git version control
- Docker (optional but recommended)
- kubectl and access to a Kubernetes cluster (for integration testing)
- IDE/Editor with Python support (VS Code, PyCharm, etc.)

### Initial Setup

1. **Clone and Environment Setup**
   ```bash
   git clone <repository-url>
   cd polito-reservation-webhook-client
   
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # macOS/Linux
   # venv\Scripts\activate   # Windows
   ```

2. **Install Dependencies**
   ```bash
   # Install runtime dependencies
   pip install -r requirements.txt
   
   # Install development dependencies
   pip install -r requirements-dev.txt
   ```

3. **Pre-commit Hooks** (recommended)
   ```bash
   pre-commit install
   ```

### Development Dependencies

Create `requirements-dev.txt`:

```txt
# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
httpx>=0.24.0

# Code Quality
black>=23.0.0
isort>=5.12.0
flake8>=6.0.0
mypy>=1.5.0

# Development Tools
pre-commit>=3.3.0
uvicorn[standard]>=0.24.0

# Documentation
mkdocs>=1.5.0
mkdocs-material>=9.2.0
```

## Project Structure

```
polito-reservation-webhook-client/
├── app/                          # Main application package
│   ├── __init__.py              # Package initialization
│   ├── main.py                  # Application entry point
│   ├── api.py                   # API route handlers
│   ├── config.py                # Configuration management
│   ├── models.py                # Pydantic models
│   └── services/                # Business logic services
│       ├── __init__.py
│       ├── kubernetes.py        # Kubernetes operations
│       └── security.py          # Security operations
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── fixtures/                # Test fixtures
├── docs/                        # Documentation
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── DEPLOYMENT.md
│   └── DEVELOPMENT.md
├── k8s/                         # Kubernetes manifests
├── Dockerfile                   # Container definition
├── requirements.txt             # Runtime dependencies
├── requirements-dev.txt         # Development dependencies
├── pyproject.toml              # Project configuration
├── .gitignore                  # Git ignore rules
├── .pre-commit-config.yaml     # Pre-commit configuration
└── README.md                   # Project documentation
```

## Code Organization

### Module Responsibilities

#### `app/main.py`
- Application factory function
- FastAPI app configuration
- Server startup logic

#### `app/api.py`
- HTTP request/response handling
- Route definitions
- Input validation
- Error handling

#### `app/models.py`
- Pydantic data models
- Request/response schemas
- Validation rules

#### `app/config.py`
- Configuration management
- Environment variable handling
- Logging setup

#### `app/services/kubernetes.py`
- Kubernetes API interactions
- Resource management
- Custom resource operations

#### `app/services/security.py`
- Webhook signature verification
- Security utilities
- Authentication logic

### Design Patterns

#### 1. Dependency Injection

```python
# Configuration injection
@router.post("/webhook")
async def webhook_handler(
    payload: WebhookPayload,
    request: Request,
    config: AppConfig = Depends(get_config)
):
    # Handler logic
```

#### 2. Factory Pattern

```python
def create_app() -> FastAPI:
    """Factory function for creating FastAPI app."""
    app = FastAPI(
        title="Resource Webhook Client",
        # ... configuration
    )
    return app
```

#### 3. Service Layer Pattern

```python
class BareMetalHostManager:
    """Service for managing BareMetalHost resources."""
    
    def __init__(self, config: KubernetesConfig):
        self.config = config
        # Initialize service
    
    async def provision_host(self, resource_name: str) -> Dict:
        # Business logic
```

## Development Workflow

### 1. Feature Development

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes
# ... develop feature

# Run tests
pytest

# Format code
black app/ tests/
isort app/ tests/

# Lint code
flake8 app/ tests/
mypy app/

# Commit changes
git add .
git commit -m "feat: add new feature"

# Push branch
git push origin feature/new-feature
```

### 2. Code Quality Checks

#### Formatting with Black

```bash
# Format all Python files
black app/ tests/

# Check formatting without making changes
black --check app/ tests/
```

#### Import Sorting with isort

```bash
# Sort imports
isort app/ tests/

# Check import sorting
isort --check-only app/ tests/
```

#### Linting with flake8

```bash
# Lint code
flake8 app/ tests/

# Configuration in setup.cfg
[flake8]
max-line-length = 88
exclude = __pycache__,venv
ignore = E203,W503
```

#### Type Checking with mypy

```bash
# Type check
mypy app/

# Configuration in pyproject.toml
[tool.mypy]
python_version = "3.10"
strict = true
```

### 3. Testing Strategy

#### Unit Tests

Test individual components in isolation:

```python
# tests/unit/test_security.py
import pytest
from app.services.security import WebhookSecurity

class TestWebhookSecurity:
    def test_signature_generation(self):
        security = WebhookSecurity("test-secret")
        payload = b"test payload"
        signature = security.generate_signature(payload)
        assert signature.startswith("sha256=")
    
    def test_signature_verification(self):
        security = WebhookSecurity("test-secret")
        payload = b"test payload"
        signature = security.generate_signature(payload)
        assert security.verify_signature(payload, signature)
```

#### Integration Tests

Test component interactions:

```python
# tests/integration/test_api.py
import pytest
from httpx import AsyncClient
from app.main import create_app

@pytest.mark.asyncio
async def test_webhook_endpoint():
    app = create_app()
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/webhook",
            json={
                "eventType": "EVENT_START",
                "resourceName": "test-bmh"
            }
        )
        assert response.status_code == 200
```

#### Test Configuration

```python
# tests/conftest.py
import pytest
from unittest.mock import Mock
from app.config import AppConfig

@pytest.fixture
def mock_config():
    config = Mock(spec=AppConfig)
    config.kubernetes.namespace = "test-namespace"
    config.provision_image = "test-image"
    return config

@pytest.fixture
def mock_k8s_client():
    return Mock()
```

#### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/unit/test_security.py

# Run tests with specific marker
pytest -m "not integration"

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

## Configuration Management

### Environment Variables

Create `.env` file for local development:

```bash
# .env
K8S_NAMESPACE=test-namespace
PROVISION_IMAGE=test://test-image
WEBHOOK_SECRET=test-secret
LOG_LEVEL=DEBUG
PORT=5001
```

Load in development:

```python
# For development only
from dotenv import load_dotenv
load_dotenv()
```

### Configuration Classes

```python
class AppConfig:
    """Main application configuration."""
    
    def __init__(self):
        self.kubernetes = KubernetesConfig()
        self.logging = LoggingConfig()
        self.webhook_secret = os.getenv("WEBHOOK_SECRET")
        self.provision_image = os.getenv("PROVISION_IMAGE", "default-image")
```

## Debugging

### Local Debugging

#### VS Code Configuration

Create `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: FastAPI",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "app.main:app",
                "--host",
                "0.0.0.0",
                "--port",
                "5001",
                "--reload"
            ],
            "env": {
                "K8S_NAMESPACE": "test-namespace",
                "LOG_LEVEL": "DEBUG"
            },
            "jinja": true,
            "justMyCode": false
        }
    ]
}
```

#### Debug Logging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Add debug points
logger = logging.getLogger(__name__)
logger.debug("Debug information: %s", data)
```

### Remote Debugging

#### Kubernetes Pod Debugging

```bash
# Access pod shell
kubectl exec -it <pod-name> -- /bin/sh

# View logs
kubectl logs -f <pod-name>

# Port forward for debugging
kubectl port-forward <pod-name> 5001:5001
```

#### Debug Container

Add debug tools to development image:

```dockerfile
# Dockerfile.dev
FROM python:3.10-slim

# Install debug tools
RUN pip install debugpy

# ... rest of Dockerfile

# Add debug endpoint
EXPOSE 5678
```

## Performance Optimization

### Profiling

```python
# Add profiling decorator
import cProfile
import functools

def profile(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        result = func(*args, **kwargs)
        profiler.disable()
        profiler.dump_stats(f"{func.__name__}.prof")
        return result
    return wrapper

@profile
async def expensive_operation():
    # Function to profile
    pass
```

### Monitoring

```python
# Add timing metrics
import time
from functools import wraps

def timed(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start
        logger.info(f"{func.__name__} took {duration:.2f}s")
        return result
    return wrapper
```

## Security Guidelines

### 1. Secret Management

```python
# Never log secrets
logger.info("Processing webhook for %s", payload.resource_name)
# NOT: logger.info("Webhook secret: %s", secret)

# Use environment variables for secrets
webhook_secret = os.getenv("WEBHOOK_SECRET")
if not webhook_secret:
    raise ConfigurationError("WEBHOOK_SECRET is required")
```

### 2. Input Validation

```python
# Use Pydantic for validation
class WebhookPayload(BaseModel):
    event_type: Literal["EVENT_START", "EVENT_END"]
    resource_name: str = Field(..., min_length=1, max_length=253)
    user_data: Optional[str] = Field(None, description="Base64 encoded user data")
```

### 3. Error Handling

```python
# Don't expose internal details
try:
    result = await kubernetes_operation()
except KubernetesError as e:
    logger.error("Kubernetes operation failed: %s", e)
    raise HTTPException(
        status_code=500,
        detail="Internal server error"
    )
```

## Documentation

### Docstring Standards

```python
def verify_signature(self, payload: bytes, signature: str) -> bool:
    """
    Verify webhook signature using HMAC-SHA256.
    
    Args:
        payload: Raw request payload bytes
        signature: Expected signature in format 'sha256=<hex>'
    
    Returns:
        True if signature is valid, False otherwise
    
    Raises:
        SecurityError: If signature format is invalid
    
    Example:
        >>> security = WebhookSecurity("secret")
        >>> security.verify_signature(b"payload", "sha256=abc123")
        True
    """
```

### API Documentation

Use Pydantic for automatic OpenAPI generation:

```python
class WebhookPayload(BaseModel):
    """Webhook payload for reservation events."""
    
    event_type: Literal["EVENT_START", "EVENT_END"] = Field(
        ...,
        description="Type of reservation event",
        example="EVENT_START"
    )
    resource_name: str = Field(
        ...,
        description="Name of the BareMetalHost resource",
        example="bmh-node-001"
    )
```

## Contributing Guidelines

### Code Review Checklist

- [ ] Code follows project style guidelines
- [ ] Tests are included and pass
- [ ] Documentation is updated
- [ ] No secrets or sensitive data in code
- [ ] Error handling is appropriate
- [ ] Logging is meaningful but not excessive
- [ ] Performance impact is considered

### Pull Request Process

1. Create feature branch from main
2. Implement changes with tests
3. Update documentation
4. Run full test suite
5. Create pull request with description
6. Address review feedback
7. Squash and merge

### Commit Message Format

```
type(scope): brief description

Longer description if needed

Fixes #issue-number
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `chore`

## Troubleshooting

### Common Development Issues

#### 1. Import Errors

```bash
# Ensure PYTHONPATH is set correctly
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or use relative imports
from .services import kubernetes
```

#### 2. Test Discovery

```bash
# Ensure test files start with test_
# tests/test_*.py or tests/*_test.py

# Check pytest configuration
pytest --collect-only
```

#### 3. Type Checking

```bash
# Install type stubs
pip install types-requests

# Ignore specific errors
# type: ignore[import]
```

### Development Tools

#### Useful Scripts

Create `scripts/dev.py`:

```python
#!/usr/bin/env python3
"""Development utility scripts."""

import subprocess
import sys

def format_code():
    """Format code with black and isort."""
    subprocess.run(["black", "app/", "tests/"])
    subprocess.run(["isort", "app/", "tests/"])

def run_tests():
    """Run test suite with coverage."""
    subprocess.run(["pytest", "--cov=app", "--cov-report=html"])

def lint():
    """Run linting checks."""
    subprocess.run(["flake8", "app/", "tests/"])
    subprocess.run(["mypy", "app/"])

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "format":
            format_code()
        elif command == "test":
            run_tests()
        elif command == "lint":
            lint()
        else:
            print(f"Unknown command: {command}")
    else:
        print("Usage: python scripts/dev.py [format|test|lint]")
```

#### Make Commands

Create `Makefile`:

```makefile
.PHONY: install test lint format clean

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test:
	pytest --cov=app

lint:
	flake8 app/ tests/
	mypy app/

format:
	black app/ tests/
	isort app/ tests/

clean:
	find . -type d -name __pycache__ -delete
	find . -name "*.pyc" -delete
	rm -rf .coverage htmlcov/ .pytest_cache/
```
