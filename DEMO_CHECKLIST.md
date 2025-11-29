# RAMA Deployment & Demo Checklist

## Pre-Demo Setup (Day Before)

### Environment Setup
- [ ] MongoDB installed and running
- [ ] Python 3.10+ installed
- [ ] Node.js 18+ installed
- [ ] Ollama installed with models pulled
  ```bash
  ollama pull mistral
  ollama pull nomic-embed-text
  ```

### API Keys Obtained
- [ ] Gemini API key from https://makersuite.google.com/app/apikey
- [ ] (Optional) NewsAPI key from https://newsapi.org
- [ ] (Optional) Google Fact Check API key

### Backend Configuration
- [ ] Backend/.env created from .env.example
- [ ] GEMINI_API_KEY set
- [ ] MONGODB_URI configured
- [ ] X_ADMIN_TOKEN set to secure value
- [ ] All dependencies installed: `pip install -r requirements.txt`

### MCP Server Configuration
- [ ] mcp-server/.env created from .env.example
- [ ] API keys configured (if available)
- [ ] Dependencies installed

### Frontend Configuration
- [ ] Frontend/.env created from .env.example
- [ ] VITE_API_BASE_URL set to backend URL
- [ ] VITE_ADMIN_TOKEN matches backend
- [ ] Dependencies installed: `npm install`

### Initial Data Population
- [ ] Backend started
- [ ] MCP server started
- [ ] Ingestion triggered successfully
- [ ] Verify data in MongoDB:
  ```javascript
  mongosh
  use rama_db
  db.news_items.countDocuments()
  db.verified_claims.countDocuments()
  ```

### Testing
- [ ] Run `python Backend/test_api.py` - all tests pass
- [ ] Manually test /verify endpoint
- [ ] Verify frontend connects to backend
- [ ] Test admin panel with admin token

---

## Demo Day - Pre-Presentation (30 min before)

### Services Running
- [ ] MongoDB running: `net start MongoDB`
- [ ] Backend running on port 8000
  ```bash
  cd Backend
  .venv\Scripts\Activate.ps1
  python -m uvicorn app.main_v2:app --reload --port 8000
  ```
- [ ] MCP server running on port 8001
  ```bash
  cd mcp-server
  python -m uvicorn app.main:app --reload --port 8001
  ```
- [ ] Frontend running on port 5173
  ```bash
  cd Frontend
  npm run dev
  ```

### Health Checks
- [ ] Backend health: http://localhost:8000/health
  - Status: "ok"
  - Mode: "online" or "offline"
  - Models: at least one "ok"
- [ ] Frontend loads: http://localhost:5173
- [ ] API docs accessible: http://localhost:8000/docs

### Demo Scenarios Prepared
- [ ] **Scenario 1**: Existing fact-check claim ready
- [ ] **Scenario 2**: New health rumor ready
- [ ] **Scenario 3**: Offline mode test ready (toggle FORCE_OFFLINE_MODE)

### Backup Plans
- [ ] Screenshots of successful runs saved
- [ ] Video recording of working demo (optional)
- [ ] Localhost tunnel ready (ngrok/localtunnel) if needed for remote demo

---

## Demo Flow (10 minutes)

### Introduction (1 min)
"RAMA is a fact-checking system with hybrid online/offline operation..."

### Architecture Overview (1 min)
Show diagram:
- React Frontend
- FastAPI Backend
- Model Gateway (Gemini → Ollama)
- Vector Store (ChromaDB)
- MongoDB
- MCP Server

### Live Demo - Scenario 1: Existing Fact-Check (2 min)
1. Open frontend
2. Enter: "Drinking hot lemon water cures cancer"
3. Select: Health category
4. Submit
5. **Show**:
   - Verdict: false
   - Explanation with sources
   - Confidence score
   - Source attribution (factcheck type)

### Live Demo - Scenario 2: Real-Time Verification (3 min)
1. Enter new claim about elections/health
2. Submit and explain while waiting:
   - "System is now querying knowledge base..."
   - "Building context from news, gov bulletins..."
   - "Calling Gemini for reasoning..."
3. **Show**:
   - Mode: "reasoned"
   - Multiple sources (news, gov, factcheck)
   - Explanation breakdown
   - Raw LLM reasoning (optional)

### Live Demo - Scenario 3: Offline Mode (2 min)
1. Show health status: mode="online"
2. Toggle FORCE_OFFLINE_MODE=1 or disconnect internet
3. Restart backend
4. Show health status: mode="offline"
5. Submit same claim
6. **Show**:
   - System still works
   - Uses Ollama (local model)
   - Deterministic response with available context

### Admin Panel Demo (1 min)
1. Click Admin button
2. Show:
   - Last sync time
   - Ingestion counts
   - Model availability status
3. (Optional) Trigger new ingestion

---

## Judge's Questions - Prepared Answers

### Technical Implementation

**Q: How does the system handle conflicting sources?**
A: The LLM is prompted to weigh sources by type (gov > factcheck > news) and provide contradiction scores. The system explicitly lists sources used so judges can verify.

**Q: What if all models fail?**
A: Three-layer fallback: Gemini → OpenRouter → Ollama. If all fail, return 503 with clear error message. Logs stored in MongoDB for debugging.

**Q: How do you prevent prompt injection?**
A: Strict system prompt enforcement. Context is clearly separated from instruction. Input validation with Pydantic. No user input in system prompts.

**Q: Can it scale?**
A: Current setup handles demo load. For production:
- Replace ChromaDB with Weaviate
- Add Redis caching
- Horizontal scaling with load balancer
- Async ingestion with Celery

### Data & Privacy

**Q: Where does data come from?**
A: Four sources via MCP server:
1. NewsAPI + RSS (Indian Express, NDTV)
2. Government feeds (PIB, WHO)
3. Google Fact Check API
4. Social samples (demo data)

**Q: How do you handle PII?**
A: User IPs hashed before storing. No authentication required for claims. Feedback is optional. Screenshots sanitized before storage (production).

**Q: Data retention policy?**
A: Configurable. Demo: unlimited. Production: claim_logs 90 days, feedback 1 year, knowledge base indefinite.

### Business Model

**Q: How will you monetize?**
A: Three tiers:
1. B2G: Government dashboards (licensing)
2. B2B: Media API for real-time verification (subscription)
3. B2C: Browser extension + mobile app (freemium)

**Q: Competition?**
A: Unique differentiators:
- Hybrid online/offline (works in low connectivity)
- Multi-source RAG with attribution
- Explainable verdicts with reasoning
- Open architecture (self-hostable)

### Impact

**Q: How do you measure success?**
A: Metrics:
- Claims verified per day
- Accuracy rate (manual audit sample)
- User trust score (surveys)
- Viral misinformation stopped (tracked by hash)

**Q: Regional language support?**
A: Current: English, Hindi, Marathi, Telugu in UI.
Backend: Language-agnostic vector search.
Roadmap: Add 10+ Indian languages with region-specific sources.

---

## Post-Demo Tasks

### Immediate (After Presentation)
- [ ] Note all judge feedback
- [ ] Capture any error logs
- [ ] Save successful demo screenshots

### Follow-Up (Within 24 hours)
- [ ] Address any bugs discovered
- [ ] Implement quick-win suggestions
- [ ] Update documentation with learnings

### Production (If Selected)
- [ ] Deploy to cloud (AWS/GCP)
- [ ] Set up monitoring (Sentry)
- [ ] Configure CI/CD
- [ ] Implement rate limiting
- [ ] Add analytics dashboard
- [ ] Launch beta with test users

---

## Emergency Troubleshooting During Demo

### Frontend not loading
```bash
# Quick restart
cd Frontend
npm run dev
```

### Backend 500 errors
1. Check MongoDB is running
2. Check logs in terminal
3. Restart backend
4. Use Swagger UI as fallback: http://localhost:8000/docs

### Ollama not responding
1. Check if running: `ollama list`
2. Restart: `ollama serve`
3. Worst case: Use online mode only with Gemini

### Gemini API errors
1. Check quota: https://makersuite.google.com/app/apikey
2. System will auto-fallback to Ollama
3. Show fallback as a feature ("offline mode works!")

### Network issues
1. Switch to localhost
2. Use pre-recorded demo video
3. Show code walkthrough instead

---

## Success Criteria

Demo is successful if judges see:

1. ✅ **Real-time claim verification** with < 10s response
2. ✅ **Multiple source attribution** (news, gov, factcheck)
3. ✅ **Offline capability** demonstrated
4. ✅ **Explainable verdicts** with reasoning
5. ✅ **Admin functionality** (ingestion, logs)
6. ✅ **Clean, responsive UI**
7. ✅ **No critical errors** during demo

---

## Presentation Tips

1. **Be confident**: You built a production-grade system
2. **Explain as you demo**: "Here the system is querying 4 collections..."
3. **Show the code**: Open app/engine_v2.py to show RAG logic
4. **Emphasize impact**: "This can stop viral misinformation in hours, not days"
5. **Handle errors gracefully**: "This shows our fallback system working"
6. **Time management**: Keep scenarios under 3 min each

---

## Final Checklist (5 min before)

- [ ] All services running
- [ ] Frontend responsive
- [ ] Demo claims ready in notepad
- [ ] Swagger UI open as backup
- [ ] Water bottle nearby
- [ ] Deep breath
- [ ] You got this! 🚀

---

**Good luck with your demo!**

Remember: You've built a comprehensive fact-checking system that addresses a real problem with solid engineering. Be proud and show it off!
