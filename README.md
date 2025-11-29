# 🛡️ R.A.M.A. - Reliable Agent for Misinformation Analysis

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)
![Node](https://img.shields.io/badge/node-18+-green.svg)
![License](https://img.shields.io/badge/license-MIT-purple.svg)

**An AI-powered fact-checking system that combats misinformation using multi-source verification, hybrid AI models, and real-time analysis.**

[Features](#-features) • [Quick Start](#-quick-start) • [Architecture](#-architecture) • [API Reference](#-api-reference) • [Team](#-team)

</div>

---

## 📖 What is R.A.M.A.?

R.A.M.A. (Reliable Agent for Misinformation Analysis) is an end-to-end fact-checking platform designed to verify claims in real-time. It combines:

- **🤖 Hybrid AI Models**: Gemini (online) with Ollama (offline) fallback
- **📰 Multi-Source Verification**: News APIs, Government bulletins, Fact-check databases, Social media
- **🔍 Vector Search (RAG)**: ChromaDB-powered semantic search for relevant evidence
- **🎨 Modern React UI**: Cinematic glassmorphism design with Three.js background effects
- **📊 Admin Dashboard**: Real-time system monitoring and data ingestion controls

---

## 👥 Team

| Name | Role |
|------|------|
| **Nimish** | Backend Lead |
| **Sarthak** | Backend |
| **Pavan** | Frontend |
| **Chetan** | Frontend |
| **Ashish** | MCP/Ingestion |

---

## ✨ Features

### Core Capabilities

| Feature | Description |
|---------|-------------|
| **Claim Verification** | Submit any claim and get verdict (true/false/misleading/unverified) with confidence scores |
| **Multi-Source Evidence** | Aggregates data from news, government sources, fact-checkers, and social media |
| **Hybrid AI** | Online (Gemini/OpenRouter) + Offline (Ollama) for continuous availability |
| **Vector RAG Pipeline** | Semantic search through ChromaDB for relevant context |
| **Admin Controls** | Trigger data ingestion, view logs, monitor system health |
| **User History** | Track verification history (MongoDB + Supabase) |

### Technical Highlights

- ✅ **FastAPI Backend** with async support
- ✅ **MCP Server** for modular data ingestion
- ✅ **ChromaDB** vector store with 4 collections
- ✅ **MongoDB** for persistent storage and logging
- ✅ **Supabase** integration for cloud data
- ✅ **React 19** with Vite and Tailwind CSS
- ✅ **Three.js** animated background effects

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                           │
│                    React + Vite (Port 5173)                     │
│              Three.js Background • Glassmorphism UI             │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP/REST
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND API (Port 8000)                    │
│                    FastAPI + Python 3.10+                       │
│         /verify • /admin/ingest • /health • /feedback           │
└──────────┬──────────────┬──────────────┬───────────────┬────────┘
           │              │              │               │
           ▼              ▼              ▼               ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌─────────────┐
    │  Model   │   │  Vector  │   │ MongoDB  │   │ MCP Server  │
    │ Gateway  │   │  Store   │   │ Database │   │ (Port 8001) │
    │          │   │ (Chroma) │   │          │   │             │
    └────┬─────┘   └──────────┘   └──────────┘   └──────┬──────┘
         │                                              │
    ┌────┴────┬──────────┐                    ┌─────────┴─────────┐
    │         │          │                    │                   │
    ▼         ▼          ▼                    ▼                   ▼
 Gemini  OpenRouter  Ollama              News APIs          Gov Sources
(primary) (fallback) (offline)           RSS Feeds          Fact-Checks
```

### Directory Structure

```
news-engine/
├── 📁 Backend/                    # FastAPI Backend Server
│   ├── 📁 app/
│   │   ├── main_v2.py            # Main FastAPI application
│   │   ├── engine_v2.py          # RAG verification engine
│   │   ├── model_gateway_v2.py   # AI model routing (Gemini/Ollama)
│   │   ├── ingestion_v2.py       # Data ingestion pipeline
│   │   ├── embeddings_v2.py      # Embedding generation
│   │   ├── vector_store.py       # ChromaDB operations
│   │   ├── mongodb.py            # MongoDB client
│   │   └── supabase_db.py        # Supabase integration
│   ├── 📁 data/
│   │   ├── fact_checks.json      # Seeded fact-checks
│   │   └── chroma/               # Vector database storage
│   ├── requirements.txt
│   └── .env.example
│
├── 📁 mcp-server/                 # MCP Data Ingestion Server
│   ├── 📁 app/
│   │   ├── main.py               # FastAPI MCP endpoints
│   │   ├── news.py               # News API integration
│   │   ├── gov.py                # Government bulletin fetcher
│   │   ├── factcheck.py          # Google Fact Check API
│   │   └── social.py             # Social media samples
│   └── requirements.txt
│
├── 📁 Frontend/                   # React Frontend Application
│   └── 📁 frontend/
│       └── 📁 frontend/          # ⚠️ ACTUAL WORKING FRONTEND
│           ├── 📁 src/
│           │   ├── App.jsx       # Main React app (1600+ lines!)
│           │   ├── main.jsx      # Entry point
│           │   └── index.css     # Tailwind styles
│           ├── package.json
│           ├── vite.config.js
│           └── tailwind.config.js
│
├── README.md                      # You are here!
├── QUICKSTART.md                  # Quick setup guide
└── IMPLEMENTATION_STATUS.md       # Development status
```

> ⚠️ **Important Note**: The working frontend is nested at `Frontend/frontend/frontend/` due to extraction issues. Keep this in mind during setup!

---

## 🚀 Quick Start

### Prerequisites

Before starting, make sure you have these installed:

| Software | Version | Check Command | Download |
|----------|---------|---------------|----------|
| Python | 3.10+ | `python --version` | [python.org](https://python.org) |
| Node.js | 18+ | `node --version` | [nodejs.org](https://nodejs.org) |
| MongoDB | 6.0+ | `mongod --version` | [mongodb.com](https://mongodb.com) |
| Ollama | Latest | `ollama --version` | [ollama.ai](https://ollama.ai) *(optional)* |

---

## 📋 Step-by-Step Setup

### Step 1: Clone & Navigate

```powershell
# Clone the repository (if not already done)
git clone https://github.com/nimishsarpande712/news-engine.git

# Navigate to project root
cd news-engine
```

---

### Step 2: Start MongoDB

MongoDB must be running before starting the backend.

```powershell
# Option A: If MongoDB is installed as a Windows service
net start MongoDB

# Option B: Start MongoDB manually
mongod --dbpath="C:\data\db"
```

> 💡 **Tip**: Create the `C:\data\db` folder if it doesn't exist: `mkdir C:\data\db`

---

### Step 3: Backend Setup

Open **Terminal 1** (PowerShell):

```powershell
# Navigate to Backend folder
cd Backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Install Python dependencies
pip install -r requirements.txt

# Create environment file from example
copy .env.example .env

# Edit .env with your API keys (use notepad or any editor)
notepad .env
```

**Configure `.env` file** (minimum required):

```env
# Required: Get from https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here

# Required: MongoDB connection
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DATABASE=rama_db

# Required: Admin authentication token (change this!)
X_ADMIN_TOKEN=my_secure_admin_token_123

# Optional: For offline mode
OLLAMA_ENDPOINT=http://localhost:11434/api/generate
OLLAMA_MODEL=mistral
```

**Start the Backend server:**

```powershell
# Run FastAPI backend (stay in Backend folder with venv activated)
python -m uvicorn app.main_v2:app --reload --port 8000
```

✅ **Success**: You should see `Application startup complete.`

🔗 **Test**: Open http://localhost:8000/docs in browser

---

### Step 4: MCP Server Setup

Open **Terminal 2** (PowerShell):

```powershell
# Navigate to MCP server folder
cd mcp-server

# Activate the Backend virtual environment (reuse it)
..\Backend\.venv\Scripts\Activate.ps1

# Install MCP dependencies
pip install -r requirements.txt

# Create environment file (optional - works without API keys)
copy .env.example .env

# Start MCP server
python -m uvicorn app.main:app --reload --port 8001
```

✅ **Success**: You should see `Uvicorn running on http://0.0.0.0:8001`

---

### Step 5: Frontend Setup ⚠️ IMPORTANT!

Open **Terminal 3** (PowerShell):

```powershell
# ⚠️ CRITICAL: The frontend is nested THREE levels deep!
# Navigate step by step:

cd Frontend
cd frontend  
cd frontend  

# You should now be in: news-engine/Frontend/frontend/frontend/

# Verify you're in the right place (should show package.json)
dir package.json

# Install Node.js dependencies
npm install

# Start development server
npm run dev
```

✅ **Success**: You should see `Local: http://localhost:5173/`

🔗 **Open**: http://localhost:5173 in your browser

---

### Step 6: Initial Data Ingestion

Open **Terminal 4** (PowerShell) or use any REST client:

```powershell
# Trigger initial data ingestion (replace token with your X_ADMIN_TOKEN from .env)
curl -X POST http://localhost:8000/admin/ingest `
  -H "X-Admin-Token: my_secure_admin_token_123" `
  -H "Content-Type: application/json" `
  -d '{\"force\": false}'
```

Or use the **Swagger UI**: 
1. Go to http://localhost:8000/docs
2. Find `POST /admin/ingest`
3. Click "Try it out"
4. Add header: `X-Admin-Token: my_secure_admin_token_123`
5. Execute

---

## 🎉 You're Done!

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost:5173 | Main user interface |
| **Backend API** | http://localhost:8000 | REST API |
| **API Documentation** | http://localhost:8000/docs | Swagger UI |
| **MCP Server** | http://localhost:8001 | Data ingestion tools |

---

## 📺 Using the Application

### Fact-Checking Interface

1. **Open** http://localhost:5173
2. **Select** a category (Health, Election, Disaster, etc.)
3. **Choose** language (English, Hindi, Marathi, Telugu)
4. **Paste** the claim you want to verify
5. **Click** "Run Analysis"
6. **View** the verdict with sources and confidence score

### Sample Claims to Test

| Category | Sample Claim | Expected Verdict |
|----------|--------------|------------------|
| Health | "Drinking hot water with lemon cures cancer" | FALSE |
| Election | "Voter turnout exceeded 70% in Phase 1" | TRUE/UNVERIFIED |
| Disaster | "Red alert issued for heavy rainfall in Mumbai" | UNVERIFIED |
| Finance | "50% tax on UPI transactions above ₹500" | FALSE |

---

## 📚 API Reference

### POST `/verify` - Verify a Claim

**Request:**
```json
{
  "text": "Drinking hot water cures cancer",
  "language": "en",
  "category": "health"
}
```

**Response:**
```json
{
  "mode": "reasoned",
  "verdict": "false",
  "confidence": 0.95,
  "contradiction_score": 0.85,
  "explanation": "This health claim contradicts established medical consensus...",
  "raw_answer": "Step 1: Analyzing claim...",
  "sources_used": [
    {
      "type": "factcheck",
      "source": "WHO",
      "url": "https://who.int/...",
      "snippet": "There is no scientific evidence..."
    }
  ],
  "timestamp": "2025-11-29T12:00:00Z"
}
```

### GET `/health` - System Health Check

```json
{
  "status": "ok",
  "mode": "online",
  "last_ingest": "2025-11-29T12:00:00Z",
  "models": {
    "gemini": "ok",
    "openrouter": "ok",
    "ollama": "down"
  }
}
```

### POST `/admin/ingest` - Trigger Data Ingestion

**Headers:** `X-Admin-Token: your_token`

```json
{
  "status": "ok",
  "ingested": {
    "news": 45,
    "gov": 12,
    "factchecks": 8,
    "social": 5
  },
  "last_synced": "2025-11-29T12:00:00Z"
}
```

### POST `/feedback` - Submit Feedback

```json
{
  "claim_text": "Original claim text",
  "verdict_returned": "false",
  "comment": "This verdict seems incorrect because..."
}
```

---

## 🛠️ Configuration

### Environment Variables (Backend/.env)

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | ✅ Yes | Google Gemini API key |
| `MONGODB_URI` | ✅ Yes | MongoDB connection string |
| `X_ADMIN_TOKEN` | ✅ Yes | Admin authentication token |
| `OLLAMA_ENDPOINT` | No | Ollama API endpoint (for offline mode) |
| `OLLAMA_MODEL` | No | Ollama model name (default: mistral) |
| `CHROMA_PERSIST_PATH` | No | ChromaDB storage path |
| `CORS_ORIGINS` | No | Allowed CORS origins |

---

## 🔧 Troubleshooting

### Common Issues

<details>
<summary><b>❌ "MongoDB connection failed"</b></summary>

**Solution:**
```powershell
# Start MongoDB service
net start MongoDB

# Or start manually
mongod --dbpath="C:\data\db"
```
</details>

<details>
<summary><b>❌ "Cannot find module" in Frontend</b></summary>

**Solution:** Make sure you're in the correct directory!
```powershell
# The frontend is nested three levels deep:
cd Frontend
cd frontend
cd frontend
npm install
```
</details>

<details>
<summary><b>❌ "Gemini API error"</b></summary>

**Solution:**
1. Verify your API key in `Backend/.env`
2. Check quota at https://makersuite.google.com/app/apikey
3. System will automatically fallback to Ollama if available
</details>

<details>
<summary><b>❌ "Port already in use"</b></summary>

**Solution:**
```powershell
# Find process using the port
netstat -ano | findstr :8000

# Kill the process (replace PID)
taskkill /PID <PID> /F
```
</details>

<details>
<summary><b>❌ "All models are down"</b></summary>

**Solution:** Install Ollama for offline fallback:
```powershell
# Download from https://ollama.ai
ollama pull mistral
ollama pull nomic-embed-text
```
</details>

---

## 📊 Performance

### Expected Latency

| Operation | Online (Gemini) | Offline (Ollama) |
|-----------|-----------------|------------------|
| `/verify` (cached) | ~500ms | ~300ms |
| `/verify` (new claim) | 3-5s | 8-12s |
| `/admin/ingest` | 30-60s | 30-60s |
| `/health` | <100ms | <100ms |

### Resource Usage

| Component | RAM Usage |
|-----------|-----------|
| Backend | 200-500 MB |
| MongoDB | 100-200 MB |
| ChromaDB | 50-100 MB |
| Ollama (mistral) | 4-8 GB |

---

## 🚢 Production Deployment

### Checklist

- [ ] Change `X_ADMIN_TOKEN` to a secure value
- [ ] Enable MongoDB authentication
- [ ] Configure HTTPS/TLS
- [ ] Set up rate limiting
- [ ] Configure CORS for production domain
- [ ] Set up monitoring (Sentry, etc.)
- [ ] Configure database backups
- [ ] Load test with expected traffic

---

## 📄 License

Copyright © 2025 Team R.A.M.A. All rights reserved.

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📞 Support

For issues or questions, contact the team leads:

| Area | Contact |
|------|---------|
| Backend | Nimish, Sarthak |
| Frontend | Pavan, Chetan |
| MCP/Ingestion | Ashish |

---

<div align="center">

**Built with ❤️ for fighting misinformation**

</div>
