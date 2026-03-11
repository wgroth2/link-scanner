# Deploying to Google Cloud VM (Ubuntu)

## 1. Create the VM on Google Cloud

- Go to **Compute Engine → VM Instances → Create Instance**
- Choose **Ubuntu 22.04 LTS**
- Machine type: **e2-small** is fine to start
- Under **Firewall**, check **Allow HTTP traffic** and **Allow HTTPS traffic**
- Create it, note the **External IP**

---

## 2. Point your domain to the VM

In your DNS provider (wherever `websitestringsearch.com` is registered), add an **A record** pointing `@` (and optionally `www`) to the VM's external IP. DNS propagation takes a few minutes to a few hours.

---

## 3. SSH into the VM and install dependencies

On a raw Ubuntu server (no desktop), install the following packages:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
    python3 \
    python-is-python3 \
    python3-pip \
    python3.12-venv \
    redis \
    nginx \
    certbot \
    python3-certbot-nginx \
    git \
    vim
```

---

## 4. Clone your repo and set up the virtualenv

```bash
git clone https://github.com/wgroth2/link-scanner.git
cd link-scanner
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

---

## 5. Create systemd services

You need three services: **Redis** (already installed as a service), **Celery**, and **Gunicorn**.

### `/etc/systemd/system/celery.service`

```ini
[Unit]
Description=Celery Worker
After=network.target redis.service

[Service]
User=www-data
WorkingDirectory=/home/YOUR_USER/link-scanner
ExecStart=/home/YOUR_USER/link-scanner/.venv/bin/celery -A tasks worker --loglevel=info --concurrency=2
Restart=always

[Install]
WantedBy=multi-user.target
```

### `/etc/systemd/system/gunicorn.service`

```ini
[Unit]
Description=Gunicorn for link-scanner
After=network.target

[Service]
User=www-data
WorkingDirectory=/home/YOUR_USER/link-scanner
ExecStart=/home/YOUR_USER/link-scanner/.venv/bin/gunicorn -w 2 -b 127.0.0.1:5001 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start all services:

```bash
sudo systemctl daemon-reload
sudo systemctl enable redis celery gunicorn
sudo systemctl start redis celery gunicorn
```

---

## 6. Configure Nginx as a reverse proxy

If your domain is not set up yet, you can use the VM's external IP address for `server_name` and test over HTTP. Skip Certbot until the domain is pointed at the IP and DNS has propagated.

Create `/etc/nginx/sites-available/link-scanner`:

```nginx
server {
    server_name websitestringsearch.com www.websitestringsearch.com;
    # If domain is not set up yet, use the external IP instead:
    # server_name 34.123.45.67;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable it:

```bash
# Activate the config by linking it into sites-enabled
sudo ln -s /etc/nginx/sites-available/link-scanner /etc/nginx/sites-enabled/

# Test the Nginx config for syntax errors before applying
sudo nginx -t

# Restart Nginx to apply the new config
sudo systemctl restart nginx
```

---

## 7. Add SSL with Let's Encrypt

```bash
sudo certbot --nginx -d websitestringsearch.com -d www.websitestringsearch.com
```

Certbot will automatically update your Nginx config for HTTPS and set up auto-renewal.

---

## 8. Verify everything is running

```bash
sudo systemctl status redis celery gunicorn nginx
```

Your site should then be live at `https://websitestringsearch.com`.

---

## Notes

- Replace `YOUR_USER` in the systemd service files with your actual Linux username on the VM.
- `gunicorn` is not in `requirements.txt` — install it separately with `pip install gunicorn`.
- Flower is not included in the production setup. It is a development/monitoring tool and should not be exposed publicly.
