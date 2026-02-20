# Production Deployment Guide

## Pre-Deployment Checklist

### 1. Environment Setup
- [ ] Create `.env` file based on `.env.example`
- [ ] Set a strong `SECRET_KEY` (use: `python -c "import secrets; print(secrets.token_hex(32))"`)
- [ ] Set `FLASK_ENV=production`
- [ ] Set `DEBUG=False`
- [ ] For PostgreSQL in production: Update `SQLALCHEMY_DATABASE_URI`

### 2. Database
- [ ] For production use PostgreSQL instead of SQLite
- [ ] Example PostgreSQL URI: `postgresql+psycopg2://user:password@host:5432/market_db`
- [ ] Run migrations if applicable

### 3. Dependencies
```bash
pip install -r requirements.txt
```

### 4. Required Environment Variables
```
FLASK_ENV=production
SECRET_KEY=<your-secure-secret-key>
SQLALCHEMY_DATABASE_URI=<database-url>
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
DEBUG=False
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<secure-password>
```

## Deployment Options

### Option 1: Gunicorn (Recommended)
```bash
# Single worker (development-like)
gunicorn -w 1 -b 0.0.0.0:5000 wsgi:app

# Production (4 workers, typically 2-4x CPU cores)
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 wsgi:app

# With auto-restart on code changes
gunicorn -w 4 -b 0.0.0.0:5000 --reload wsgi:app
```

### Option 2: Docker Deployment
Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "wsgi:app"]
```

Build and run:
```bash
docker build -t market-app .
docker run -p 5000:5000 --env-file .env market-app
```

### Option 3: Systemd Service (Linux)
Create `/etc/systemd/system/market-app.service`:
```ini
[Unit]
Description=Market App
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/opt/market-app
ExecStart=/opt/market-app/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 wsgi:app
EnvironmentFile=/opt/market-app/.env
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable market-app
sudo systemctl start market-app
```

## Reverse Proxy Setup (Nginx)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## SSL/TLS (Let's Encrypt with Certbot)
```bash
sudo certbot --nginx -d your-domain.com
```

## Security Checklist
- [x] Debug mode disabled
- [x] CSRF protection enabled
- [x] Form validation enabled
- [x] Secure session cookies configured
- [x] SECRET_KEY is strong and unique
- [ ] SSL/TLS certificate installed
- [ ] Database credentials secured
- [ ] Regular backups configured
- [ ] Monitoring and logging set up

## Health Check Endpoint
Test the application:
```bash
curl http://localhost:5000/
```

## Troubleshooting

### Application not starting
- Check `.env` file exists and is correct
- Verify `SECRET_KEY` is set
- Check database connectivity
- Review logs: `gunicorn` outputs to stdout/stderr

### Database errors
- Verify `SQLALCHEMY_DATABASE_URI` is correct
- Ensure database user has proper permissions
- Check database server is running

### Port already in use
```bash
lsof -i :5000  # Linux/Mac
netstat -ano | findstr :5000  # Windows
```

## Performance Tuning
- Adjust gunicorn worker count: `workers = 2 + (2 × CPU_cores)`
- Enable reverse proxy caching for static files
- Use PostgreSQL for better concurrency
- Consider adding Redis for session storage
