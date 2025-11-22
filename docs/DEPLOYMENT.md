# Deployment Guide

## Overview

This guide covers deploying the Nanonets VL OCR API to production environments.

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- NVIDIA GPU with CUDA 11.8+ (for GPU inference)
- 16GB+ RAM
- 50GB+ disk space

## Local Development

### Quick Start

```bash
# Clone repository
git clone https://github.com/your-org/nanonets-ocr.git
cd nanonets-ocr

# Start services
docker-compose up -d

# Check health
curl http://localhost:8000/api/v1/health
```

### Environment Variables

Create `.env` file:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_PREFIX=/api/v1
DEBUG=false

# Model Configuration
MODEL_NAME=nanonets-ocr-vl
MODEL_DEVICE=cuda
MODEL_QUANTIZATION=int8

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/nanonets

# Redis Cache
REDIS_URL=redis://localhost:6379/0

# Storage
STORAGE_TYPE=s3
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
S3_BUCKET=nanonets-ocr

# Security
JWT_SECRET_KEY=your-secret-key
API_KEY_SALT=your-salt
```

## Docker Deployment

### Build Image

```bash
docker build -t nanonets-ocr:latest .
```

### Run Container

```bash
# CPU mode
docker run -d \
  --name nanonets-ocr \
  -p 8000:8000 \
  -v ./data:/app/data \
  --env-file .env \
  nanonets-ocr:latest

# GPU mode
docker run -d \
  --name nanonets-ocr \
  --gpus all \
  -p 8000:8000 \
  -v ./data:/app/data \
  --env-file .env \
  nanonets-ocr:latest
```

### Docker Compose

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/nanonets
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=nanonets
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

## Kubernetes Deployment

### Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nanonets-ocr
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nanonets-ocr
  template:
    metadata:
      labels:
        app: nanonets-ocr
    spec:
      containers:
        - name: api
          image: nanonets-ocr:latest
          ports:
            - containerPort: 8000
          resources:
            requests:
              memory: "8Gi"
              cpu: "2"
              nvidia.com/gpu: 1
            limits:
              memory: "16Gi"
              cpu: "4"
              nvidia.com/gpu: 1
          livenessProbe:
            httpGet:
              path: /api/v1/live
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /api/v1/ready
              port: 8000
            initialDelaySeconds: 60
            periodSeconds: 5
          envFrom:
            - secretRef:
                name: nanonets-secrets
            - configMapRef:
                name: nanonets-config
```

### Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: nanonets-ocr
spec:
  selector:
    app: nanonets-ocr
  ports:
    - port: 80
      targetPort: 8000
  type: LoadBalancer
```

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: nanonets-ocr
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: nanonets-ocr
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

## Cloud Deployments

### AWS ECS

1. Push image to ECR
2. Create ECS cluster with GPU instances
3. Create task definition with GPU requirements
4. Deploy service with ALB

### Google Cloud Run

```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT/nanonets-ocr

# Deploy
gcloud run deploy nanonets-ocr \
  --image gcr.io/PROJECT/nanonets-ocr \
  --platform managed \
  --memory 8Gi \
  --cpu 4 \
  --gpu 1
```

### Azure Container Instances

```bash
az container create \
  --resource-group myResourceGroup \
  --name nanonets-ocr \
  --image nanonets-ocr:latest \
  --cpu 4 \
  --memory 16 \
  --gpu-count 1 \
  --gpu-sku K80 \
  --ports 8000
```

## Monitoring

### Prometheus Metrics

The API exposes metrics at `/api/v1/metrics`:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'nanonets-ocr'
    static_configs:
      - targets: ['nanonets-ocr:8000']
    metrics_path: /api/v1/metrics
```

### Grafana Dashboard

Import dashboard from `monitoring/grafana-dashboard.json`

### Health Checks

- **Liveness**: `GET /api/v1/live`
- **Readiness**: `GET /api/v1/ready`
- **Health**: `GET /api/v1/health`

## Performance Tuning

### Model Optimization

```env
# Use INT8 quantization for faster inference
MODEL_QUANTIZATION=int8

# Batch processing
MAX_BATCH_SIZE=16

# Worker threads
WORKERS=4
```

### Caching

```env
# Enable Redis caching
CACHE_ENABLED=true
CACHE_TTL=3600
```

### Connection Pooling

```env
# Database pool
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
```

## Security

### TLS/SSL

```bash
# Generate certificates
openssl req -x509 -nodes -days 365 \
  -newkey rsa:2048 \
  -keyout server.key \
  -out server.crt
```

### API Authentication

- API Keys for service-to-service
- JWT tokens for user authentication
- Rate limiting per client

### Network Security

- Use VPC/private networks
- Configure security groups
- Enable WAF for public endpoints

## Troubleshooting

### Common Issues

1. **GPU not detected**
   ```bash
   nvidia-smi  # Check GPU availability
   docker run --gpus all nvidia/cuda:11.8-base nvidia-smi
   ```

2. **Out of memory**
   - Reduce batch size
   - Enable quantization
   - Use streaming for large files

3. **Slow inference**
   - Check GPU utilization
   - Enable caching
   - Use async processing

### Logs

```bash
# Docker logs
docker logs nanonets-ocr -f

# Kubernetes logs
kubectl logs -f deployment/nanonets-ocr
```

## Backup & Recovery

### Database Backup

```bash
pg_dump -h localhost -U postgres nanonets > backup.sql
```

### Restore

```bash
psql -h localhost -U postgres nanonets < backup.sql
```
