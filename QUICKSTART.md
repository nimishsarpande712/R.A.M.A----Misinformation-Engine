# RAMA Quick Start Guide

## Complete Setup in 10 Minutes

This guide will get your RAMA system up and running quickly.

---

## Prerequisites Check

Run these commands to verify you have everything:

```powershell
# Python 3.10+
python --version

# Node.js 18+
node --version

# MongoDB
mongod --version

# Ollama (optional, for offline mode)
ollama --version
```

If any are missing, install them first.

---

## Step 1: Clone and Setup (2 min)

```powershell
# Clone repo (if not already done)
cd C:\Users\YourName\Documents\GitHub
git clone <repo-url> news-engine
cd news-engine
```

---

## Step 2: Backend Setup (3 min)

```powershell
cd Backend

# Create virtual environment
python -m venv .venv

# Activate it
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env

# Edit .env with your keys:
# - Add GEMINI_API_KEY (get from https://makersuite.google.com/app/apikey)
# - Add MONGODB_URI (default: mongodb://localhost:27017/)
# - Set X_ADMIN_TOKEN to a secure random string

# Open in notepad
notepad .env
```

**Required .env values:**
```env
GEMINI_API_KEY=your_gemini_key_here
MONGODB_URI=mongodb://localhost:27017/
X_ADMIN_TOKEN=my_secure_token_123
```

---

## Step 3: MCP Server Setup (1 min)

```powershell
cd ..\mcp-server

# Use same venv
..\Backend\.venv\Scripts\Activate.ps1

# Configure
cp .env.example .env

# Edit if you have these keys (optional):
# - NEWS_API_KEY (from https://newsapi.org)
# - FACT_CHECK_API_KEY (from Google Cloud Console)

# The system works without these keys using RSS feeds
```

---

## Step 4: Frontend Setup (2 min)

```powershell
cd ..\Frontend

# Install dependencies
npm install

# Configure
cp .env.example .env

# Edit .env - match admin token with backend
notepad .env
```

**Required .env values:**
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_ADMIN_TOKEN=my_secure_token_123
```

---

## Step 5: Start Services (2 min)

Open **3 separate PowerShell terminals**:

### Terminal 1: Backend
```powershell
cd news-engine\Backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main_v2:app --reload --port 8000
```

Expected output: `Application startup complete.`

### Terminal 2: MCP Server
```powershell
cd news-engine\mcp-server
..\Backend\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --port 8001
```

Expected output: `Uvicorn running on http://0.0.0.0:8001`

### Terminal 3: Frontend
```powershell
cd news-engine\Frontend
npm run dev
```

Expected output: `Local: http://localhost:5173/`

---

## Step 6: Initial Data Load (1 min)

In a 4th terminal:

```powershell
# Trigger ingestion
curl -X POST http://localhost:8000/admin/ingest `
  -H "X-Admin-Token: my_secure_token_123" `
  -H "Content-Type: application/json" `
  -d '{\"force\": false}'
```

Wait 30-60 seconds for ingestion to complete.

---

## Step 7: Test the System

### Open in Browser
```
http://localhost:5173
```

### Try These Test Queries

1. **Health Claim** (will use reasoned mode):
   ```
   Drinking hot water cures cancer
   ```
   Expected: `false` with health sources

2. **Election Claim** (will use reasoned mode):
   ```
   Voter turnout in 2024 elections exceeded 70%
   ```
   Expected: `true` or `unverified` with government sources

3. **Disaster Claim**:
   ```
   Red alert issued for heavy rainfall
   ```
   Expected: `unverified` or verdict based on recent IMD data

---

## Verify Everything Works

Run the automated test suite:

```powershell
cd Backend
.\.venv\Scripts\Activate.ps1
python test_api.py
```

Expected: All tests should pass (9/9 PASS)

---

## Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:5173 | User interface |
| Backend API | http://localhost:8000 | REST API |
| API Docs | http://localhost:8000/docs | Swagger UI |
| MCP Server | http://localhost:8001 | Ingestion tools |

---

## Quick Troubleshooting

### "MongoDB connection failed"
```powershell
# Start MongoDB (if installed as service)
net start MongoDB

# Or start manually
mongod --dbpath=C:\data\db
```

### "Gemini API error"
- Check your API key in Backend/.env
- Verify quota: https://makersuite.google.com/app/apikey
- System will fallback to Ollama if Gemini fails

### "All models down"
```powershell
# Install Ollama from https://ollama.ai
ollama pull mistral
ollama pull nomic-embed-text

# Start Ollama (usually auto-starts)
ollama serve
```

### "Port already in use"
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill it (replace PID)
taskkill /PID <PID> /F

# Or use different ports:
# Backend: --port 8080
# MCP: --port 8081
```

### "CORS errors in browser"
- Check CORS_ORIGINS in Backend/.env
- Make sure it includes http://localhost:5173
- Restart backend after changing .env

---

## Optional: Ollama Setup (for offline mode)

```powershell
# Download from https://ollama.ai/download

# Install models
ollama pull mistral
ollama pull nomic-embed-text

# Verify
ollama list

# Test
ollama run mistral "Hello"
```

---

## Next Steps

1. **Populate Knowledge Base**
   - Run ingestion regularly (daily/hourly)
   - Add custom fact-checks to MongoDB verified_claims collection

2. **Customize**
   - Adjust similarity threshold in Backend/.env
   - Modify system prompt in app/model_gateway_v2.py
   - Customize UI colors in Frontend/src/App.jsx

3. **Monitor**
   - Check logs: Backend terminal output
   - View claim logs: http://localhost:8000/admin/logs (with admin token)
   - Monitor MongoDB: `mongosh` → `use rama_db` → `db.claim_logs.find()`

---

## Production Deployment

See [README.md](README.md) "Production Deployment Checklist" section.

Key changes:
- Set secure X_ADMIN_TOKEN
- Enable MongoDB authentication
- Set up HTTPS/TLS
- Configure production CORS origins
- Use production Gemini API key
- Set up monitoring

---

## Getting Help

1. Check [README.md](README.md) for detailed documentation
2. Check [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) for feature status
3. Review backend logs in terminal
4. Test API with: http://localhost:8000/docs

---

## Demo Scenarios for Judges

Run these three scenarios to demonstrate all features:

### Scenario 1: Existing Fact-Check
```json
{
  "text": "Seeded claim from Google Fact Check database",
  "language": "en"
}
```
Expected: mode="existing_fact_check", sources from factcheck

### Scenario 2: Real-time Verification
```json
{
  "text": "New health rumor about vaccines",
  "language": "en",
  "category": "health"
}
```
Expected: mode="reasoned", sources from news/gov

### Scenario 3: Offline Mode
1. Stop internet connection or set FORCE_OFFLINE_MODE=1
2. Restart backend
3. Submit any claim
Expected: model_used="ollama", verdict with constrained context

---

**System ready! 🚀**

Your RAMA fact-checking system is now running and ready for demo.
