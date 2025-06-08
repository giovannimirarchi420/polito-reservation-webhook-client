# Troubleshooting Guide

## Overview

This guide provides solutions to common issues encountered when deploying and operating the Polito Reservation Webhook Client.

## Common Issues

### 1. Authentication and Authorization Issues

#### Issue: "Forbidden" errors when accessing Kubernetes resources

**Symptoms:**
```
ERROR: Failed to patch BareMetalHost: Forbidden
kubernetes.client.exceptions.ApiException: (403)
```

**Root Causes:**
- Insufficient RBAC permissions
- Wrong service account configuration
- Incorrect namespace access

**Solutions:**

1. **Check RBAC permissions:**
   ```bash
   # Verify service account exists
   kubectl get serviceaccount webhook-client -n webhook-client
   
   # Check role bindings
   kubectl get rolebinding -n metal3-system | grep webhook-client
   
   # Test permissions
   kubectl auth can-i get baremetalhosts \
     --as=system:serviceaccount:webhook-client:webhook-client \
     -n metal3-system
   ```

2. **Verify RBAC configuration:**
   ```yaml
   # Ensure role has correct permissions
   apiVersion: rbac.authorization.k8s.io/v1
   kind: Role
   metadata:
     name: webhook-client-role
     namespace: metal3-system
   rules:
   - apiGroups: ["metal3.io"]
     resources: ["baremetalhosts"]
     verbs: ["get", "list", "patch"]
   - apiGroups: [""]
     resources: ["secrets"]
     verbs: ["get", "create", "update", "delete"]
   ```

3. **Fix service account binding:**
   ```bash
   # Recreate role binding
   kubectl delete rolebinding webhook-client-binding -n metal3-system
   kubectl apply -f k8s/rbac.yaml
   ```

#### Issue: "Unauthorized" errors in local development

**Symptoms:**
```
ERROR: Unauthorized access to Kubernetes cluster
kubernetes.config.config_exception.ConfigException
```

**Solutions:**

1. **Check kubeconfig:**
   ```bash
   # Verify current context
   kubectl config current-context
   
   # Test cluster access
   kubectl get nodes
   
   # Check kubeconfig path
   echo $KUBECONFIG
   ```

2. **Refresh authentication:**
   ```bash
   # For cloud providers, refresh tokens
   # AWS EKS
   aws eks update-kubeconfig --region <region> --name <cluster-name>
   
   # Google GKE
   gcloud container clusters get-credentials <cluster-name> --zone <zone>
   ```

### 2. Configuration Issues

#### Issue: Service fails to start with configuration errors

**Symptoms:**
```
ERROR: ConfigurationError: PROVISION_IMAGE is required
```

**Solutions:**

1. **Verify environment variables:**
   ```bash
   # Check required variables
   env | grep -E "K8S_|BMH_|PROVISION_|WEBHOOK_"
   
   # In Kubernetes pod
   kubectl exec deployment/webhook-client -n webhook-client -- env | grep -E "K8S_|BMH_"
   ```

2. **Check secret and configmap:**
   ```bash
   # Verify secret exists and has correct keys
   kubectl get secret webhook-client-secret -n webhook-client -o yaml
   
   # Check configmap
   kubectl get configmap webhook-client-config -n webhook-client -o yaml
   ```

3. **Validate configuration values:**
   ```bash
   # Decode base64 secrets
   kubectl get secret webhook-client-secret -n webhook-client -o jsonpath='{.data.WEBHOOK_SECRET}' | base64 -d
   ```

#### Issue: Kubernetes connection failures

**Symptoms:**
```
ERROR: Failed to load Kubernetes configuration
ConnectionError: Unable to connect to Kubernetes API
```

**Solutions:**

1. **In-cluster configuration (production):**
   ```bash
   # Check service account token mount
   kubectl describe pod <pod-name> -n webhook-client
   
   # Verify token exists
   kubectl exec <pod-name> -n webhook-client -- ls -la /var/run/secrets/kubernetes.io/serviceaccount/
   ```

2. **Local development:**
   ```bash
   # Test direct connection
   kubectl cluster-info
   
   # Check network connectivity
   curl -k https://<k8s-api-server>/api/v1
   ```

### 3. Network and Connectivity Issues

#### Issue: Webhook endpoint not reachable

**Symptoms:**
```
Connection refused when sending webhook requests
curl: (7) Failed to connect to localhost port 5001
```

**Solutions:**

1. **Check service status:**
   ```bash
   # Verify pod is running
   kubectl get pods -n webhook-client
   
   # Check pod logs
   kubectl logs deployment/webhook-client -n webhook-client
   
   # Check service endpoints
   kubectl get endpoints webhook-client -n webhook-client
   ```

2. **Test internal connectivity:**
   ```bash
   # Port forward for testing
   kubectl port-forward svc/webhook-client 5001:5001 -n webhook-client
   
   # Test from another pod
   kubectl run test-pod --image=curlimages/curl -it --rm -- \
     curl http://webhook-client.webhook-client.svc.cluster.local:5001/healthz
   ```

3. **Check ingress configuration:**
   ```bash
   # Verify ingress
   kubectl get ingress -n webhook-client
   kubectl describe ingress webhook-client-ingress -n webhook-client
   
   # Check ingress controller logs
   kubectl logs -n ingress-nginx deployment/ingress-nginx-controller
   ```

#### Issue: External webhook requests failing

**Symptoms:**
```
webhook signature verification failed
401 Unauthorized
```

**Solutions:**

1. **Verify signature generation:**
   ```python
   import hmac
   import hashlib
   
   def test_signature(payload: str, secret: str):
       signature = hmac.new(
           secret.encode('utf-8'),
           payload.encode('utf-8'),
           hashlib.sha256
       ).hexdigest()
       return f"sha256={signature}"
   
   # Test with actual values
   print(test_signature("test payload", "your-secret"))
   ```

2. **Check webhook secret:**
   ```bash
   # Compare secrets between sender and receiver
   kubectl get secret webhook-client-secret -n webhook-client -o jsonpath='{.data.WEBHOOK_SECRET}' | base64 -d
   ```

### 4. Resource Management Issues

#### Issue: BareMetalHost resources not found

**Symptoms:**
```
ERROR: BareMetalHost 'bmh-node-001' not found in namespace 'metal3-system'
```

**Solutions:**

1. **Verify resource exists:**
   ```bash
   # List all BareMetalHost resources
   kubectl get baremetalhosts -n metal3-system
   
   # Check specific resource
   kubectl get baremetalhosts bmh-node-001 -n metal3-system
   
   # Verify CRD is installed
   kubectl get crd baremetalhosts.metal3.io
   ```

2. **Check namespace configuration:**
   ```bash
   # Verify webhook client namespace config
   kubectl get configmap webhook-client-config -n webhook-client -o yaml | grep K8S_NAMESPACE
   ```

#### Issue: Secret management failures

**Symptoms:**
```
ERROR: Failed to create user data secret
secrets "bmh-node-001-user-data" already exists
```

**Solutions:**

1. **Clean up orphaned secrets:**
   ```bash
   # List user data secrets
   kubectl get secrets -n metal3-system | grep user-data
   
   # Delete specific secret
   kubectl delete secret bmh-node-001-user-data -n metal3-system
   ```

2. **Check secret ownership:**
   ```bash
   # Verify secret labels and annotations
   kubectl get secret bmh-node-001-user-data -n metal3-system -o yaml
   ```

### 5. Performance Issues

#### Issue: Slow webhook processing

**Symptoms:**
- Long response times
- Timeout errors
- High CPU/memory usage

**Solutions:**

1. **Check resource limits:**
   ```bash
   # View current resource usage
   kubectl top pods -n webhook-client
   
   # Check resource limits
   kubectl describe pod <pod-name> -n webhook-client | grep -A 10 Resources
   ```

2. **Optimize configuration:**
   ```yaml
   # Increase resource limits if needed
   resources:
     requests:
       memory: "256Mi"
       cpu: "200m"
     limits:
       memory: "512Mi"
       cpu: "500m"
   ```

3. **Scale horizontally:**
   ```bash
   # Increase replicas
   kubectl scale deployment webhook-client --replicas=3 -n webhook-client
   ```

### 6. Development Issues

#### Issue: Import errors in development

**Symptoms:**
```
ModuleNotFoundError: No module named 'app'
```

**Solutions:**

1. **Fix Python path:**
   ```bash
   # Ensure you're in the project root
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   
   # Or use relative imports
   python -m app.main
   ```

2. **Virtual environment setup:**
   ```bash
   # Recreate virtual environment
   rm -rf venv
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

#### Issue: Type checking errors

**Symptoms:**
```
mypy: error: Cannot find implementation or library stub
```

**Solutions:**

1. **Install type stubs:**
   ```bash
   pip install types-requests types-pyyaml
   ```

2. **Configure mypy:**
   ```ini
   # pyproject.toml
   [tool.mypy]
   ignore_missing_imports = true
   ```

## Debugging Tools

### 1. Log Analysis

```bash
# Follow logs in real-time
kubectl logs -f deployment/webhook-client -n webhook-client

# Get logs from all replicas
kubectl logs -l app=webhook-client -n webhook-client --tail=100

# Filter logs by level
kubectl logs deployment/webhook-client -n webhook-client | grep ERROR
```

### 2. Health Checks

```bash
# Test health endpoint
curl http://localhost:5001/healthz

# Via port forward
kubectl port-forward svc/webhook-client 5001:5001 -n webhook-client &
curl http://localhost:5001/healthz
```

### 3. Network Diagnostics

```bash
# Test DNS resolution
kubectl exec -it <pod-name> -n webhook-client -- nslookup kubernetes.default.svc.cluster.local

# Test network connectivity
kubectl exec -it <pod-name> -n webhook-client -- nc -zv <target-host> <port>
```

### 4. Resource Inspection

```bash
# Detailed pod information
kubectl describe pod <pod-name> -n webhook-client

# Events
kubectl get events -n webhook-client --sort-by='.lastTimestamp'

# Resource usage
kubectl top pod <pod-name> -n webhook-client
```

## Performance Monitoring

### 1. Application Metrics

```bash
# Monitor request processing time
kubectl logs deployment/webhook-client -n webhook-client | grep "processing time"

# Monitor error rates
kubectl logs deployment/webhook-client -n webhook-client | grep ERROR | wc -l
```

### 2. Resource Monitoring

```bash
# CPU and memory usage
kubectl top pods -n webhook-client

# Persistent monitoring
watch kubectl top pods -n webhook-client
```

### 3. Network Monitoring

```bash
# Monitor ingress traffic
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller | grep webhook-client
```

## Emergency Procedures

### 1. Service Recovery

```bash
# Restart deployment
kubectl rollout restart deployment/webhook-client -n webhook-client

# Scale down and up
kubectl scale deployment webhook-client --replicas=0 -n webhook-client
kubectl scale deployment webhook-client --replicas=2 -n webhook-client
```

### 2. Configuration Reset

```bash
# Backup current configuration
kubectl get secret webhook-client-secret -n webhook-client -o yaml > secret-backup.yaml
kubectl get configmap webhook-client-config -n webhook-client -o yaml > config-backup.yaml

# Reset to default configuration
kubectl delete secret webhook-client-secret -n webhook-client
kubectl delete configmap webhook-client-config -n webhook-client
kubectl apply -f k8s/secret.yaml -f k8s/configmap.yaml
```

### 3. Complete Reinstall

```bash
# Remove all resources
kubectl delete namespace webhook-client

# Reinstall
kubectl apply -f k8s/
```

## Getting Help

### 1. Information Gathering

Before seeking help, gather this information:

```bash
# System information
kubectl version
kubectl cluster-info

# Application logs
kubectl logs deployment/webhook-client -n webhook-client --tail=50

# Configuration
kubectl get configmap webhook-client-config -n webhook-client -o yaml
kubectl describe deployment webhook-client -n webhook-client

# Resource status
kubectl get all -n webhook-client
kubectl get events -n webhook-client --sort-by='.lastTimestamp'
```

### 2. Support Channels

1. **GitHub Issues**: For bugs and feature requests
2. **Documentation**: Check all files in `/docs` directory
3. **API Documentation**: Visit `/docs` endpoint for API reference
4. **Logs**: Enable debug logging for detailed troubleshooting

### 3. Debug Configuration

```yaml
# Enable debug mode
env:
- name: LOG_LEVEL
  value: "DEBUG"
- name: PYTHONDEBUG
  value: "1"
```

## Prevention

### 1. Monitoring Setup

- Set up log aggregation (ELK stack, Fluentd)
- Configure alerting for error rates
- Monitor resource usage trends
- Set up health check monitoring

### 2. Testing

- Run integration tests before deployment
- Test with production-like data
- Validate RBAC permissions
- Test network connectivity

### 3. Documentation

- Keep deployment documentation up to date
- Document configuration changes
- Maintain runbooks for common procedures
- Regular backup of configurations
