# Google Fact Check Tools API Integration

## Overview

This integration fetches and normalizes fact-check data from Google's Fact Check Tools API into your news engine's standardized format.

**API Reference:** https://developers.google.com/fact-check/tools/api/reference/rest/v1alpha1/claims/search

## Features

- **Automatic Normalization**: Converts Google API responses to standardized fact-check format
- **Verdict Normalization**: Intelligently maps various rating formats to "TRUE", "FALSE", "MISLEADING"
- **Auto-Tagging**: Extracts relevant category tags from claim content
- **Multi-Query Support**: Fetch data for multiple topics in one call
- **Language Support**: Query fact-checks in different languages
- **Error Handling**: Graceful fallbacks and comprehensive logging

## Setup

### 1. Get API Key

1. Go to [Google Cloud Console](https://console.developers.google.com/)
2. Create a new project or select an existing one
3. Enable the **Fact Check Tools API**
4. Create an API key (OAuth 2.0 or API Key)

### 2. Configure Environment Variable

**Windows PowerShell:**
```powershell
$env:GOOGLE_FACTCHECK_API_KEY = "your-api-key-here"
```

**Windows Command Prompt:**
```cmd
set GOOGLE_FACTCHECK_API_KEY=your-api-key-here
```

**Linux/macOS:**
```bash
export GOOGLE_FACTCHECK_API_KEY="your-api-key-here"
```

## Usage

### Basic Usage - Single Query

```python
from app.google_factcheck_ingestion import fetch_factchecks_from_google

# Fetch fact checks about vaccines
results = fetch_factchecks_from_google(
    query="vaccine",
    language_code="en",
    max_claims=10
)

for fact_check in results:
    print(f"Claim: {fact_check['claim']}")
    print(f"Verdict: {fact_check['verdict']}")
    print(f"Source: {fact_check['source']}")
    print(f"Tags: {fact_check['tags']}")
```

### Multiple Queries

```python
from app.google_factcheck_ingestion import ingest_multiple_queries_from_google

# Fetch fact checks for multiple topics
results = ingest_multiple_queries_from_google(
    queries=["vaccine", "election", "climate"],
    language_code="en",
    max_claims_per_query=5
)

print(results)
# Output: {'vaccine': 5, 'election': 4, 'climate': 6}
```

### Integration with Main Ingestion Pipeline

```python
from app.ingestion import ingest_factchecks_from_google

# Ingest using default queries
results = ingest_factchecks_from_google()

# Or with custom queries
results = ingest_factchecks_from_google(
    queries=["disinformation", "misinformation"],
    language_code="en",
    max_claims_per_query=10
)
```

### Include in Full Ingestion

```python
from app.ingestion import ingest_all_sources

# This now includes Google Fact Check API
results = ingest_all_sources()

print(results['verified_claims_google'])  # Number from Google API
print(results['total'])  # Total from all sources
```

## Data Format

### Input (from Google API)

```json
{
  "claims": [
    {
      "claimText": "Vaccines cause autism",
      "claimDate": "2024-01-15",
      "languageCode": "en",
      "claimReview": {
        "url": "https://example.com/claim-1",
        "title": "False claim debunked",
        "publisher": {
          "name": "Fact Checker Organization",
          "site": "https://example.com"
        },
        "reviewRating": {
          "ratingValue": 1,
          "bestRating": 5,
          "worstRating": 1,
          "name": "False"
        },
        "textualRating": "Extensive research shows no link"
      }
    }
  ]
}
```

### Output (Normalized)

```json
{
  "id": "google_factcheck_0_Vaccines_cause_autism",
  "claim": "Vaccines cause autism",
  "verdict": "FALSE",
  "explanation": "False claim debunked",
  "source": "Fact Checker Organization",
  "url": "https://example.com/claim-1",
  "language": "en",
  "date": "2024-01-15",
  "tags": ["false", "health"],
  "provider": "google_factcheck",
  "original_data": {
    "textual_rating": "Extensive research shows no link",
    "rating_value": 1,
    "best_rating": 5,
    "worst_rating": 1
  }
}
```

## Verdict Normalization

The system automatically normalizes various rating formats:

### "TRUE" (Accurate/Correct)
- Rating names: "true", "accurate", "correct", "verified", "fact-checked", "correct fact"
- Rating value > best_rating/2 (with numeric ratings)

### "FALSE" (Inaccurate)
- Rating names: "false", "inaccurate", "incorrect", "fabricated", "false claim"
- Rating value ≤ best_rating/2

### "MISLEADING" (Partial/Out of Context)
- Rating names: "misleading", "partial", "out of context", "lacks context", "mixed"
- Default if no other match

## Tag Extraction

Automatic tags are added based on claim content:

- **health**: vaccine, covid, flu, disease, medicine, symptom, treatment, cancer, autism
- **election**: election, vote, voter, ballot, candidate, poll, voting
- **disaster**: earthquake, flood, storm, hurricane, tornado, tsunami, emergency
- **politics**: politician, senator, congressman, parliament, president, government
- **science**: study, research, scientist, climate, physics, chemistry
- **technology**: tech, ai, algorithm, software, computer, internet
- **economy**: economy, stock, market, business, money, price
- **immigration**: immigrant, immigration, border, refugee

## Testing

Run the test script to verify your setup:

```bash
python test_google_factcheck.py
```

### Test Functions

1. **Normalization Test** (runs without API key)
   - Tests the normalization logic with sample data
   - No API key required

2. **Single Query Test**
   - Fetches fact checks for one query
   - Requires API key

3. **Multiple Queries Test**
   - Fetches fact checks for multiple queries
   - Requires API key

## API Rate Limits

- Requests per day: 100 requests/day (free tier)
- Customize limits per project in Google Cloud Console
- Cache results to minimize API calls

## Error Handling

The integration gracefully handles errors:

```python
from app.google_factcheck_ingestion import fetch_factchecks_from_google

try:
    results = fetch_factchecks_from_google("vaccine")
except ValueError as e:
    print(f"Configuration error: {e}")
    # API key not set
except requests.RequestException as e:
    print(f"API request failed: {e}")
    # Network or API error
```

## Troubleshooting

### "GOOGLE_FACTCHECK_API_KEY environment variable not set"
- Set the environment variable before running
- Check it's set: `$env:GOOGLE_FACTCHECK_API_KEY` (PowerShell)

### "API request failed"
- Check your internet connection
- Verify API key is valid
- Check Google Cloud Console for rate limits
- Review API response in logs

### "No valid fact checks retrieved"
- Query may have no results
- Try broader search terms
- Increase `max_claims` parameter

## Performance Tips

1. **Cache Results**: Store fetched data locally to avoid repeated API calls
2. **Batch Queries**: Use `ingest_multiple_queries_from_google()` for efficiency
3. **Selective Ingestion**: Choose specific queries instead of fetching everything
4. **Background Jobs**: Run ingestion as a scheduled task, not on each request

## Example Queries by Category

### Health
- vaccine
- covid-19
- flu
- pandemic
- medical treatment

### Elections
- election
- voting
- voter fraud
- election results
- candidate

### Disasters
- earthquake
- flood
- hurricane
- tsunami
- disaster relief

### Climate
- climate change
- global warming
- renewable energy
- carbon emissions

## Architecture

```
google_factcheck_ingestion.py
├── fetch_factchecks_from_google()
│   └── Makes API request
├── normalize_google_response()
│   ├── normalize_verdict()
│   └── extract_tags()
└── ingest_factchecks_from_google()
    └── Upserts to verified_claims collection
```

## Integration with Vector Store

Ingested fact-checks are automatically:
1. Transformed to document format
2. Added to `verified_claims` collection
3. Indexed for semantic search
4. Made queryable through the engine

## Future Enhancements

- [ ] Schedule periodic ingestion
- [ ] Support for custom rating normalization
- [ ] Database caching to reduce API calls
- [ ] Support for fact-check update tracking
- [ ] Multi-language batch processing
- [ ] Advanced filtering options

## References

- [Google Fact Check Tools API](https://developers.google.com/fact-check/tools/api)
- [API Reference](https://developers.google.com/fact-check/tools/api/reference/rest/v1alpha1/claims/search)
- [Google Cloud Console](https://console.developers.google.com/)

## License

Same as the news-engine project.
