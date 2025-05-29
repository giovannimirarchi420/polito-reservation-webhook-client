# Documentation Index

Welcome to the comprehensive documentation for the Polito Reservation Webhook Client. This index provides an overview of all available documentation and guides you to the right resource based on your needs.

## 📖 Documentation Overview

This documentation is organized into several key areas:

### 🚀 Getting Started
- **[README](../README.md)**: Project overview, quick start, and basic usage
- **[Configuration Guide](CONFIGURATION.md)**: Complete configuration reference
- **[Deployment Guide](DEPLOYMENT.md)**: Production deployment instructions

### 🏗️ Technical Deep Dive
- **[Architecture Documentation](ARCHITECTURE.md)**: System design and component relationships
- **[API Reference](API.md)**: Complete API documentation with examples
- **[Development Guide](DEVELOPMENT.md)**: Developer setup and contribution guidelines

### 🔧 Operations & Maintenance
- **[Troubleshooting Guide](TROUBLESHOOTING.md)**: Common issues and solutions
- **[Changelog](../CHANGELOG.md)**: Version history and migration guides

## 🎯 Documentation by Role

### For System Administrators

**Getting the service running in production:**

1. **Start Here**: [README](../README.md) - Understanding what the service does
2. **Configuration**: [Configuration Guide](CONFIGURATION.md) - Set up environment variables and secrets
3. **Deployment**: [Deployment Guide](DEPLOYMENT.md) - Deploy to Kubernetes or Docker
4. **Operations**: [Troubleshooting Guide](TROUBLESHOOTING.md) - Handle common issues

**Key Sections:**
- [Production Deployment](DEPLOYMENT.md#kubernetes-deployment)
- [Security Configuration](CONFIGURATION.md#security-configuration)
- [Monitoring Setup](TROUBLESHOOTING.md#performance-monitoring)

### For Developers

**Contributing to or extending the service:**

1. **Architecture**: [Architecture Documentation](ARCHITECTURE.md) - Understand the system design
2. **Development Setup**: [Development Guide](DEVELOPMENT.md) - Local environment setup
3. **API Understanding**: [API Reference](API.md) - How the service APIs work
4. **Configuration**: [Configuration Guide](CONFIGURATION.md) - Environment setup

**Key Sections:**
- [Development Environment Setup](DEVELOPMENT.md#development-environment-setup)
- [Code Organization](DEVELOPMENT.md#code-organization)
- [Testing Strategy](DEVELOPMENT.md#testing-strategy)
- [Contributing Guidelines](DEVELOPMENT.md#contributing-guidelines)

### For Integration Teams

**Integrating with the webhook client:**

1. **API Reference**: [API Reference](API.md) - Complete API documentation
2. **Security**: [Configuration Guide](CONFIGURATION.md#security-configuration) - Webhook signature setup
3. **Examples**: [API Reference](API.md#sdk-examples) - SDK examples in multiple languages

**Key Sections:**
- [Webhook Endpoint](API.md#post-webhook)
- [Authentication](API.md#authentication)
- [SDK Examples](API.md#sdk-examples)

### For DevOps Engineers

**Operating and scaling the service:**

1. **Deployment**: [Deployment Guide](DEPLOYMENT.md) - Complete deployment instructions
2. **Configuration**: [Configuration Guide](CONFIGURATION.md) - Production configuration
3. **Monitoring**: [Troubleshooting Guide](TROUBLESHOOTING.md) - Monitoring and debugging
4. **Architecture**: [Architecture Documentation](ARCHITECTURE.md) - Scalability considerations

**Key Sections:**
- [Kubernetes Deployment](DEPLOYMENT.md#kubernetes-deployment)
- [Production Considerations](DEPLOYMENT.md#production-considerations)
- [Scaling Considerations](DEPLOYMENT.md#scaling-considerations)
- [Emergency Procedures](TROUBLESHOOTING.md#emergency-procedures)

## 📋 Quick Reference

### Essential Commands

```bash
# Health check
curl http://localhost:5001/healthz

# Send webhook event
curl -X POST http://localhost:5001/webhook \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: sha256=..." \
  -d '{"eventType": "EVENT_START", "resourceName": "bmh-node-001"}'

# Check logs
kubectl logs -f deployment/webhook-client -n webhook-client

# Scale service
kubectl scale deployment webhook-client --replicas=3 -n webhook-client
```

### Configuration Quick Start

```bash
# Required environment variables
export PROVISION_IMAGE="http://your-server/images/provision.iso"
export K8S_NAMESPACE="metal3-system"
export WEBHOOK_SECRET="your-secure-secret"

# Optional but recommended
export LOG_LEVEL="INFO"
export PORT="5001"
```

### Troubleshooting Quick Checks

```bash
# Check service status
kubectl get pods -n webhook-client
kubectl describe deployment webhook-client -n webhook-client

# Test connectivity
kubectl port-forward svc/webhook-client 5001:5001 -n webhook-client

# Check logs for errors
kubectl logs deployment/webhook-client -n webhook-client | grep ERROR
```

## 🔍 Finding Information

### By Topic

| Topic | Primary Document | Additional References |
|-------|------------------|----------------------|
| **Installation** | [Deployment Guide](DEPLOYMENT.md) | [README](../README.md), [Configuration](CONFIGURATION.md) |
| **Configuration** | [Configuration Guide](CONFIGURATION.md) | [Deployment Guide](DEPLOYMENT.md) |
| **API Usage** | [API Reference](API.md) | [Development Guide](DEVELOPMENT.md) |
| **Architecture** | [Architecture Documentation](ARCHITECTURE.md) | [Development Guide](DEVELOPMENT.md) |
| **Troubleshooting** | [Troubleshooting Guide](TROUBLESHOOTING.md) | [Configuration](CONFIGURATION.md) |
| **Development** | [Development Guide](DEVELOPMENT.md) | [Architecture](ARCHITECTURE.md) |

### By Problem

| Problem | Solution Location |
|---------|------------------|
| Service won't start | [Troubleshooting Guide](TROUBLESHOOTING.md#configuration-issues) |
| Authentication errors | [Troubleshooting Guide](TROUBLESHOOTING.md#authentication-and-authorization-issues) |
| Webhook signature fails | [API Reference](API.md#authentication) |
| Performance issues | [Troubleshooting Guide](TROUBLESHOOTING.md#performance-issues) |
| Kubernetes errors | [Troubleshooting Guide](TROUBLESHOOTING.md#resource-management-issues) |
| Configuration questions | [Configuration Guide](CONFIGURATION.md) |

## 📚 Documentation Standards

### Format
- **Markdown**: All documentation is written in GitHub-flavored Markdown
- **Structure**: Hierarchical organization with clear headings
- **Examples**: Practical examples for all concepts
- **Code Blocks**: Syntax highlighting for shell commands and code

### Conventions
- **File Names**: UPPERCASE.md for main documentation files
- **Headings**: Use emoji prefixes for section identification
- **Links**: Relative links between documentation files
- **Code**: Inline code for commands, code blocks for examples

### Maintenance
- **Version Control**: All documentation is version controlled with the code
- **Updates**: Documentation is updated with each feature change
- **Review**: Documentation changes go through the same review process as code
- **Testing**: Examples and commands are tested for accuracy

## 🔄 Documentation Lifecycle

### 1. Creation
- New features require documentation updates
- API changes require API documentation updates
- Configuration changes require configuration guide updates

### 2. Review
- Documentation changes are reviewed with code changes
- Technical accuracy is verified
- Examples are tested

### 3. Publication
- Documentation is published with releases
- Changes are noted in the changelog
- Migration guides are provided for breaking changes

### 4. Maintenance
- Regular review for accuracy
- Update examples with new versions
- Archive obsolete information

## 📞 Getting Help

### Self-Service Resources

1. **Search this documentation** for your specific issue
2. **Check the [Troubleshooting Guide](TROUBLESHOOTING.md)** for common problems
3. **Review the [API Reference](API.md)** for integration questions
4. **Consult the [Configuration Guide](CONFIGURATION.md)** for setup issues

### Support Channels

1. **GitHub Issues**: For bugs, feature requests, and technical questions
2. **Documentation Issues**: For improvements to this documentation
3. **Security Issues**: For security-related concerns (use private reporting)

### Contributing to Documentation

We welcome improvements to this documentation! See the [Development Guide](DEVELOPMENT.md#contributing-guidelines) for information on how to contribute.

**Types of contributions we welcome:**
- **Clarifications**: Making existing content clearer
- **Examples**: Additional practical examples
- **Corrections**: Fixing errors or outdated information
- **New Content**: Documentation for new features or use cases

## 🎯 Next Steps

Based on your role, here are suggested next steps:

### New Users
1. Read the [README](../README.md) for project overview
2. Follow the [Quick Start](../README.md#quick-start) guide
3. Set up your [Configuration](CONFIGURATION.md)

### Developers
1. Review the [Architecture Documentation](ARCHITECTURE.md)
2. Set up your [Development Environment](DEVELOPMENT.md#development-environment-setup)
3. Understand the [API Reference](API.md)

### Operators
1. Plan your [Deployment Strategy](DEPLOYMENT.md)
2. Configure [Production Settings](CONFIGURATION.md)
3. Set up [Monitoring](TROUBLESHOOTING.md#performance-monitoring)

---

**Last Updated**: May 29, 2025
**Documentation Version**: 1.0.0
**Service Version**: 1.0.0
