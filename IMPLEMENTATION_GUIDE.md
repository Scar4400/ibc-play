# 📘 IBC Play - Complete Implementation Guide

This guide provides detailed, step-by-step instructions for setting up and deploying your IBC Play platform.

## 🎯 Overview

You'll learn how to:
1. Set up the development environment
2. Configure the backend API
3. Deploy the platform to production
4. Test all functionality
5. Monitor and maintain the system

**Time Required**: 30-45 minutes for full setup

---

## 📋 Prerequisites

Before starting, ensure you have:

- ✅ **Python 3.11+** installed ([Download](https://www.python.org/downloads/))
- ✅ **Git** installed ([Download](https://git-scm.com/downloads))
- ✅ **Text editor** (VS Code recommended)
- ✅ **GitHub account** (for deployment)
- ✅ **Command line** access (Terminal/PowerShell)

---

## 🚀 Part 1: Local Development Setup

### Step 1: Clone and Navigate

```bash
# Clone the repository
git clone https://github.com/Scar4400/ibc-play.git

# Navigate into the directory
cd ibc-play

# Verify files are present
ls -la
```

**Expected files:**
- `main.py` - Backend application
- `db_init.py` - Database setup
- `requirements.txt` - Dependencies
- `.env.example` - Configuration template
- `README.md` - Documentation

### Step 2: Create Virtual Environment

**macOS/Linux:**
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate
```

**Windows:**
```cmd
# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate
```

**Verify activation:**
You should see `(venv)` in your terminal prompt.

### Step 3: Install Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt

# Verify installation
pip list
```

**Expected packages:**
- fastapi
- uvicorn
- python-dotenv
- pydantic
- passlib
- python-jose
- httpx

### Step 4: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Generate secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Edit `.env` file:**
```bash
# Open in your editor
nano .env  # or code .env for VS Code
```

**Update SECRET_KEY:**
```env
SECRET_KEY=<paste-generated-key-here>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
COINGECKO_API_URL=https://api.coingecko.com/api/v3
```

### Step 5: Initialize Database

```bash
# Run database initialization script
python db_init.py
```

**Expected output:**
```
✅ Database initialized successfully!
Tables created:
  - users
  - wallets
  - transactions
  - bets
  - casino_rounds
  - crypto_holdings
```

**Verify database:**
```bash
# Check database file exists
ls -l ibc_play.db
```

### Step 6: Start the Server

```bash
# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### Step 7: Test the API

**Open a new terminal** (keep server running) and test:

```bash
# Test health endpoint
curl http://localhost:8000/health

# Expected response:
# {"status":"ok","db":"connected","crypto_api":"reachable","timestamp":"..."}
```

**Open in browser:**
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

---

## 🎨 Part 2: Frontend Setup

### Step 8: Serve the Frontend

The React frontend is included in the artifacts. To use it:

**Option A: Copy from artifact to your project**
1. Create a `frontend` directory
2. Save the React component as `index.html`
3. Open in browser

**Option B: Serve via Python**
```bash
# Create a simple server
python -m http.server 3000 --directory frontend
```

### Step 9: Configure Frontend API URL

Edit the frontend file and update `API_BASE`:

```javascript
// For local development
const API_BASE = 'http://localhost:8000';

// For production (after deployment)
const API_BASE = 'https://your-app-name.onrender.com';
```

---

## 🧪 Part 3: Testing the Platform

### Step 10: Manual Testing Workflow

**Test 1: User Registration**
```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPass123!"
  }'
```

**Test 2: Login**
```bash
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "TestPass123!"
  }'
```

**Save the token from response!**

**Test 3: Check Wallet**
```bash
# Replace YOUR_TOKEN with actual token
curl http://localhost:8000/wallet \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Test 4: Get Crypto Prices**
```bash
curl http://localhost:8000/crypto/prices
```

**Test 5: Deposit Cryptocurrency**
```bash
curl -X POST http://localhost:8000/deposit \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "crypto": "BTC",
    "amount": 0.01
  }'
```

**Test 6: Play Casino Game**
```bash
curl -X POST http://localhost:8000/casino/play \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "game": "dice",
    "bet_amount": 10,
    "bet_options": {
      "target": 50,
      "direction": "over"
    }
  }'
```

### Step 11: Run Automated Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest test_main.py -v

# Run with coverage
pytest test_main.py --cov=main --cov-report=html
```

**View coverage report:**
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

---

## 🌐 Part 4: Production Deployment

### Step 12: Prepare for Deployment

```bash
# Ensure all changes are committed
git add .
git commit -m "Ready for production deployment"
git push origin main
```

### Step 13: Deploy to Render.com

**A. Create Render Account**
1. Go to https://render.com
2. Click "Get Started"
3. Sign up with GitHub
4. Authorize Render to access your repositories

**B. Create New Web Service**
1. Click "New +" → "Web Service"
2. Connect your `ibc-play` repository
3. Configure:
   - **Name**: `ibc-play` (or your choice)
   - **Environment**: Python 3
   - **Region**: Choose closest to users
   - **Branch**: `main`
   - **Build Command**: 
     ```
     pip install -r requirements.txt && python db_init.py
     ```
   - **Start Command**: 
     ```
     uvicorn main:app --host 0.0.0.0 --port $PORT
     ```

**C. Add Environment Variables**

Click "Advanced" → "Add Environment Variable":

```
SECRET_KEY = <generate-new-secure-key>
JWT_ALGORITHM = HS256
ACCESS_TOKEN_EXPIRE_MINUTES = 1440
COINGECKO_API_URL = https://api.coingecko.com/api/v3
ENVIRONMENT = production
PYTHON_VERSION = 3.11.0
```

**Generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**D. Deploy**
1. Click "Create Web Service"
2. Wait 3-5 minutes for deployment
3. Monitor logs for any errors

**E. Get Your URL**

After successful deployment:
- Your API: `https://ibc-play-XXXX.onrender.com`
- Save this URL!

### Step 14: Update Frontend

Update frontend `API_BASE`:
```javascript
const API_BASE = 'https://ibc-play-XXXX.onrender.com';
```

### Step 15: Test Production Deployment

```bash
# Test health check
curl https://ibc-play-XXXX.onrender.com/health

# Test API docs
# Open in browser: https://ibc-play-XXXX.onrender.com/docs
```

---

## 📊 Part 5: Post-Deployment

### Step 16: Monitor Your Application

**Check Logs:**
1. Go to Render Dashboard
2. Click on your service
3. Click "Logs" tab
4. Monitor for errors

**Common log entries:**
- `INFO: Application startup complete` - ✅ Good
- `ERROR: Database connection failed` - ❌ Issue
- `INFO: User registered: username` - ✅ Activity

### Step 17: Set Up Monitoring

**Use Render's built-in monitoring:**
1. Go to "Metrics" tab
2. Monitor:
   - CPU usage
   - Memory usage
   - Request count
   - Response times

**Set up alerts (optional):**
1. Click "Settings"
2. Scroll to "Notifications"
3. Add email for alerts

### Step 18: Enable HTTPS

Render provides free SSL automatically:
- ✅ HTTPS is enabled by default
- ✅ Certificate renews automatically
- ✅ HTTP redirects to HTTPS

### Step 19: Custom Domain (Optional)

**Add custom domain:**
1. Go to "Settings"
2. Click "Custom Domain"
3. Add your domain
4. Update DNS records as instructed

**DNS Configuration:**
```
Type: CNAME
Name: www
Value: ibc-play-XXXX.onrender.com
```

---

## 🔧 Part 6: Maintenance & Troubleshooting

### Common Issues & Solutions

**Issue 1: Database Locked**
```bash
# Stop server
# Delete database
rm ibc_play.db
# Reinitialize
python db_init.py
# Restart server
```

**Issue 2: Port Already in Use**
```bash
# Find process using port 8000
lsof -ti:8000 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :8000  # Windows
```

**Issue 3: Module Not Found**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**Issue 4: CoinGecko API Rate Limit**
- Wait 60 seconds (cache TTL)
- Fallback prices are used automatically
- No action needed

**Issue 5: JWT Token Invalid**
- Token expired (24 hour limit)
- User needs to login again
- Check SECRET_KEY is consistent

### Database Backup

**Backup SQLite database:**
```bash
# Create backup
cp ibc_play.db backups/ibc_play_$(date +%Y%m%d).db

# Restore from backup
cp backups/ibc_play_20260105.db ibc_play.db
```

**For PostgreSQL (production):**
```bash
# Export
pg_dump DATABASE_URL > backup.sql

# Import
psql DATABASE_URL < backup.sql
```

### Performance Optimization

**Enable caching:**
```python
# Already implemented in main.py
# Price cache: 60 seconds TTL
# Adjust in code if needed
```

**Add database indices:**
```sql
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_transactions_timestamp ON transactions(timestamp);
```

---

## 📝 Part 7: Final Checklist

### Development Checklist
- [ ] Python 3.11+ installed
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] .env file configured
- [ ] Database initialized
- [ ] Server runs locally
- [ ] API endpoints tested
- [ ] Frontend configured
- [ ] All tests passing

### Deployment Checklist
- [ ] Code pushed to GitHub
- [ ] Render account created
- [ ] Web service deployed
- [ ] Environment variables set
- [ ] Production URL obtained
- [ ] Frontend updated with prod URL
- [ ] Health check passing
- [ ] API documentation accessible
- [ ] SSL/HTTPS working
- [ ] Monitoring enabled

### Security Checklist
- [ ] Secure SECRET_KEY generated
- [ ] .env not in version control
- [ ] Passwords hashed (bcrypt)
- [ ] JWT tokens expiring
- [ ] CORS configured properly
- [ ] Input validation enabled
- [ ] Error messages sanitized
- [ ] Logs monitored

---

## 🎉 You're Live!

Congratulations! Your IBC Play platform is now:
- ✅ Fully functional
- ✅ Deployed to production
- ✅ Secure and monitored
- ✅ Ready for users

## 📞 Next Steps

1. **Share your platform**: Give users your URL
2. **Gather feedback**: Monitor user activity
3. **Iterate**: Add features based on feedback
4. **Scale**: Upgrade resources as needed

## 🆘 Getting Help

If you encounter issues:

1. **Check logs**: Review error messages
2. **Read documentation**: README.md and DEPLOYMENT_GUIDE.md
3. **Test locally**: Reproduce issues in dev environment
4. **Search issues**: GitHub issues for similar problems
5. **Ask for help**: Create new GitHub issue

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Render Documentation](https://render.com/docs)
- [CoinGecko API](https://www.coingecko.com/en/api/documentation)
- [SQLite Documentation](https://www.sqlite.org/docs.html)

---

**Remember**: This is a demo platform. For real-money gambling:
- Obtain proper licenses
- Implement KYC/AML
- Conduct security audits
- Consult legal professionals

Good luck with your platform! 🚀