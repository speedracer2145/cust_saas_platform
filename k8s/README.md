# Kubernetes Deployment for RoBERTa Sentiment Analysis Service

This directory contains Kubernetes manifests for deploying the RoBERTa Sentiment Analysis Service as pods in a cluster.

## Prerequisites

- Kubernetes cluster (v1.20+)
- kubectl configured to access your cluster
- Docker registry access (for pushing the container image)
- Persistent volume support in your cluster
- Optional: NVIDIA GPU support for faster inference

## Quick Deployment

### 1. Build and Push Docker Image

```bash
# Build the image
docker build -t your-registry/roberta-sentiment-service:latest .

# Push to registry
docker push your-registry/roberta-sentiment-service:latest
```

### 2. Update Image Reference

Edit `kustomization.yaml` to point to your image:

```yaml
images:
- name: roberta-sentiment-service
  newName: your-registry/roberta-sentiment-service
  newTag: latest
```

### 3. Deploy to Cluster

```bash
# Deploy all resources
kubectl apply -k k8s/

# Or deploy individually
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/hpa.yaml
```

### 4. Verify Deployment

```bash
# Check pods
kubectl get pods -n roberta-sentiment

# Check services
kubectl get svc -n roberta-sentiment

# Check logs
kubectl logs -f deployment/roberta-sentiment-service -n roberta-sentiment
```

## Configuration

### Environment Variables

The service is configured via ConfigMap (`configmap.yaml`):

- `MODEL_NAME`: Hugging Face model identifier
- `HOST`: Service host (0.0.0.0 for all interfaces)
- `PORT`: Service port (8000)
- `LOG_LEVEL`: Logging level (info, debug, warning, error)
- `BATCH_SIZE`: Batch processing size (32)
- `MAX_BATCH_SIZE`: Maximum batch size (1000)
- `USE_CUDA`: Enable GPU acceleration (true/false)
- `TORCH_DTYPE`: PyTorch data type (auto, float16, float32)
- `DATABASE_PATH`: SQLite database path
- `CORS_ORIGINS`: CORS allowed origins

### Resource Requirements

The deployment requests:
- **CPU**: 1000m (1 core)
- **Memory**: 2Gi
- **GPU**: 1 NVIDIA GPU (if available)

Limits:
- **CPU**: 2000m (2 cores)
- **Memory**: 4Gi
- **GPU**: 1 NVIDIA GPU

### Scaling

The service includes Horizontal Pod Autoscaler (HPA) that:
- Scales between 2-10 replicas
- Triggers on CPU (>70%) and Memory (>80%) usage
- Includes scale-up/down policies for smooth scaling

## Accessing the Service

### Cluster Access

```bash
# Port forward for local access
kubectl port-forward svc/roberta-sentiment-service 8000:8000 -n roberta-sentiment

# Access via NodePort (if enabled)
curl http://your-node-ip:30080/health
```

### Ingress Access

If using ingress, update the host in `ingress.yaml` and access via:

```bash
# Add to /etc/hosts
your-domain roberta-sentiment.local

# Access the service
curl http://roberta-sentiment.local/health
```

## Monitoring and Health Checks

### Health Endpoints

- **Liveness Probe**: `/health` - checks if service is running
- **Readiness Probe**: `/health` - checks if service is ready to accept traffic
- **Startup Probe**: `/health` - allows up to 5 minutes for model loading

### Logs

```bash
# View logs
kubectl logs -f deployment/roberta-sentiment-service -n roberta-sentiment

# View logs from specific pod
kubectl logs -f pod/roberta-sentiment-service-xxx -n roberta-sentiment
```

### Metrics

The service exposes metrics at `/metrics` endpoint for monitoring.

## Data Persistence

The service uses a PersistentVolumeClaim for data storage:
- **Size**: 10Gi
- **Access Mode**: ReadWriteOnce
- **Storage Class**: standard (adjust for your cluster)

## Security Considerations

### Network Policies

Consider adding NetworkPolicy for network segmentation:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: roberta-sentiment-netpol
  namespace: roberta-sentiment
spec:
  podSelector:
    matchLabels:
      app: roberta-sentiment-service
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
```

### RBAC

For production, consider adding RBAC:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: roberta-sentiment-sa
  namespace: roberta-sentiment
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: roberta-sentiment-role
  namespace: roberta-sentiment
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list"]
```

## Troubleshooting

### Common Issues

1. **Pod CrashLoopBackOff**: Check logs for model download issues
2. **OutOfMemory**: Increase memory limits or reduce batch size
3. **GPU Issues**: Ensure NVIDIA device plugin is installed
4. **Storage Issues**: Check PVC status and storage class

### Debug Commands

```bash
# Describe pod for events
kubectl describe pod pod-name -n roberta-sentiment

# Check PVC status
kubectl get pvc -n roberta-sentiment

# Check node resources
kubectl describe nodes

# Check HPA status
kubectl get hpa -n roberta-sentiment
```

## Production Considerations

1. **Resource Limits**: Adjust based on your workload
2. **Replica Count**: Start with 2-3 replicas, scale based on demand
3. **Storage**: Use appropriate storage class for your environment
4. **Monitoring**: Integrate with Prometheus/Grafana
5. **Logging**: Use centralized logging (ELK stack, Fluentd)
6. **Security**: Implement proper RBAC and network policies
7. **Backup**: Regular backup of persistent data
