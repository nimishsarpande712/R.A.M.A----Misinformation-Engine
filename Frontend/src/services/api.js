/**
 * API Service for RAMA Frontend
 * Connects to backend at http://localhost:8000
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const ADMIN_TOKEN = import.meta.env.VITE_ADMIN_TOKEN || 'dev_admin_token_change_in_production';

/**
 * Generic API request handler with error handling
 */
async function apiRequest(endpoint, options = {}) {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || `API Error: ${response.status}`);
    }

    return data;
  } catch (error) {
    console.error('API Request Failed:', error);
    throw error;
  }
}

/**
 * Check system health
 * GET /health
 */
export async function checkHealth() {
  return apiRequest('/health');
}

/**
 * Verify a claim
 * POST /verify
 * 
 * @param {string} text - Claim text (min 10 chars)
 * @param {string} language - ISO 639-1 language code (default: 'en')
 * @param {string|null} category - Optional category (health, election, disaster, other)
 * @returns {Promise<VerifyResponse>}
 */
export async function verifyClaim(text, language = 'en', category = null) {
  const payload = {
    text,
    language,
  };

  if (category) {
    payload.category = category;
  }

  return apiRequest('/verify', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/**
 * Trigger ingestion (requires admin token)
 * POST /admin/ingest
 * 
 * @param {boolean} force - Force re-ingestion
 * @returns {Promise<IngestResponse>}
 */
export async function triggerIngestion(force = false) {
  return apiRequest('/admin/ingest', {
    method: 'POST',
    headers: {
      'X-Admin-Token': ADMIN_TOKEN,
    },
    body: JSON.stringify({ force }),
  });
}

/**
 * Submit user feedback
 * POST /feedback
 * 
 * @param {string} claimText - Original claim
 * @param {string} verdictReturned - Verdict that was returned
 * @param {string} comment - User feedback comment
 * @param {string|null} screenshotUrl - Optional screenshot URL
 * @returns {Promise<FeedbackResponse>}
 */
export async function submitFeedback(claimText, verdictReturned, comment, screenshotUrl = null) {
  const payload = {
    claim_text: claimText,
    verdict_returned: verdictReturned,
    comment,
  };

  if (screenshotUrl) {
    payload.screenshot_url = screenshotUrl;
  }

  return apiRequest('/feedback', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/**
 * Get recent claim logs (requires admin token)
 * GET /admin/logs
 * 
 * @param {number} limit - Number of logs to retrieve
 * @returns {Promise<LogsResponse>}
 */
export async function getClaimLogs(limit = 20) {
  return apiRequest(`/admin/logs?limit=${limit}`, {
    headers: {
      'X-Admin-Token': ADMIN_TOKEN,
    },
  });
}

/**
 * Get API information
 * GET /
 */
export async function getApiInfo() {
  return apiRequest('/');
}

/**
 * Type definitions for TypeScript-like documentation
 * 
 * @typedef {Object} Source
 * @property {string} type - Source type (news, factcheck, gov, social)
 * @property {string} source - Source name
 * @property {string} url - Source URL
 * @property {string} snippet - Relevant text snippet
 * 
 * @typedef {Object} VerifyResponse
 * @property {string} mode - 'existing_fact_check' or 'reasoned'
 * @property {string} verdict - 'true', 'false', 'unverified', or 'misleading'
 * @property {number} confidence - Confidence score (0.0-1.0)
 * @property {number} contradiction_score - Contradiction score (0.0-1.0)
 * @property {string} explanation - Short explanation
 * @property {string} raw_answer - Full model response
 * @property {Source[]} sources_used - List of sources
 * @property {string} timestamp - ISO 8601 timestamp
 * 
 * @typedef {Object} IngestResponse
 * @property {string} status - 'ok' or 'error'
 * @property {Object} ingested - Counts by source (news, gov, factchecks, social)
 * @property {string} last_synced - ISO 8601 timestamp
 * @property {string[]} errors - Error messages
 * 
 * @typedef {Object} FeedbackResponse
 * @property {string} status - 'ok'
 * @property {string} message - Success message
 * 
 * @typedef {Object} LogsResponse
 * @property {string} status - 'ok'
 * @property {number} count - Number of logs
 * @property {Object[]} logs - Array of log objects
 * 
 * @typedef {Object} HealthResponse
 * @property {string} status - 'ok' or 'degraded'
 * @property {string} mode - 'online' or 'offline'
 * @property {string|null} last_ingest - ISO 8601 timestamp or null
 * @property {Object} models - Model availability (gemini, openrouter, ollama)
 */

export default {
  checkHealth,
  verifyClaim,
  triggerIngestion,
  submitFeedback,
  getClaimLogs,
  getApiInfo,
};
