import type { Batch } from '../types'

interface Props {
  batches: Batch[]
  loading: boolean
  onSelectBatch: (batch: Batch) => void
  selectedBatchId?: string
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, { bg: string; color: string }> = {
    Pending: { bg: '#FFF3E0', color: '#E8A317' },
    Released: { bg: '#E8F5E9', color: '#2E7D32' },
    Rejected: { bg: '#FFEBEE', color: '#C62828' },
  }
  const s = styles[status] || styles.Pending
  return (
    <span className="status-badge" style={{ backgroundColor: s.bg, color: s.color }}>
      {status}
    </span>
  )
}

function TrafficLight({ pass, value }: { pass: boolean; value: string }) {
  return (
    <div className={`traffic-light ${pass ? 'pass' : 'fail'}`}>
      <div className={`light-dot ${pass ? 'green' : 'red'}`} />
      <span className="light-value">{value}</span>
    </div>
  )
}

export function BatchTable({ batches, loading, onSelectBatch, selectedBatchId }: Props) {
  if (loading) {
    return (
      <div className="table-container">
        <div className="table-loading">Loading batch data...</div>
      </div>
    )
  }

  if (batches.length === 0) {
    return (
      <div className="table-container">
        <div className="table-empty">No batches found</div>
      </div>
    )
  }

  return (
    <div className="table-container">
      <table className="batch-table">
        <thead>
          <tr>
            <th>Batch ID</th>
            <th>Drug</th>
            <th>Status</th>
            <th>Temp Check (37&deg;C &plusmn; 0.5&deg;C)</th>
            <th>Purity Check (&gt;98%)</th>
            <th>Cycle Time</th>
            <th>Manufactured</th>
            <th>Last Updated</th>
          </tr>
        </thead>
        <tbody>
          {batches.map((batch) => (
            <tr
              key={batch.batch_id}
              className={`batch-row clickable ${selectedBatchId === batch.batch_id ? 'selected' : ''}`}
              onClick={() => onSelectBatch(batch)}
            >
              <td className="batch-id-cell">
                <span className="batch-id-link">{batch.batch_id}</span>
              </td>
              <td>{batch.drug_name}</td>
              <td><StatusBadge status={batch.status} /></td>
              <td>
                <TrafficLight
                  pass={batch.temp_check}
                  value={`${batch.temp_actual.toFixed(1)}\u00B0C`}
                />
              </td>
              <td>
                <TrafficLight
                  pass={batch.purity_check}
                  value={`${batch.purity_actual.toFixed(1)}%`}
                />
              </td>
              <td>{batch.cycle_time_hours.toFixed(1)}h</td>
              <td>{new Date(batch.manufactured_date).toLocaleDateString()}</td>
              <td>{new Date(batch.last_updated).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
