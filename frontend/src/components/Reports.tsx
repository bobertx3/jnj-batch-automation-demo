import { useState, useEffect } from 'react'
import { BarChart3, TrendingUp, AlertTriangle, Clock } from 'lucide-react'

interface ReportData {
  status_breakdown: { status: string; count: number }[]
  monthly_trend: { month: string; total: number; released: number; pending: number; rejected: number }[]
  exception_rate: { total: number; with_exceptions: number; rate_pct: number; temp_fails: number; purity_fails: number }
  cycle_time_by_status: { status: string; avg_cycle: number; min_cycle: number; max_cycle: number }[]
}

function BarSegment({ value, max, color, label }: { value: number; max: number; color: string; label: string }) {
  const pct = max > 0 ? (value / max) * 100 : 0
  return (
    <div className="bar-segment-row">
      <span className="bar-label">{label}</span>
      <div className="bar-track">
        <div className="bar-fill" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
      <span className="bar-value">{value}</span>
    </div>
  )
}

export function Reports() {
  const [data, setData] = useState<ReportData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/reports/summary')
      .then((r) => r.json())
      .then(setData)
      .finally(() => setLoading(false))
  }, [])

  if (loading || !data) {
    return <div className="page-loading">Loading reports...</div>
  }

  const maxStatus = Math.max(...data.status_breakdown.map((s) => s.count))
  const statusColors: Record<string, string> = { Pending: '#E8A317', Released: '#2E7D32', Rejected: '#C62828' }
  const maxTrend = Math.max(...data.monthly_trend.map((t) => t.total))

  return (
    <div className="reports-page">
      <div className="page-header-row">
        <div>
          <h2 className="page-title">Reports &amp; Analytics</h2>
          <p className="page-subtitle">Batch disposition metrics and trend analysis for Stelara</p>
        </div>
      </div>

      <div className="reports-grid">
        {/* Status Breakdown */}
        <div className="report-card">
          <div className="report-card-header">
            <BarChart3 size={16} />
            <h3>Batch Dispositions by Status</h3>
          </div>
          <div className="report-card-body">
            {data.status_breakdown.map((s) => (
              <BarSegment
                key={s.status}
                value={s.count}
                max={maxStatus}
                color={statusColors[s.status] || '#1B3A5C'}
                label={s.status}
              />
            ))}
            <div className="report-total">
              Total: {data.status_breakdown.reduce((a, b) => a + b.count, 0)} batches
            </div>
          </div>
        </div>

        {/* Exception Rate */}
        <div className="report-card">
          <div className="report-card-header">
            <AlertTriangle size={16} />
            <h3>Exception Rate</h3>
          </div>
          <div className="report-card-body">
            <div className="exception-rate-display">
              <div className="rate-circle" style={{ background: data.exception_rate.rate_pct > 30 ? '#FFEBEE' : '#FFF3E0' }}>
                <span className="rate-value" style={{ color: data.exception_rate.rate_pct > 30 ? '#C62828' : '#E8A317' }}>
                  {data.exception_rate.rate_pct}%
                </span>
                <span className="rate-subtitle">of batches</span>
              </div>
            </div>
            <div className="exception-breakdown">
              <div className="exc-row">
                <span>Temperature Excursions</span>
                <span className="exc-count">{data.exception_rate.temp_fails}</span>
              </div>
              <div className="exc-row">
                <span>Purity Failures</span>
                <span className="exc-count">{data.exception_rate.purity_fails}</span>
              </div>
              <div className="exc-row total">
                <span>Total with Exceptions</span>
                <span className="exc-count">{data.exception_rate.with_exceptions} / {data.exception_rate.total}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Cycle Time by Status */}
        <div className="report-card">
          <div className="report-card-header">
            <Clock size={16} />
            <h3>Cycle Time by Status (Hours)</h3>
          </div>
          <div className="report-card-body">
            <table className="mini-table">
              <thead>
                <tr>
                  <th>Status</th>
                  <th>Avg</th>
                  <th>Min</th>
                  <th>Max</th>
                </tr>
              </thead>
              <tbody>
                {data.cycle_time_by_status.map((c) => (
                  <tr key={c.status}>
                    <td>
                      <span className="status-dot" style={{ backgroundColor: statusColors[c.status] || '#1B3A5C' }} />
                      {c.status}
                    </td>
                    <td><strong>{c.avg_cycle}h</strong></td>
                    <td>{c.min_cycle}h</td>
                    <td>{c.max_cycle}h</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Monthly Trend */}
        <div className="report-card wide">
          <div className="report-card-header">
            <TrendingUp size={16} />
            <h3>Monthly Batch Trend</h3>
          </div>
          <div className="report-card-body">
            <div className="trend-chart">
              {data.monthly_trend.map((m) => (
                <div key={m.month} className="trend-column">
                  <div className="trend-bars" style={{ height: 120 }}>
                    <div
                      className="trend-bar"
                      style={{
                        height: `${maxTrend > 0 ? (m.total / maxTrend) * 100 : 0}%`,
                        background: 'linear-gradient(to top, #1B3A5C, #2D5F8A)',
                      }}
                      title={`Total: ${m.total} | Released: ${m.released} | Pending: ${m.pending} | Rejected: ${m.rejected}`}
                    >
                      <span className="trend-bar-value">{m.total}</span>
                    </div>
                  </div>
                  <div className="trend-label">{m.month}</div>
                  <div className="trend-breakdown">
                    {m.released > 0 && <span style={{ color: '#2E7D32', fontSize: 10 }}>{m.released}R</span>}
                    {m.pending > 0 && <span style={{ color: '#E8A317', fontSize: 10 }}>{m.pending}P</span>}
                    {m.rejected > 0 && <span style={{ color: '#C62828', fontSize: 10 }}>{m.rejected}X</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
