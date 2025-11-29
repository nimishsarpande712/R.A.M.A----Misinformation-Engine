import { useState } from 'react'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function verdictBadge(verdict) {
  const v = (verdict || '').toLowerCase()
  if (!v) return null
  let label = verdict
  let cls = 'badge badge-unknown'
  if (v.includes('true') || v.includes('correct')) cls = 'badge badge-true'
  else if (v.includes('false') || v.includes('incorrect')) cls = 'badge badge-false'
  else if (v.includes('partly') || v.includes('mixed')) cls = 'badge badge-mixed'
  return <span className={cls}>{label}</span>
}

export default function ClaimCheckPage() {
  const [claim, setClaim] = useState('')
  const [language, setLanguage] = useState('en')
  const [sector, setSector] = useState('other')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!claim.trim()) {
      setError('Please paste a claim to check.')
      return
    }

    setError('')
    setLoading(true)
    setResult(null)

    try {
<<<<<<< HEAD
      const payload = { text: claim, language, sector }
=======
      const payload = { claim, language, sector }
>>>>>>> f7b9d1374505795c6df0a83d5b4547f2b7c6b837
      const { data } = await axios.post(`${API_BASE}/check-claim`, payload)
      setResult(data)
    } catch (err) {
      console.error(err)
      const message =
        err.response?.data?.detail ||
        err.message ||
        'Something went wrong while checking this claim.'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  const mode = result?.mode

  return (
    <div>
      <header className="page-header">
        <div className="page-eyebrow">Realtime fact-checking cockpit</div>
        <h1 className="page-title">Claim check console</h1>
        <p className="page-subtitle">
          Paste any WhatsApp forward, tweet, post or headline — we&apos;ll
          cross-check against trusted sources and show you what&apos;s real.
        </p>
      </header>

      <div className="page-shell">
        <section className="card-glass">
          <form onSubmit={handleSubmit}>
            <div className="field">
              <label className="field-label" htmlFor="claim">
                Claim / message
              </label>
              <textarea
                id="claim"
                className="textarea"
                placeholder="Paste the exact message or claim you want to verify…"
                value={claim}
                onChange={(e) => setClaim(e.target.value)}
              />
              <p className="field-hint">
                We only use this text for fact-checking and do not store
                personal identifiers.
              </p>
            </div>

            <div className="field-grid">
              <div className="field">
                <label className="field-label" htmlFor="language">
                  Language
                </label>
                <select
                  id="language"
                  className="select"
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                >
                  <option value="en">English</option>
                  <option value="hi">Hindi</option>
                </select>
              </div>

              <div className="field">
                <label className="field-label" htmlFor="sector">
                  Sector / theme
                </label>
                <select
                  id="sector"
                  className="select"
                  value={sector}
                  onChange={(e) => setSector(e.target.value)}
                >
                  <option value="health">Health</option>
                  <option value="election">Election</option>
                  <option value="disaster">Disaster / crisis</option>
                  <option value="communal">Communal / hate</option>
                  <option value="other">Other / mixed</option>
                </select>
              </div>
            </div>

            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? (
                <>
                  <span className="spinner" />
                  Checking claim…
                </>
              ) : (
                <>
                  Run fact-check
                  <span aria-hidden>↗</span>
                </>
              )}
            </button>

            {error && <div className="error-box">{error}</div>}
          </form>
        </section>

        <section className="card-glass card-alt">
          <div className="status-row">
            <div className="status-chip">
              <span
                className="status-dot"
                aria-hidden
                style={{ background: loading ? '#f97316' : '#22c55e' }}
              />
              {loading ? 'Running checks across sources…' : 'Ready for your next claim'}
            </div>
            <button
              type="button"
              className="btn-ghost"
              onClick={() => {
                setClaim('')
                setResult(null)
                setError('')
              }}
            >
              Clear
            </button>
          </div>

          {!result && !error && (
            <p className="result-empty">
              Results will appear here. We summarise verdicts from multiple
              fact-check streams — official bulletins, fact-check desks, and
              R.A.M.A&apos;s own retrieval engine.
            </p>
          )}

          {result && (
            <div>
              {mode === 'existing_fact_check' ? (
                <>
                  <div className="result-header">
                    <div className="result-title">Existing fact-check found</div>
                    {verdictBadge(result?.verdict)}
                  </div>
                  {result?.explanation && (
                    <>
                      <div className="result-section-title">Why</div>
                      <p className="result-body">{result.explanation}</p>
                    </>
                  )}
                  {result?.source && (
                    <>
                      <div className="result-section-title">Source</div>
                      <p className="result-body">
                        <a href={result.source} target="_blank" rel="noreferrer">
                          {result.source}
                        </a>
                      </p>
                    </>
                  )}
                </>
              ) : (
                <>
                  <div className="result-header">
                    <div className="result-title">AI-assisted analysis</div>
                    <span className="badge badge-pill badge-unknown">No direct match</span>
                  </div>
                  {result?.raw_answer && (
                    <>
                      <div className="result-section-title">Summary</div>
                      <p className="result-body">{result.raw_answer}</p>
                    </>
                  )}
                  {Array.isArray(result?.sources_used) && result.sources_used.length > 0 && (
                    <>
                      <div className="result-section-title">Sources consulted</div>
                      <ul className="result-source-list">
                        {result.sources_used.map((src, idx) => (
                          <li key={idx}>
                            <a
                              href={src.url || src}
                              target="_blank"
                              rel="noreferrer"
                            >
                              {src.title || src.url || src}
                            </a>
                          </li>
                        ))}
                      </ul>
                    </>
                  )}
                </>
              )}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
