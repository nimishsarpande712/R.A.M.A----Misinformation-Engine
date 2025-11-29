# Debugging Guide: API Sources Not Returning Properly

## Quick Diagnostic Steps

If your API still isn't returning complete sources with evidence and URLs:

### Step 1: Check Backend is Running
```powershell
# Terminal 1
cd Backend
python -m uvicorn app.main_v2:app --reload --host 0.0.0.0 --port 8000
```

Expected output:
```
INFO:     Application startup complete
Uvicorn running on http://0.0.0.0:8000
```

### Step 2: Check Health Endpoint
```powershell
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "ok",
  "mode": "online",
  "models": {
    "gemini": "ok|down",
    "openrouter": "ok|down",
    "ollama": "ok|down"
  }
}
```

### Step 3: Check Data Ingestion
```powershell
# Is MCP server running?
curl http://localhost:8001/tools/news.get_latest?limit=5

# Should return news articles with complete fields:
# - title
# - text/description  
# - url
# - source
```

### Step 4: Run Full API Test
```powershell
cd Backend
python VERIFY_API_FIX.py
```

This will:
1. Test health endpoint
2. Test /verify with sample claims
3. Check all response fields
4. Verify sources have URLs
5. Verify snippets are 500+ chars

### Step 5: Manual API Test
```powershell
$body = @{
    text = "India won the Cricket World Cup"
    category = "other"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/verify" `
  -Method POST `
  -Headers @{"Content-Type" = "application/json"} `
  -Body $body | ConvertTo-Json -Depth 10
```

## Common Issues & Solutions

### Issue 1: "No sources returned"
**Cause**: Ingestion hasn't run or data isn't in vector store

**Solution**:
```bash
# Trigger ingestion
curl -X POST http://localhost:8000/admin/ingest \
  -H "X-Admin-Token: dev_admin_token_change_in_production"

# Wait 30 seconds...
# Then test verify endpoint again
```

### Issue 2: "Sources missing URLs"
**Cause**: MCP server not returning URL field OR ingestion failed

**Check**:
```bash
# 1. Check MCP output
curl http://localhost:8001/tools/news.get_latest?limit=1 | jq .

# Should have "url" field in each item

# 2. Check MongoDB has URLs
mongosh
> use rama
> db.news_items.findOne()
# Should have "url" field
```

### Issue 3: "Snippets too short"
**Cause**: Old code still running (didn't restart)

**Solution**:
```bash
# Stop backend: Ctrl+C in terminal
# Start again:
cd Backend
python -m uvicorn app.main_v2:app --reload --host 0.0.0.0 --port 8000
```

### Issue 4: "No models available"
**Cause**: LLM backends (Gemini, OpenRouter) not configured

**Solution**:
Check `.env` file has:
```
# At least ONE of these must be set:
GOOGLE_API_KEY=your_key
OPENROUTER_API_KEY=your_key
OLLAMA_URL=http://localhost:11434
```

**Test model availability**:
```bash
cd Backend
python test_model_gateway.py
```

## Expected Flow

```
User sends /verify request
    ↓
Backend receives claim
    ↓
1. Query Google Fact Check API (if available)
    ↓ (if found) Return live fact-check → ✅ WITH SOURCES
    ↓ (if not found) Continue...
    ↓
2. Query live news via MCP
    ↓ Add to context → ✅ WITH URLS
    ↓
3. Query vector store (Chroma) for similar articles
    ↓ From news_articles, gov_bulletins, social_posts
    ↓ Extract metadata (source, url) → ✅ WITH URLS
    ↓
4. Call LLM with all context
    ↓
5. Parse response
    ↓
6. Validate sources (ensure URLs present, snippets 500+ chars)
    ↓
7. Return VerifyResponse ✅ WITH COMPLETE SOURCES
```

## Logs to Check

### Backend Logs
Watch for these log messages:

```
✓ Good sign:
- "Found existing fact-check"
- "Found live fact-check"  
- "Found X live news articles"
- "Calling LLM with X sources"
- "Claim verification complete: true|false|misleading"

✗ Bad sign:
- "No existing fact-check found"
- "No relevant information found in knowledge base"
- "Model gateway error"
- "Live News API failed"
```

### Debug: Enable Verbose Logging
```python
# In Backend/app/main_v2.py
# Change:
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "DEBUG"),  # ← Add DEBUG
    ...
)
```

Then restart and watch for detailed logs.

## Files That Handle Sources

### Data Flow:

1. **MCP Server** → fetches live news
   - File: `Backend/app/mcp_client.py`
   - Function: `fetch_news()`

2. **Ingestion** → stores in vector DB
   - File: `Backend/app/ingestion_v2.py`
   - Function: `ingest_news()`, `ingest_gov()`, `ingest_social()`

3. **Vector Store** → retrieves similar
   - File: `Backend/app/vector_store.py`
   - Function: `query_similar()`

4. **Engine** → builds context with sources ✅ FIXED
   - File: `Backend/app/engine_v2.py`
   - Function: `_build_context_string()` → NOW 500 char snippets
   - Function: `check_claim()` → NOW validates URLs

5. **API** → returns response
   - File: `Backend/app/main_v2.py`
   - Endpoint: `POST /verify`

## Production Deployment Checklist

Before going live:

- [ ] All 3 LLM options configured (at least 1 working)
- [ ] MCP server running and returning data
- [ ] Ingestion completed successfully
- [ ] Vector store populated with documents
- [ ] Health check passes
- [ ] Test API returns sources with URLs
- [ ] Test API returns 500+ char snippets
- [ ] Response time < 10 seconds
- [ ] Error handling working (returns meaningful errors)

## Getting Help

If still stuck:
1. Run diagnostic: `python VERIFY_API_FIX.py`
2. Check logs: Look for errors in terminal
3. Verify each component:
   - MCP: `curl http://localhost:8001/tools/news.get_latest`
   - MongoDB: `mongosh` → check collections
   - Chroma: Check vector store has documents
   - Models: `python test_model_gateway.py`

---

**Made Changes**: ✅
**Tested Changes**: Run VERIFY_API_FIX.py
**Ready to Deploy**: When all checklist items pass
