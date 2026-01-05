# 🚀 Complete Deployment Guide - IBC Play

This guide walks you through deploying your IBC Play platform to production.

## 📋 Pre-Deployment Checklist

- [ ] All code tested locally
- [ ] Database schema verified
- [ ] Environment variables configured
- [ ] Secret keys generated
- [ ] API endpoints tested
- [ ] Frontend updated with production API URL
- [ ] `.env` file not committed to repository
- [ ] `.gitignore` properly configured

## 🌐 Deployment Options

### Option 1: Render.com (Recommended for Beginners)

#### Step 1: Prepare Repository

1. **Push code to GitHub**
```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

2. **Verify files**
Ensure these files are in your repository:
- `main.py`
- `db_init.py`
- `requirements.txt`
- `render.yaml`
- `.gitignore`

#### Step 2: Create Render Account

1. Go to https://render.com
2. Sign up with GitHub
3. Authorize Render to access your repositories

#### Step 3: Deploy with Blueprint

1. Click "New +" → "Blueprint"
2. Select your `ibc-play` repository
3. Render automatically detects `render.yaml`
4. Click "Apply"

#### Step 4: Configure Environment Variables

Render will prompt you to set:

```
SECRET_KEY=<generate-secure-key>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
COINGECKO_API_URL=https://api.coingecko.com/api/v3
ENVIRONMENT=production
```

**Generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### Step 5: Monitor Deployment

1. Watch build logs in Render dashboard
2. Wait for "Live" status (usually 3-5 minutes)
3. Note your service URL: `https://ibc-play-XXXX.onrender.com`

#### Step 6: Update Frontend

Update the frontend `API_BASE` constant:
```javascript
const API_BASE = 'https://ibc-play-XXXX.onrender.com';
```

#### Step 7: Test Production Deployment

```bash
# Health check
curl https://ibc-play-XXXX.onrender.com/health

# API documentation
Open: https://ibc-play-XXXX.onrender.com/docs
```

---

### Option 2: Railway.app

#### Step 1: Create Railway Account

1. Go to https://railway.app
2. Sign up with GitHub

#### Step 2: Deploy from GitHub

1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose your `ibc-play` repository
4. Railway auto-detects Python

#### Step 3: Configure

Add environment variables in Settings:
```
SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
COINGECKO_API_URL=https://api.coingecko.com/api/v3
```

#### Step 4: Set Start Command

In Settings → Deploy:
```bash
python db_init.py && uvicorn main:app --host 0.0.0.0 --port $PORT
```

---

### Option 3: Heroku

#### Step 1: Install Heroku CLI

```bash
# macOS
brew tap heroku/brew && brew install heroku

# Ubuntu
curl https://cli-assets.heroku.com/install.sh | sh

# Windows
# Download from https://devcenter.heroku.com/articles/heroku-cli
```

#### Step 2: Create Procfile

```bash
echo "web: uvicorn main:app --host 0.0.0.0 --port \$PORT" > Procfile
```

#### Step 3: Deploy

```bash
# Login
heroku login

# Create app
heroku create ibc-play-app

# Set environment variables
heroku config:set SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
heroku config:set JWT_ALGORITHM=HS256
heroku config:set ACCESS_TOKEN_EXPIRE_MINUTES=1440
heroku config:set COINGECKO_API_URL=https://api.coingecko.com/api/v3

# Deploy
git push heroku main

# Initialize database
heroku run python db_init.py

# Open app
heroku open
```

---

### Option 4: DigitalOcean App Platform

#### Step 1: Create DigitalOcean Account

1. Go to https://www.digitalocean.com
2. Sign up and verify account

#### Step 2: Create App

1. Click "Create" → "App"
2. Connect GitHub repository
3. Select `ibc-play` repository

#### Step 3: Configure Build

```yaml
name: ibc-play
services:
  - name: api
    github:
      repo: your-username/ibc-play
      branch: main
    build_command: pip install -r requirements.txt && python db_init.py
    run_command: uvicorn main:app --host 0.0.0.0 --port 8080
    environment_variables:
      - key: SECRET_KEY
        value: <your-secret-key>
      - key: JWT_ALGORITHM
        value: HS256
      - key: ACCESS_TOKEN_EXPIRE_MINUTES
        value: 1440
      - key: COINGECKO_API_URL
        value: https://api.coingecko.com/api/v3
```

---

### Option 5: AWS Elastic Beanstalk

#### Step 1: Install EB CLI

```bash
pip install awsebcli
```

#### Step 2: Initialize

```bash
eb init -p python-3.11 ibc-play

# Select region
# Create new application
```

#### Step 3: Create Environment

```bash
eb create ibc-play-env

# Set environment variables
eb setenv SECRET_KEY=your-secret-key
eb setenv JWT_ALGORITHM=HS256
eb setenv ACCESS_TOKEN_EXPIRE_MINUTES=1440
eb setenv COINGECKO_API_URL=https://api.coingecko.com/api/v3
```

#### Step 4: Deploy

```bash
eb deploy
eb open
```

---

## 🔧 Post-Deployment Configuration

### 1. Database Persistence

For production, consider upgrading from SQLite:

**PostgreSQL on Render:**
1. Create PostgreSQL database in Render
2. Copy DATABASE_URL from dashboard
3. Update `main.py` to use PostgreSQL:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

### 2. Custom Domain

**Render:**
1. Go to Settings → Custom Domains
2. Add your domain
3. Update DNS records as instructed

**Railway:**
1. Go to Settings → Domains
2. Add custom domain
3. Configure DNS

### 3. SSL Certificate

Most platforms (Render, Heroku, Railway) provide automatic SSL.

For custom setup:
- Use Let's Encrypt
- Configure in platform settings

### 4. Monitoring

**Set up monitoring:**

```python
# Add to main.py
from datetime import datetime
import logging

@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"{request.method} {request.url}")
    start_time = datetime.utcnow()
    response = await call_next(request)
    duration = (datetime.utcnow() - start_time).total_seconds()
    logger.info(f"Duration: {duration}s")
    return response
```

### 5. Backup Strategy

**SQLite:**
```bash
# Schedule daily backups
cron: 0 0 * * * cp /app/ibc_play.db /backups/ibc_play_$(date +\%Y\%m\%d).db
```

**PostgreSQL:**
```bash
# Use platform's backup feature
# Or schedule pg_dump
```

---

## 🧪 Deployment Testing

### Automated Testing

Create `test_deployment.py`:

```python
import requests
import sys

API_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

def test_health():
    r = requests.get(f"{API_URL}/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    print("✅ Health check passed")

def test_register():
    r = requests.post(f"{API_URL}/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123"
    })
    assert r.status_code in [201, 400]  # 400 if user exists
    print("✅ Registration endpoint working")

def test_prices():
    r = requests.get(f"{API_URL}/crypto/prices")
    assert r.status_code == 200
    data = r.json()
    assert "BTC" in data
    assert "ETH" in data
    print("✅ Price endpoint working")

if __name__ == "__main__":
    test_health()
    test_register()
    test_prices()
    print("
✅ All deployment tests passed!")
```

Run tests:
```bash
python test_deployment.py https://your-app.onrender.com
```

---

## 🔒 Security Hardening

### 1. Environment Variables

Never commit sensitive data:
```bash
# Check what's being tracked
git status

# If .env was committed, remove it
git rm --cached .env
git commit -m "Remove .env from tracking"
```

### 2. Rate Limiting

Add rate limiting (requires `slowapi`):

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, user: UserLogin):
    # ... login logic
```

### 3. CORS Configuration

Restrict CORS in production:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains only
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### 4. HTTPS Only

Force HTTPS:
```python
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(HTTPSRedirectMiddleware)
```

---

## 📊 Monitoring & Maintenance

### 1. Set Up Logging

Use a logging service:
- **Render**: Built-in logs
- **Logtail**: External logging
- **Papertrail**: Centralized logging

### 2. Uptime Monitoring

- **UptimeRobot**: Free tier available
- **Pingdom**: Professional monitoring
- **StatusCake**: Status page

### 3. Error Tracking

Integrate Sentry:

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FastApiIntegration()],
)
```

---

## 🆘 Troubleshooting Common Issues

### Build Fails

**Issue**: Requirements installation fails

**Solution**:
```bash
# Specify Python version in runtime.txt
echo "python-3.11.0" > runtime.txt

# Or in render.yaml
envVars:
  - key: PYTHON_VERSION
    value: 3.11.0
```

### Database Connection Errors

**Issue**: SQLite locked or inaccessible

**Solution**: Use PostgreSQL for production:
```bash
# Add to requirements.txt
psycopg2-binary==2.9.9

# Update database connection
```

### Memory Issues

**Issue**: App crashes due to memory limits

**Solution**:
- Upgrade plan (Render Free tier: 512MB)
- Optimize queries
- Add pagination

### Slow Response Times

**Issue**: API responses are slow

**Solution**:
- Enable caching
- Use connection pooling
- Optimize database queries
- Add indices

---

## 📝 Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] Environment variables configured
- [ ] Database initialized
- [ ] Health check endpoint working
- [ ] API documentation accessible
- [ ] Frontend updated with production URL
- [ ] SSL certificate active
- [ ] Custom domain configured (if applicable)
- [ ] Monitoring set up
- [ ] Backup strategy in place
- [ ] Security headers configured
- [ ] Rate limiting enabled
- [ ] Error tracking integrated
- [ ] Documentation updated

---

## 🎉 You're Live!

Your IBC Play platform is now deployed and ready for users!

**Next Steps:**
1. Share your platform URL
2. Monitor initial user activity
3. Gather feedback
4. Iterate and improve

**Need Help?**
- Check platform documentation
- Review logs for errors
- Test all features manually
- Monitor resource usage

---

**Remember**: This is a demo platform. For real-money gambling, ensure:
- Proper licensing
- Regulatory compliance
- Security audits
- Legal consultation