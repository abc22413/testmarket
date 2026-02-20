# Deploying Market App to an AWS EC2 instance (Ubuntu)

This guide covers a minimal, secure deployment of the Market app on an EC2 Ubuntu instance using systemd + gunicorn and Nginx as a reverse proxy.

Prerequisites:
- EC2 instance (Ubuntu 20.04/22.04)
- Security group allowing SSH (22) and HTTP (80) / HTTPS (443) as needed
- Optionally: a managed Postgres (RDS) or local Postgres on the instance

Steps (concise commands):

1) Update and install packages

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3-venv python3-pip nginx git postgresql-client
```

2) Clone the repo and create a virtualenv

```bash
cd /home/ubuntu
git clone <your-repo-url> testmarket
cd testmarket
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

3) Configure environment variables

Copy the example file and edit values (SECRET_KEY, SQLALCHEMY_DATABASE_URI, ADMIN_PASSWORD, etc.)

```bash
cp .env.example .env
nano .env
```

For Postgres, set `SQLALCHEMY_DATABASE_URI` to:

`postgresql://<dbuser>:<dbpass>@<dbhost>:5432/<dbname>`

4) Create the database schema

Use Python to create tables (simple approach):

```bash
source venv/bin/activate
python -c "from app import db; db.create_all(); print('DB created')"
```

5) Install systemd service

Copy the template and update paths:

```bash
sudo cp deploy/market.service /etc/systemd/system/market.service
# Edit /etc/systemd/system/market.service: set User, WorkingDirectory and EnvironmentFile to your paths (e.g. /home/ubuntu/testmarket)
sudo systemctl daemon-reload
sudo systemctl enable --now market.service
sudo systemctl status market.service
```

6) Configure Nginx

```bash
sudo cp deploy/nginx_market /etc/nginx/sites-available/market
# Update static path inside file if needed
sudo ln -s /etc/nginx/sites-available/market /etc/nginx/sites-enabled/market
sudo nginx -t
sudo systemctl restart nginx
```

7) Firewall / AWS security group

- Ensure AWS Security Group allows inbound traffic on ports 80/443 (and 22 for SSH).
- If using `ufw` on the instance: `sudo ufw allow 'Nginx Full'` then `sudo ufw enable`.

8) Logs & troubleshooting

- Gunicorn logs via `journalctl -u market.service -f`
- Nginx logs: `/var/log/nginx/market.error.log` and `/var/log/nginx/market.access.log`

Notes & recommendations
- Use a secure `SECRET_KEY` and keep `.env` private.
- Prefer a managed Postgres (RDS) for production; update `SQLALCHEMY_DATABASE_URI` accordingly.
- Consider enabling TLS (Let's Encrypt) on Nginx for HTTPS.
- If you want to run behind a unix socket, update `deploy/market.service` and `deploy/nginx_market` accordingly.
