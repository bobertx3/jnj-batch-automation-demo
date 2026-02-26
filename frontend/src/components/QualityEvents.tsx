import { useState, useEffect } from 'react'
import { AlertTriangle, ThermometerSun, Droplets } from 'lucide-react'

interface QualityEvent {
  batch_id: string
  drug_name: string
  batch_name: string
  status: string
  temp_actual: number
  temp_check: boolean
  purity_actual: number
  purity_check: boolean
  cycle_time_hours: number
  last_updated: string
  exceptions: string | null
  event_type: string
  severity: string
}

export function QualityEvents() {
  const [events, setEvents] = useState<QualityEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('All')

  useEffect(() => {
    fetch('/api/quality-events')
      .then((r) => r.json())
      .then(setEvents)
      .finally(() => setLoading(false))
  }, [])

  const filtered = filter === 'All' ? events : events.filter((e) => e.event_type.includes(filter))

  if (loading) {
    return <div className="page-loading">Loading quality events...</div>
  }

  return (
    <div className="quality-events-page">
      <div className="page-header-row">
        <div>
          <h2 className="page-title">Quality Events</h2>
          <p className="page-subtitle">Batches with temperature excursions or purity failures</p>
        </div>
        <div className="toolbar-controls">
          <select className="status-filter" value={filter} onChange={(e) => setFilter(e.target.value)}>
            <option value="All">All Events</option>
            <option value="Temperature">Temperature Excursions</option>
            <option value="Purity">Purity Failures</option>
          </select>
        </div>
      </div>

      <div className="qe-summary-strip">
        <div className="qe-summary-card">
          <AlertTriangle size={20} color="#C62828" />
          <div>
            <div className="qe-summary-value">{events.length}</div>
            <div className="qe-summary-label">Total Events</div>
          </div>
        </div>
        <div className="qe-summary-card">
          <ThermometerSun size={20} color="#E8A317" />
          <div>
            <div className="qe-summary-value">{events.filter((e) => !e.temp_check).length}</div>
            <div className="qe-summary-label">Temp Excursions</div>
          </div>
        </div>
        <div className="qe-summary-card">
          <Droplets size={20} color="#7B1FA2" />
          <div>
            <div className="qe-summary-value">{events.filter((e) => !e.purity_check).length}</div>
            <div className="qe-summary-label">Purity Failures</div>
          </div>
        </div>
      </div>

      <div className="table-container">
        <table className="batch-table">
          <thead>
            <tr>
              <th>Batch ID</th>
              <th>Batch Name</th>
              <th>Event Type</th>
              <th>Severity</th>
              <th>Details</th>
              <th>Status</th>
              <th>Date</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((evt) => (
              <tr key={evt.batch_id} className="batch-row">
                <td className="batch-id-cell">
                  <span className="batch-id-link">{evt.batch_id}</span>
                </td>
                <td>{evt.batch_name}</td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    {!evt.temp_check && <ThermometerSun size={14} color="#E8A317" />}
                    {!evt.purity_check && <Droplets size={14} color="#7B1FA2" />}
                    <span>{evt.event_type}</span>
                  </div>
                </td>
                <td>
                  <span className={`severity-badge ${evt.severity.toLowerCase()}`}>
                    {evt.severity}
                  </span>
                </td>
                <td className="exception-detail-cell">
                  {!evt.temp_check && (
                    <div className="detail-line fail">Temp: {evt.temp_actual.toFixed(2)}&deg;C (target: 37.0&deg;C &plusmn; 0.5&deg;C)</div>
                  )}
                  {!evt.purity_check && (
                    <div className="detail-line fail">Purity: {evt.purity_actual.toFixed(2)}% (min: 98.0%)</div>
                  )}
                </td>
                <td>
                  <span
                    className="status-badge"
                    style={{
                      backgroundColor: evt.status === 'Pending' ? '#FFF3E0' : evt.status === 'Rejected' ? '#FFEBEE' : '#E8F5E9',
                      color: evt.status === 'Pending' ? '#E8A317' : evt.status === 'Rejected' ? '#C62828' : '#2E7D32',
                    }}
                  >
                    {evt.status}
                  </span>
                </td>
                <td>{new Date(evt.last_updated).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div className="table-empty">No quality events matching the filter</div>
        )}
      </div>
    </div>
  )
}
