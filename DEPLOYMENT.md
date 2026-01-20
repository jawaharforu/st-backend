# Ubuntu Server Deployment Guide

Deploy the Smart Incubator Backend on Ubuntu using Docker for all services (including PostgreSQL).

## Prerequisites

- Ubuntu 20.04+ server
- Root or sudo access
- Domain name (optional, for SSL)

---

## Step 1: Install Docker

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install -y docker-compose-plugin

# Log out and back in, then verify
docker --version
docker compose version
```

---

## Step 2: Install Other Dependencies

```bash
sudo apt install -y git nginx python3.11 python3.11-venv
```

---

## Step 3: Upload Application Code

```bash
# Create application directory
sudo mkdir -p /opt/st-backend
sudo chown $USER:$USER /opt/st-backend

# Upload via SCP or clone from Git
# scp -r ./st-backend/* user@server:/opt/st-backend/
# git clone https://your-repo.git /opt/st-backend

cd /opt/st-backend
```

---

## Step 4: Configure Environment

```bash
# Copy and edit environment file
cp .env.example .env
nano .env
```

**Update these values in `.env`:**
```bash
POSTGRES_PASSWORD=your_secure_db_password
DATABASE_URL=postgresql+asyncpg://postgres:your_secure_db_password@db:5432/incubator_db
MINIO_SECRET_KEY=your_secure_minio_password
SECRET_KEY=$(openssl rand -hex 32)  # Generate and paste this
BACKEND_CORS_ORIGINS=["https://your-domain.com"]
```

---

## Step 5: Start All Docker Services

```bash
cd /opt/st-backend
docker compose -f docker-compose.prod.yml up -d

# Verify all containers are running
docker ps
```

---

## Step 6: Setup Python & Run Migrations

```bash
cd /opt/st-backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt gunicorn

# Wait for database to be ready, then run migrations
sleep 10
alembic upgrade head
```

---

## Step 7: Create MinIO Bucket

```bash
# Install MinIO client
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc && sudo mv mc /usr/local/bin/

# Configure and create bucket
mc alias set local http://localhost:9000 minioadmin your_secure_minio_password
mc mb local/firmware
mc anonymous set download local/firmware
```

---

## Step 8: Create Systemd Service

```bash
sudo tee /etc/systemd/system/st-backend.service << 'EOF'
[Unit]
Description=Smart Incubator Backend
After=network.target docker.service
Requires=docker.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/st-backend
Environment="PATH=/opt/st-backend/venv/bin"
EnvironmentFile=/opt/st-backend/.env
ExecStart=/opt/st-backend/venv/bin/gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --access-logfile /var/log/st-backend/access.log \
    --error-logfile /var/log/st-backend/error.log
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Setup
sudo mkdir -p /var/log/st-backend
sudo chown -R www-data:www-data /opt/st-backend /var/log/st-backend
sudo systemctl daemon-reload
sudo systemctl enable st-backend
sudo systemctl start st-backend
```

---

## Step 9: Configure Nginx

```bash
sudo tee /etc/nginx/sites-available/st-backend << 'EOF'
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/st-backend /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

---

## Step 10: Setup SSL (Optional)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## Step 11: Configure Firewall

```bash
sudo apt install -y ufw
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw allow 1883/tcp  # MQTT for IoT devices
sudo ufw enable
```

---

## Quick Commands

```bash
# Service management
sudo systemctl restart st-backend
sudo journalctl -u st-backend -f

# Docker services
docker compose -f docker-compose.prod.yml logs -f
docker compose -f docker-compose.prod.yml restart

# Database backup
docker exec st-backend-db-1 pg_dump -U postgres incubator_db > backup.sql
```

---

## Architecture

```
Internet → Nginx (:80/:443) → FastAPI (:8000)
                                   ↓
              ┌────────────────────┼────────────────────┐
              ↓                    ↓                    ↓
         PostgreSQL            Redis               EMQX MQTT
          (:5432)             (:6379)               (:1883)
                                                       ↓
                                                  IoT Devices
```
