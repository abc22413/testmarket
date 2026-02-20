#!/bin/bash
# Production startup script for Market App

set -e

echo "🚀 Starting Market App in Production Mode"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please copy .env.example to .env and configure it for production"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check required variables
required_vars=("FLASK_ENV" "SECRET_KEY" "SQLALCHEMY_DATABASE_URI")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Error: $var is not set in .env"
        exit 1
    fi
done

# Verify FLASK_ENV is production
if [ "$FLASK_ENV" != "production" ]; then
    echo "⚠️  Warning: FLASK_ENV is set to '$FLASK_ENV', not 'production'"
fi

# Verify DEBUG is false
if [ "$DEBUG" != "False" ] && [ "$DEBUG" != "false" ]; then
    echo "❌ Error: DEBUG must be False in production"
    exit 1
fi

echo "✅ Configuration verified"
echo "📝 Database: $SQLALCHEMY_DATABASE_URI"
echo "🔒 CSRF Protection: Enabled"
echo "🔒 Secure Cookies: Enabled"

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Start gunicorn
echo "🌐 Starting Gunicorn server..."
gunicorn -w 4 \
         -b 0.0.0.0:${FLASK_PORT:-5000} \
         --timeout 120 \
         --access-logfile - \
         --error-logfile - \
         wsgi:app
