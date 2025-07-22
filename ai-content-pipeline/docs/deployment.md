# Deployment Guide
## AI Content Generation Pipeline

**Version**: 1.0  
**Last Updated**: January 2025

---

## 1. Deployment Overview

This guide covers deployment strategies for the AI Content Generation Pipeline across different environments:
- **Local Development**: Docker Compose setup
- **Staging**: Kubernetes on cloud providers
- **Production**: High-availability Kubernetes cluster

---

## 2. Prerequisites

### 2.1 Required Tools
```bash
# Check versions
docker --version          # 20.10+
docker-compose --version  # 1.29+
kubectl version          # 1.23+
terraform --version      # 1.0+
helm version            # 3.8+
```

### 2.2 Required Access
- Cloud provider account (AWS/GCP/Azure)
- Container registry access
- API keys for external services
- SSL certificates for domains

---

## 3. Local Development Deployment

### 3.1 Quick Start with Docker Compose
```bash
# Clone repository
git clone https://github.com/your-org/ai-content-pipeline.git
cd ai-content-pipeline

# Copy environment template
cp .env.example .env

# Configure environment variables
nano .env

# Start services
docker-compose up -d

# Check service health
docker-compose ps
docker-compose logs -f
```

### 3.2 Docker Compose Configuration
```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: ./api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/pipeline
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  worker:
    build: ./worker
    environment:
      - CELERY_BROKER_URL=redis://redis:6379
    depends_on:
      - redis
    deploy:
      replicas: 3

  db:
    image: postgres:14
    environment:
      - POSTGRES_DB=pipeline
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

---

## 4. Container Build & Registry

### 4.1 Build Images
```bash
# Build all images
make build-all

# Or build individually
docker build -t pipeline/api:latest ./api
docker build -t pipeline/worker:latest ./worker
docker build -t pipeline/frontend:latest ./frontend
```

### 4.2 Push to Registry
```bash
# AWS ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_REGISTRY
docker tag pipeline/api:latest $ECR_REGISTRY/pipeline/api:latest
docker push $ECR_REGISTRY/pipeline/api:latest

# Docker Hub
docker login
docker tag pipeline/api:latest yourusername/pipeline-api:latest
docker push yourusername/pipeline-api:latest
```

---

## 5. Kubernetes Deployment

### 5.1 Cluster Setup

#### AWS EKS
```bash
# Create cluster with eksctl
eksctl create cluster \
  --name content-pipeline \
  --region us-east-1 \
  --nodegroup-name workers \
  --node-type t3.large \
  --nodes 3 \
  --nodes-min 2 \
  --nodes-max 5
```

#### GKE
```bash
# Create cluster with gcloud
gcloud container clusters create content-pipeline \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type n1-standard-2 \
  --enable-autoscaling \
  --min-nodes 2 \
  --max-nodes 5
```

### 5.2 Kubernetes Manifests

#### Namespace
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: content-pipeline
```

#### API Deployment
```yaml
# k8s/api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: content-pipeline
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
      - name: api
        image: pipeline/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### Service & Ingress
```yaml
# k8s/api-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: api
  namespace: content-pipeline
spec:
  selector:
    app: api
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
  namespace: content-pipeline
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.contentpipeline.ai
    secretName: api-tls
  rules:
  - host: api.contentpipeline.ai
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api
            port:
              number: 80
```

### 5.3 Deploy to Kubernetes
```bash
# Apply all manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get all -n content-pipeline

# View logs
kubectl logs -f deployment/api -n content-pipeline
```

---

## 6. Helm Chart Deployment

### 6.1 Helm Chart Structure
```
helm/
├── Chart.yaml
├── values.yaml
├── templates/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── configmap.yaml
│   └── secrets.yaml
```

### 6.2 Install with Helm
```bash
# Add custom values
cat > custom-values.yaml <<EOF
api:
  replicas: 3
  image:
    repository: pipeline/api
    tag: v1.0.0
  resources:
    requests:
      memory: 512Mi
      cpu: 500m

worker:
  replicas: 5
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 10

redis:
  enabled: true
  persistence:
    size: 10Gi

postgresql:
  enabled: true
  persistence:
    size: 50Gi
EOF

# Install chart
helm install content-pipeline ./helm \
  -f custom-values.yaml \
  -n content-pipeline \
  --create-namespace
```

---

## 7. Infrastructure as Code (Terraform)

### 7.1 AWS Infrastructure
```hcl
# terraform/aws/main.tf
provider "aws" {
  region = var.region
}

# VPC
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  version = "3.14.0"
  
  name = "content-pipeline-vpc"
  cidr = "10.0.0.0/16"
  
  azs             = ["${var.region}a", "${var.region}b", "${var.region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
  
  enable_nat_gateway = true
  enable_vpn_gateway = true
  enable_dns_hostnames = true
}

# EKS Cluster
module "eks" {
  source = "terraform-aws-modules/eks/aws"
  version = "18.26.0"
  
  cluster_name    = "content-pipeline"
  cluster_version = "1.23"
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
  
  eks_managed_node_groups = {
    workers = {
      desired_capacity = 3
      max_capacity     = 10
      min_capacity     = 2
      
      instance_types = ["t3.large"]
    }
  }
}

# RDS Database
resource "aws_db_instance" "postgres" {
  identifier = "content-pipeline-db"
  
  engine         = "postgres"
  engine_version = "14.7"
  instance_class = "db.t3.medium"
  
  allocated_storage = 100
  storage_encrypted = true
  
  db_name  = "pipeline"
  username = var.db_username
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  deletion_protection = true
}

# S3 Buckets
resource "aws_s3_bucket" "media" {
  bucket = "content-pipeline-media-${var.environment}"
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    enabled = true
    
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }
    
    transition {
      days          = 90
      storage_class = "GLACIER"
    }
  }
}
```

### 7.2 Deploy Infrastructure
```bash
# Initialize Terraform
terraform init

# Plan deployment
terraform plan -out=tfplan

# Apply changes
terraform apply tfplan

# Get outputs
terraform output -json > infrastructure-outputs.json
```

---

## 8. CI/CD Pipeline

### 8.1 GitHub Actions
```yaml
# .github/workflows/deploy.yml
name: Deploy Pipeline

on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Run tests
      run: |
        docker-compose -f docker-compose.test.yml up --abort-on-container-exit

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v1
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-east-1
    
    - name: Build and push images
      run: |
        make build-all
        make push-all TAG=${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to Kubernetes
      run: |
        aws eks update-kubeconfig --name content-pipeline
        kubectl set image deployment/api api=pipeline/api:${{ github.sha }} -n content-pipeline
        kubectl rollout status deployment/api -n content-pipeline
```

---

## 9. Monitoring & Observability

### 9.1 Prometheus & Grafana
```bash
# Install Prometheus Operator
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n monitoring \
  --create-namespace

# Access Grafana
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
# Default login: admin/prom-operator
```

### 9.2 Application Metrics
```python
# Add to application code
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
video_generation_counter = Counter(
    'video_generations_total',
    'Total number of videos generated',
    ['status']
)

processing_time_histogram = Histogram(
    'video_processing_seconds',
    'Time spent processing videos'
)

queue_depth_gauge = Gauge(
    'job_queue_depth',
    'Number of jobs in queue'
)
```

---

## 10. Security Considerations

### 10.1 Secrets Management
```bash
# Create Kubernetes secrets
kubectl create secret generic api-secrets \
  --from-literal=elevenlabs-api-key=$ELEVENLABS_API_KEY \
  --from-literal=runway-api-key=$RUNWAY_API_KEY \
  -n content-pipeline

# Use AWS Secrets Manager
aws secretsmanager create-secret \
  --name content-pipeline/api-keys \
  --secret-string file://secrets.json
```

### 10.2 Network Policies
```yaml
# k8s/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-network-policy
  namespace: content-pipeline
spec:
  podSelector:
    matchLabels:
      app: api
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

---

## 11. Backup & Disaster Recovery

### 11.1 Database Backups
```bash
# Automated PostgreSQL backups
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
  namespace: content-pipeline
spec:
  schedule: "0 2 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: postgres-backup
            image: postgres:14
            command:
            - /bin/bash
            - -c
            - |
              pg_dump $DATABASE_URL | gzip > /backup/db-$(date +%Y%m%d).sql.gz
              aws s3 cp /backup/db-$(date +%Y%m%d).sql.gz s3://backups/postgres/
EOF
```

### 11.2 Disaster Recovery Plan
1. **Database Recovery**: Restore from S3 backups
2. **Media Recovery**: S3 cross-region replication
3. **Configuration Recovery**: GitOps with ArgoCD
4. **Service Recovery**: Multi-region failover

---

## 12. Performance Tuning

### 12.1 Horizontal Pod Autoscaling
```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
  namespace: content-pipeline
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 12.2 Redis Optimization
```yaml
# Redis configuration for high performance
apiVersion: v1
kind: ConfigMap
metadata:
  name: redis-config
  namespace: content-pipeline
data:
  redis.conf: |
    maxmemory 2gb
    maxmemory-policy allkeys-lru
    save ""
    appendonly no
```

---

## 13. Troubleshooting

### 13.1 Common Issues

#### Pod CrashLoopBackOff
```bash
# Check logs
kubectl logs -f pod-name -n content-pipeline --previous

# Describe pod
kubectl describe pod pod-name -n content-pipeline

# Check events
kubectl get events -n content-pipeline --sort-by='.lastTimestamp'
```

#### Database Connection Issues
```bash
# Test connection from pod
kubectl exec -it deployment/api -n content-pipeline -- psql $DATABASE_URL -c "SELECT 1"

# Check network policies
kubectl get networkpolicies -n content-pipeline
```

### 13.2 Debug Mode
```bash
# Enable debug logging
kubectl set env deployment/api LOG_LEVEL=DEBUG -n content-pipeline

# Port forward for local debugging
kubectl port-forward deployment/api 8000:8000 -n content-pipeline
```

---

## 14. Maintenance

### 14.1 Rolling Updates
```bash
# Update image
kubectl set image deployment/api api=pipeline/api:v1.1.0 -n content-pipeline

# Watch rollout
kubectl rollout status deployment/api -n content-pipeline

# Rollback if needed
kubectl rollout undo deployment/api -n content-pipeline
```

### 14.2 Scaling Operations
```bash
# Manual scaling
kubectl scale deployment/worker --replicas=10 -n content-pipeline

# Check resource usage
kubectl top nodes
kubectl top pods -n content-pipeline
```

---

## 15. Cost Optimization

### 15.1 Resource Recommendations
- Use spot instances for workers
- Enable cluster autoscaling
- Right-size pod resources
- Use S3 lifecycle policies

### 15.2 Cost Monitoring
```bash
# Install Kubecost
helm install kubecost kubecost/cost-analyzer \
  -n kubecost \
  --create-namespace

# Access dashboard
kubectl port-forward -n kubecost deployment/kubecost-cost-analyzer 9090:9090
```

---

## Support & Resources

- **Documentation**: https://docs.contentpipeline.ai
- **GitHub Issues**: https://github.com/your-org/ai-content-pipeline/issues
- **Slack Channel**: #content-pipeline-support
- **Email**: support@contentpipeline.ai