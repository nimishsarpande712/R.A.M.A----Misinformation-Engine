import { useState } from 'react'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export default function AdminPage() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [stats, setStats] = useState(null)

  const handleSync = async () => {
    setLoading(true)
    setError('')
    try {
      const { data } = await axios.post(`${API_BASE}/admin/ingest`)
<<<<<<< HEAD
      // Normalize backend response to the UI shape the page expects
      const normalized = {
        last_synced_at: new Date().toISOString(),
        total_docs: data.total_ingested ?? (data.results?.total ?? 0),
        sources: data.results ?? {},
        raw: data,
      }
      setStats(normalized)
=======
      setStats(data)
>>>>>>> f7b9d1374505795c6df0a83d5b4547f2b7c6b837
    } catch (err) {
      console.error(err)
      setError(
        err.response?.data?.detail ||
          err.message ||
          'Failed to sync sources from backend.',
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <header className="page-header">
        <div className="page-eyebrow">Admin utilities</div>
        <h1 className="page-title">Source ingestion & telemetry</h1>
        <p className="page-subtitle">
          Trigger background sync jobs to pull the latest bulletins, fact-checks
          and feeds into the R.A.M.A engine.
        </p>
      </header>

      <div className="page-shell">
        <section className="card-glass">
          <div className="field">
            <label className="field-label">Ingestion controls</label>
            <p className="field-hint">
              This will call the backend&apos;s <code>/admin/ingest</code> endpoint.
            </p>
          </div>
          <button
            type="button"
            className="btn-primary"
            onClick={handleSync}
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="spinner" /> Syncing feeds…
              </>
            ) : (
              <>Sync sources now ↻</>
            )}
          </button>
          {error && <div className="error-box">{error}</div>}
        </section>

        <section className="card-glass card-alt">
          <div className="result-header">
            <div className="result-title">Last sync status</div>
          </div>

          {!stats && !error && (
            <p className="result-empty">
              No sync run yet in this session. Trigger a run to see document
              counts and last refresh timestamps.
            </p>
          )}

          {stats && (
            <div className="result-body">
<<<<<<< HEAD
              <div style={{ marginBottom: 8, opacity: 0.9 }}>
                <small>Response snapshot (debug):</small>
                <pre style={{ maxHeight: 120, overflow: 'auto' }}>{JSON.stringify(stats.raw || stats, null, 2)}</pre>
              </div>
=======
>>>>>>> f7b9d1374505795c6df0a83d5b4547f2b7c6b837
              {typeof stats.last_synced_at === 'string' && (
                <p>
                  <strong>Last synced:</strong> {new Date(stats.last_synced_at).toLocaleString()}
                </p>
              )}

              {typeof stats.total_docs === 'number' && (
                <p>
                  <strong>Total documents:</strong> {stats.total_docs}
                </p>
              )}

              {stats.sources && (
                <>
                  <div className="result-section-title">By source</div>
                  <ul className="result-source-list">
                    {Object.entries(stats.sources).map(([name, count]) => (
                      <li key={name}>
                        <span>{name}</span>{' '}
                        <span style={{ opacity: 0.8 }}>· {count} docs</span>
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
