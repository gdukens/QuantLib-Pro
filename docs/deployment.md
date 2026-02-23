# QuantLib Pro Deployment Guide

Complete guide for deploying QuantLib Pro in various environments.

## Table of Contents

1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Cloud Deployment](#cloud-deployment)
4. [Production Best Practices](#production-best-practices)
5. [Monitoring & Maintenance](#monitoring--maintenance)

---

## Local Development

### Prerequisites

- Python 3.8+
- pip or conda
- Git
- 8GB+ RAM recommended

### Setup

**1. Clone Repository**

```bash
git clone https://github.com/gdukens/quant-simulator.git
cd quant-simulator
```

**2. Create Virtual Environment**

```bash
# Using venv
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate
```

**3. Install Dependencies**

```bash
pip install -r requirements.txt
```

**4. Run Application**

```bash
streamlit run Home.py
```

The application will start at `http://localhost:8501`

### Configuration

**Environment Variables** (`.env`):

```bash
# Data Provider API Keys
ALPHA_VANTAGE_API_KEY=your_key_here
IEX_API_KEY=your_key_here
POLYGON_API_KEY=your_key_here

# Application Settings
CACHE_DIR=./data/cache
LOG_LEVEL=INFO
ENABLE_PROFILING=true

# Risk Settings
DEFAULT_CONFIDENCE_LEVEL=0.95
DEFAULT_PORTFOLIO_VALUE=1000000

# Performance
MAX_WORKERS=4
CACHE_EXPIRY_HOURS=24
```

### Development Tools

**Linting:**

```bash
pip install flake8 black
flake8 quantlib_pro/
black quantlib_pro/
```

**Type Checking:**

```bash
pip install mypy
mypy quantlib_pro/
```

**Testing:**

```bash
pip install pytest pytest-cov
pytest tests/ -v --cov=quantlib_pro
```

---

## Docker Deployment

### Dockerfile

Create `Dockerfile`:

```dockerfile
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run application
CMD ["streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  quantlib:
    build: .
    ports:
      - "8501:8501"
    environment:
      - ALPHA_VANTAGE_API_KEY=${ALPHA_VANTAGE_API_KEY}
      - CACHE_DIR=/app/data/cache
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    networks:
      - quantlib-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - quantlib-network
    restart: unless-stopped

networks:
  quantlib-network:
    driver: bridge

volumes:
  redis-data:
```

### Build and Run

```bash
# Build image
docker build -t quantlib-pro:latest .

# Run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f quantlib

# Stop
docker-compose down
```

### Environment Configuration

Create `.env` file:

```bash
ALPHA_VANTAGE_API_KEY=your_key_here
REDIS_HOST=redis
REDIS_PORT=6379
```

---

## Cloud Deployment

### AWS Deployment

#### Option 1: EC2 Instance

**1. Launch EC2 Instance**

```bash
# Using AWS CLI
aws ec2 run-instances \
    --image-id ami-0c55b159cbfafe1f0 \
    --instance-type t3.medium \
    --key-name your-key-pair \
    --security-groups quantlib-sg \
    --user-data file://user-data.sh
```

**user-data.sh:**

```bash
#!/bin/bash
# Update system
yum update -y

# Install Docker
yum install -y docker
service docker start
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Clone repository
git clone https://github.com/gdukens/quant-simulator.git /home/ec2-user/quantlib

# Start application
cd /home/ec2-user/quantlib
docker-compose up -d
```

**2. Configure Security Group**

```bash
# Allow HTTP/HTTPS and Streamlit
aws ec2 authorize-security-group-ingress \
    --group-name quantlib-sg \
    --protocol tcp --port 8501 --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
    --group-name quantlib-sg \
    --protocol tcp --port 22 --cidr your-ip/32
```

#### Option 2: ECS (Elastic Container Service)

**task-definition.json:**

```json
{
  "family": "quantlib-pro",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "quantlib",
      "image": "your-ecr-repo/quantlib-pro:latest",
      "portMappings": [
        {
          "containerPort": 8501,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "CACHE_DIR",
          "value": "/app/data/cache"
        }
      ],
      "secrets": [
        {
          "name": "ALPHA_VANTAGE_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:name"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/quantlib-pro",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

**Deploy:**

```bash
# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create service
aws ecs create-service \
    --cluster quantlib-cluster \
    --service-name quantlib-service \
    --task-definition quantlib-pro \
    --desired-count 2 \
    --launch-type FARGATE \
    --load-balancers targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=quantlib,containerPort=8501
```

### Google Cloud Platform

#### Cloud Run Deployment

**1. Build and Push Image**

```bash
# Build for Cloud Run
gcloud builds submit --tag gcr.io/your-project-id/quantlib-pro

# Or using Docker
docker build -t gcr.io/your-project-id/quantlib-pro .
docker push gcr.io/your-project-id/quantlib-pro
```

**2. Deploy to Cloud Run**

```bash
gcloud run deploy quantlib-pro \
    --image gcr.io/your-project-id/quantlib-pro \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --port 8501 \
    --set-env-vars "CACHE_DIR=/tmp/cache,LOG_LEVEL=INFO" \
    --set-secrets "ALPHA_VANTAGE_API_KEY=alpha-vantage-key:latest"
```

**3. Configure Cloud SQL (Optional)**

```bash
gcloud run services update quantlib-pro \
    --add-cloudsql-instances your-project:region:instance-name \
    --set-env-vars "DB_HOST=/cloudsql/your-project:region:instance-name"
```

### Azure Deployment

#### Azure App Service

**1. Create App Service**

```bash
# Create resource group
az group create --name quantlib-rg --location eastus

# Create App Service plan
az appservice plan create \
    --name quantlib-plan \
    --resource-group quantlib-rg \
    --is-linux \
    --sku B2

# Create Web App
az webapp create \
    --resource-group quantlib-rg \
    --plan quantlib-plan \
    --name quantlib-pro \
    --deployment-container-image-name your-registry.azurecr.io/quantlib-pro:latest
```

**2. Configure Settings**

```bash
# Set port
az webapp config appsettings set \
    --resource-group quantlib-rg \
    --name quantlib-pro \
    --settings WEBSITES_PORT=8501

# Set environment variables
az webapp config appsettings set \
    --resource-group quantlib-rg \
    --name quantlib-pro \
    --settings CACHE_DIR=/home/data/cache LOG_LEVEL=INFO
```

### Heroku Deployment

**1. Create Heroku App**

```bash
heroku login
heroku create quantlib-pro
```

**2. Add Buildpack**

```bash
heroku buildpacks:set heroku/python
```

**3. Create Procfile**

```
web: streamlit run Home.py --server.port=$PORT --server.address=0.0.0.0
```

**4. Deploy**

```bash
git push heroku main
```

**5. Scale**

```bash
heroku ps:scale web=2
```

---

## Production Best Practices

### 1. Security

**API Key Management:**

```python
import os
from dotenv import load_dotenv

# Never commit .env file
load_dotenv()

# Use environment variables
API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
if not API_KEY:
    raise ValueError("API_KEY not set")
```

**HTTPS Only:**

```python
# In Streamlit config.toml
[server]
enableCORS = false
enableXsrfProtection = true
```

**Input Validation:**

```python
def validate_ticker(ticker: str) -> bool:
    """Prevent injection attacks."""
    import re
    return bool(re.match(r'^[A-Z]{1,5}$', ticker))
```

### 2. Performance

**Caching:**

```python
import streamlit as st

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_data(tickers):
    return provider.get_historical_data(tickers)
```

**Connection Pooling:**

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    'postgresql://user:pass@host/db',
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20
)
```

**Load Balancing:**

```nginx
upstream quantlib {
    server quantlib1:8501;
    server quantlib2:8501;
    server quantlib3:8501;
}

server {
    listen 80;
    server_name quantlib.example.com;
    
    location / {
        proxy_pass http://quantlib;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. Reliability

**Health Checks:**

```python
# health_check.py
import requests

def check_health():
    try:
        response = requests.get('http://localhost:8501/_stcore/health')
        return response.status_code == 200
    except:
        return False

if __name__ == '__main__':
    exit(0 if check_health() else 1)
```

**Auto-Restart:**

```bash
# systemd service file
[Unit]
Description=QuantLib Pro
After=network.target

[Service]
Type=simple
User=quantlib
WorkingDirectory=/opt/quantlib
ExecStart=/opt/quantlib/venv/bin/streamlit run Home.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Database Backups:**

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump quantlib_db > /backups/quantlib_$DATE.sql
# Retain last 7 days
find /backups -name "quantlib_*.sql" -mtime +7 -delete
```

### 4. Logging

**Structured Logging:**

```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
        })

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
```

**Log Rotation:**

```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'quantlib.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
```

---

## Monitoring & Maintenance

### Application Monitoring

**Prometheus Metrics:**

```python
from prometheus_client import Counter, Histogram, start_http_server

request_count = Counter('quantlib_requests_total', 'Total requests')
request_duration = Histogram('quantlib_request_duration_seconds', 'Request duration')

@request_duration.time()
def handle_request():
    request_count.inc()
    # Process request
```

**Grafana Dashboard:**

```json
{
  "dashboard": {
    "title": "QuantLib Pro Metrics",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(quantlib_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Response Time (P95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, quantlib_request_duration_seconds_bucket)"
          }
        ]
      }
    ]
  }
}
```

### Database Maintenance

**PostgreSQL Vacuum:**

```bash
# Cron job (daily at 2 AM)
0 2 * * * /usr/bin/vacuumdb -U postgres quantlib_db
```

**Index Optimization:**

```sql
-- Monitor index usage
SELECT 
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;

-- Rebuild indexes
REINDEX TABLE portfolio_data;
```

### Dependency Updates

```bash
# Check for outdated packages
pip list --outdated

# Update dependencies
pip install -U -r requirements.txt

# Run tests
pytest tests/

# Update requirements.txt
pip freeze > requirements.txt
```

### Performance Tuning

**Application Profiling:**

```bash
# Profile with cProfile
python -m cProfile -o profile.stats run_optimization.py

# Analyze with snakeviz
pip install snakeviz
snakeviz profile.stats
```

**Database Query Optimization:**

```sql
-- Explain query plan
EXPLAIN ANALYZE
SELECT * FROM portfolio_data WHERE ticker = 'AAPL';

-- Add index if needed
CREATE INDEX idx_portfolio_ticker ON portfolio_data(ticker);
```

---

## Troubleshooting

### Common Issues

**Issue: Out of Memory**

```bash
# Increase container memory
docker run -m 4g quantlib-pro

# Or in docker-compose.yml
services:
  quantlib:
    mem_limit: 4g
```

**Issue: Slow Performance**

```python
# Enable profiling
from quantlib_pro.observability import profile

@profile
def slow_function():
    # Identify bottlenecks
    pass
```

**Issue: Data Provider Timeouts**

```python
# Increase timeout
import requests

session = requests.Session()
session.timeout = 30  # 30 seconds
```

### Debugging

**Enable Debug Mode:**

```bash
# .streamlit/config.toml
[server]
runOnSave = true
fileWatcherType = "auto"

[logger]
level = "debug"
```

**Check Logs:**

```bash
# Docker logs
docker logs -f quantlib-container

# Application logs
tail -f logs/quantlib.log
```

---

## Rollback Procedures

**Docker Rollback:**

```bash
# Tag previous version
docker tag quantlib-pro:latest quantlib-pro:v1.0.0

# Rollback
docker-compose down
docker-compose up -d quantlib-pro:v1.0.0
```

**Database Rollback:**

```bash
# Restore from backup
pg_restore -d quantlib_db /backups/quantlib_20240223_120000.sql
```

---

## See Also

- [Architecture Documentation](architecture.md)
- [User Guide](guides/user_guide.md)
- [API Reference](api/README.md)
- [Contributing Guidelines](../CONTRIBUTING.md)
