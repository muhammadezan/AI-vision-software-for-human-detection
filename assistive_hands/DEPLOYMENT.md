# AssistiveHands - Deployment & Production Guide

## 🚀 Deployment Options

### Option 1: Local Development (Recommended for Testing)

```bash
python app.py
```

Access: `http://127.0.0.1:5000`

**Pros:**
- Simplest setup
- Full local control
- No network latency

**Cons:**
- Local access only
- Not suitable for production

---

## Option 2: Local Network Deployment

Allow access from other devices on your network.

### Setup

Edit `app.py`:

```python
if __name__ == '__main__':
    app.run(
        host='0.0.0.0',           # Listen on all interfaces
        port=5000,
        debug=False,               # Disable debug mode
        threaded=True
    )
```

### Access

From any device on the network:
```
http://<your-computer-ip>:5000
```

Find your IP:
- **Windows**: `ipconfig` → IPv4 Address
- **macOS/Linux**: `ifconfig` → inet address

### Network Security

⚠️ **Important**: Local network deployment exposes your application.

Add basic authentication:

```python
from flask_httpauth import HTTPBasicAuth

auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    users = {"admin": "your-secure-password"}
    return users.get(username) == password

@app.route('/')
@auth.login_required
def index():
    return render_template('dashboard.html')
```

---

## Option 3: Docker Deployment

### Create Dockerfile

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

CMD ["python", "app.py"]
```

### Create docker-compose.yml

```yaml
version: '3.8'

services:
  assistive-hands:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - FLASK_ENV=production
      - CAMERA_DEVICE_INDEX=0
```

### Deploy with Docker

```bash
# Build image
docker build -t assistive-hands .

# Run container
docker run -p 5000:5000 --device /dev/video0 assistive-hands

# Or use docker-compose
docker-compose up
```

---

## Option 4: Cloud Deployment

### Heroku Deployment

1. **Create Procfile:**
```
web: gunicorn app:app
```

2. **Create requirements.txt** (already done)

3. **Deploy:**
```bash
heroku login
heroku create your-app-name
git push heroku main
```

⚠️ **Note**: Heroku doesn't have webcam access. Use for backend testing only.

### AWS Deployment

1. **EC2 Instance Setup:**
```bash
sudo apt update
sudo apt install python3-pip python3-venv
git clone <your-repo>
cd assistive_hands
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **Run with Gunicorn:**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

3. **Security Group Settings:**
- Port 5000: Inbound traffic
- HTTPS (443): Recommended

### Azure Deployment

1. **Create App Service:**
```bash
az webapp create --resource-group myGroup --plan myPlan --name assistive-hands
```

2. **Deploy code:**
```bash
az webapp up --name assistive-hands --runtime python:3.11
```

---

## Production Configuration

### Environment Variables

Create `.env` file:

```env
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-very-secret-key-change-this
CAMERA_DEVICE_INDEX=0
LOG_LEVEL=WARNING
```

Load in `app.py`:

```python
from dotenv import load_dotenv
load_dotenv()

app.config['DEBUG'] = os.getenv('FLASK_DEBUG', False)
SECRET_KEY = os.getenv('SECRET_KEY', 'change-this-in-production')
```

### Performance Optimization

#### 1. Reduce Camera Resolution

```python
# config/settings.py
CAMERA_RESOLUTION = (960, 540)  # From 1280x720
CAMERA_FPS = 25                  # From 30
```

#### 2. Enable Caching

```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@app.route('/api/status')
@cache.cached(timeout=1)
def get_status():
    # ...
```

#### 3. Use Production WSGI Server

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 app:app
```

#### 4. Enable Compression

```python
from flask_compress import Compress

Compress(app)
```

### Database Setup (Optional)

For user profiles and calibration data:

```python
from flask_sqlalchemy import SQLAlchemy

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///assistive_hands.db'
db = SQLAlchemy(app)

class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    calibration_data = db.Column(db.LargeBinary)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

---

## Security Hardening

### 1. HTTPS/SSL

```bash
# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

# Run with SSL
gunicorn --certfile=cert.pem --keyfile=key.pem --bind 0.0.0.0:5000 app:app
```

### 2. Rate Limiting

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(app, key_func=get_remote_address)

@app.route('/api/gaze/current')
@limiter.limit("60 per minute")
def get_gaze():
    # ...
```

### 3. Input Validation

```python
from marshmallow import Schema, fields, ValidationError

class SettingsSchema(Schema):
    dwell_time = fields.Float(validate=lambda x: 0.3 <= x <= 3.0)
    brightness = fields.Integer(validate=lambda x: -100 <= x <= 100)
```

### 4. CORS Configuration

```python
from flask_cors import CORS

# Allow specific origins only
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://yourdomain.com"],
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type"]
    }
})
```

---

## Monitoring & Logging

### Logging to File

```python
import logging
from logging.handlers import RotatingFileHandler

if not os.path.exists('logs'):
    os.mkdir('logs')

file_handler = RotatingFileHandler('logs/assistive_hands.log',
                                   maxBytes=10240000,
                                   backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
app.logger.addHandler(file_handler)
```

### Monitoring with Datadog

```python
from datadog import statsd

@app.route('/api/gaze/current')
def get_gaze():
    statsd.increment('gaze.requests')
    # ...
```

### Application Monitoring

Use APM (Application Performance Monitoring):
- **New Relic**: `pip install newrelic`
- **Sentry**: `pip install sentry-sdk`

Sentry example:
```python
import sentry_sdk

sentry_sdk.init(
    "your-sentry-dsn",
    traces_sample_rate=1.0
)
```

---

## Backup & Recovery

### Backup Strategy

```bash
# Backup user data and calibration
tar -czf backup-$(date +%Y%m%d).tar.gz data/ logs/

# Upload to cloud storage
aws s3 cp backup-$(date +%Y%m%d).tar.gz s3://my-backups/
```

### Automated Backups

Add cron job (Linux):

```bash
0 2 * * * /home/user/assistive_hands/backup.sh
```

---

## Troubleshooting Deployment

### Camera Not Available in Docker

```dockerfile
# Build with device mapping
docker run --device /dev/video0 assistive-hands
```

### Port Already in Use

```bash
# Change port in production
gunicorn -b 0.0.0.0:8000 app:app
```

### High Memory Usage

```python
# Reduce camera resolution
CAMERA_RESOLUTION = (640, 480)

# Reduce buffer size
FRAME_BUFFER_SIZE = 15
```

### Slow Performance Over Network

```python
# Lower FPS
CAMERA_FPS = 15

# Reduce JPEG quality
cv2.IMWRITE_JPEG_QUALITY = 50
```

---

## Performance Metrics

### Expected Performance

| Metric | Local | Network |
|--------|-------|---------|
| Latency | 33-50ms | 50-200ms |
| CPU Usage | 20-40% | 25-45% |
| Memory | 200-400MB | 250-450MB |
| Bandwidth | Local | ~2-5 Mbps |

### Optimization Checklist

- [ ] Reduce camera resolution
- [ ] Lower FPS (20-25)
- [ ] Disable performance monitoring
- [ ] Enable gzip compression
- [ ] Use production WSGI server
- [ ] Enable caching where appropriate
- [ ] Monitor system resources
- [ ] Regular log rotation
- [ ] Database indexing

---

## Maintenance

### Regular Updates

```bash
# Check for dependency updates
pip list --outdated

# Update carefully
pip install --upgrade flask==3.1.0
```

### Database Maintenance

```python
# Clean old logs
import os
from datetime import datetime, timedelta

def cleanup_old_logs(days=30):
    log_dir = 'logs/'
    cutoff_time = datetime.now() - timedelta(days=days)
    for filename in os.listdir(log_dir):
        filepath = os.path.join(log_dir, filename)
        if os.path.getmtime(filepath) < cutoff_time.timestamp():
            os.remove(filepath)
```

---

## Rollback Procedure

```bash
# Tag releases
git tag -a v1.0 -m "Production release v1.0"

# Rollback if needed
git checkout v1.0
python app.py
```

---

## Support for Production

- Monitor application logs continuously
- Set up alerts for errors
- Regular security updates
- Test backup restoration
- Document deployment process
- Keep deployment scripts version controlled

---

## Next Steps

1. **Test locally** with `python app.py`
2. **Choose deployment option** (local, network, Docker, cloud)
3. **Configure for production** (environment variables, security)
4. **Set up monitoring** (logging, APM)
5. **Plan backup strategy** (automated backups, recovery)

For additional help, see [README.md](README.md) and [INSTALLATION.md](INSTALLATION.md).
