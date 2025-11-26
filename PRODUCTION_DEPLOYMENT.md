# Production Deployment Guide

## 🚀 Quick Start (5 Minutes)

```bash
# 1. Clone and navigate
git clone https://github.com/elliottsax/discovery.git
cd discovery

# 2. Copy environment template
cp .env.example .env

# 3. Edit .env with your values (REQUIRED)
nano .env  # Set DB_PASSWORD, SECRET_KEY, etc.

# 4. Deploy with Docker Compose
docker-compose -f docker-compose.production.yml up -d

# 5. Check status
docker-compose -f docker-compose.production.yml ps
```

## 📋 Prerequisites

- Docker 20.10+ and Docker Compose 2.0+
- 4GB RAM minimum (8GB recommended)
- 20GB disk space
- PostgreSQL client tools (optional, for manual DB access)

## 🔐 Security Checklist

Before deploying to production, ensure:

- [ ] Changed all default passwords in .env
- [ ] Generated SECRET_KEY: `openssl rand -hex 32`
- [ ] Generated JWT_SECRET_KEY: `openssl rand -hex 32`
- [ ] Set strong DB_PASSWORD
- [ ] Configured firewall rules
- [ ] Enabled HTTPS with valid SSL certificates
- [ ] Set SENTRY_DSN for error tracking
- [ ] Configured backup schedule

## 🛠️ Detailed Setup

### Step 1: Environment Configuration

```bash
# Required variables
export DB_PASSWORD="your_secure_password_here"
export SECRET_KEY=$(openssl rand -hex 32)
export JWT_SECRET_KEY=$(openssl rand -hex 32)

# Optional but recommended
export SENTRY_DSN="https://your-sentry-dsn"
export SMTP_PASSWORD="your_smtp_password"
```

### Step 2: Database Initialization

The PostgreSQL container will automatically initialize on first run. To manually init:

```bash
# Access database
docker-compose -f docker-compose.production.yml exec postgres psql -U quant_user -d quant_db

# Run migrations if needed
docker-compose -f docker-compose.production.yml exec app python manage.py migrate
```

### Step 3: SSL Certificates (for HTTPS)

```bash
# Using Let's Encrypt
sudo certbot certonly --standalone -d yourdomain.com

# Copy certificates
mkdir -p nginx/ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/
```

## 📊 Monitoring

Access monitoring dashboards:

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9091
- **MLFlow**: http://localhost:5000

## 🔄 Deployment Commands

```bash
# Start all services
docker-compose -f docker-compose.production.yml up -d

# Stop all services
docker-compose -f docker-compose.production.yml down

# View logs
docker-compose -f docker-compose.production.yml logs -f app

# Restart specific service
docker-compose -f docker-compose.production.yml restart app

# Scale workers
docker-compose -f docker-compose.production.yml up -d --scale celery_worker=4
```

## 🔧 Maintenance

### Backups

```bash
# Backup database
docker-compose -f docker-compose.production.yml exec postgres pg_dump -U quant_user quant_db > backup_$(date +%Y%m%d).sql

# Backup volumes
docker run --rm -v politician_trading_data:/data -v $(pwd):/backup alpine tar czf /backup/data_backup_$(date +%Y%m%d).tar.gz /data
```

### Updates

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml up -d
```

### Health Checks

```bash
# Check all services
docker-compose -f docker-compose.production.yml ps

# Check specific service health
docker inspect --format='{{.State.Health.Status}}' politician_trading_app

# View service logs
docker-compose -f docker-compose.production.yml logs --tail=100 app
```

## 🐛 Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose -f docker-compose.production.yml logs app

# Check environment variables
docker-compose -f docker-compose.production.yml config

# Rebuild from scratch
docker-compose -f docker-compose.production.yml down -v
docker-compose -f docker-compose.production.yml build --no-cache
docker-compose -f docker-compose.production.yml up -d
```

### Database Connection Issues

```bash
# Check database is running
docker-compose -f docker-compose.production.yml ps postgres

# Test connection
docker-compose -f docker-compose.production.yml exec app python -c "from sqlalchemy import create_engine; print('OK')"

# Check credentials
docker-compose -f docker-compose.production.yml exec postgres psql -U quant_user -d quant_db -c "SELECT 1"
```

### Performance Issues

```bash
# Check resource usage
docker stats

# Scale workers
docker-compose -f docker-compose.production.yml up -d --scale celery_worker=8

# Clear cache
docker-compose -f docker-compose.production.yml exec app rm -rf /app/cache/*
```

## 📈 Scaling

### Horizontal Scaling

```bash
# Add more workers
docker-compose -f docker-compose.production.yml up -d --scale celery_worker=10

# Add read replicas (edit docker-compose.yml first)
docker-compose -f docker-compose.production.yml up -d postgres_replica
```

### Vertical Scaling

Edit `docker-compose.production.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '4'      # Increase CPU
      memory: 8G     # Increase memory
```

## 🔒 Security Best Practices

1. **Never commit .env files**
2. **Rotate secrets regularly**
3. **Enable firewall**: Only expose necessary ports
4. **Use HTTPS**: Install SSL certificates
5. **Monitor logs**: Set up alerts for errors
6. **Keep updated**: Regular security patches
7. **Backup regularly**: Automated daily backups
8. **Restrict access**: Use strong passwords, 2FA

## 📞 Support

- Documentation: ./docs/
- Issues: https://github.com/elliottsax/discovery/issues
- Email: support@yourdomain.com

## 📄 License

See LICENSE file in repository root.
