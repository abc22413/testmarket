# Market App - Production Ready

A prediction market application built with Flask using the LMSR (Logarithmic Market Scoring Rule) mechanism.

## 🚀 Quick Start

### Development
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
python app.py
```

### Production

**Linux/Mac:**
```bash
chmod +x start-production.sh
./start-production.sh
```

**Windows:**
```cmd
start-production.bat
```

**Docker:**
```bash
docker-compose up -d
```

## 📋 Configuration

1. Copy `.env.example` to `.env`
2. Set all required environment variables:
   ```
   FLASK_ENV=production
   SECRET_KEY=<strong-random-key>
   SQLALCHEMY_DATABASE_URI=<database-url>
   DEBUG=False
   ```

3. For PostgreSQL (recommended for production):
   ```
   SQLALCHEMY_DATABASE_URI=postgresql+psycopg2://user:password@host:5432/marketdb
   ```

## 🔒 Production Features

- ✅ **CSRF Protection** - Enabled with Flask-WTF
- ✅ **Secure Session Cookies** - HTTPOnly, Secure, SameSite flags
- ✅ **Form Validation** - All inputs validated
- ✅ **Environment Configuration** - All sensitive config via env vars
- ✅ **Debug Mode Disabled** - Production safe
- ✅ **Strong Secret Key** - Required in production
- ✅ **WSGI Ready** - Compatible with Gunicorn, uWSGI
- ✅ **Docker Ready** - Included Dockerfile and docker-compose

## 📚 Documentation

- [DEPLOYMENT.md](DEPLOYMENT.md) - Detailed deployment instructions
- [.env.example](.env.example) - Configuration template

## 🗄️ Database

### Development
Default SQLite database: `instance/market.db`

### Production
Supports:
- PostgreSQL (recommended)
- MySQL
- MariaDB
- Oracle
- MSSQL

## 🎯 Key Features

- User registration and authentication
- Market price discovery using LMSR
- Buy/sell prediction shares
- Admin market resolution
- User balance and holdings tracking
- Admin dashboard

## ⚙️ Environment Variables

| Variable | Default | Required | Notes |
|----------|---------|----------|-------|
| `FLASK_ENV` | production | ✓ | Set to 'production' or 'development' |
| `SECRET_KEY` | - | ✓ | Strong random key (min 32 chars) |
| `SQLALCHEMY_DATABASE_URI` | sqlite:///market.db | | Database connection URL |
| `DEBUG` | False | | Never True in production |
| `FLASK_HOST` | 127.0.0.1 | | Server host (0.0.0.0 for Docker) |
| `FLASK_PORT` | 5000 | | Server port |
| `ADMIN_USERNAME` | - | | Auto-create admin on startup |
| `ADMIN_PASSWORD` | - | | Admin user password |
| `LMSR_B` | 10.0 | | Market liquidity parameter |

## 🔧 Deployment Options

1. **Gunicorn** (recommended)
2. **Docker Compose**
3. **Systemd Service** (Linux)
4. **Cloud Platforms** (Heroku, Railway, AWS, etc.)

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

## 🛡️ Security Checklist

Before going live:
- [ ] Set strong `SECRET_KEY`
- [ ] Set `FLASK_ENV=production`
- [ ] Set `DEBUG=False`
- [ ] Configure database with strong credentials
- [ ] Use HTTPS/SSL (via reverse proxy like Nginx)
- [ ] Set up monitoring and logging
- [ ] Configure automated backups
- [ ] Test admin panel access

## 📊 Performance

Gunicorn configuration:
- Workers: 4 (adjust based on CPU cores: `2 + (2 × cores)`)
- Timeout: 120 seconds
- Bind: 0.0.0.0:5000

For production, use Nginx as reverse proxy for:
- Static file serving
- SSL/TLS termination
- Load balancing

## 📝 License

[Your License Here]

## 🤝 Support

See DEPLOYMENT.md for troubleshooting.
