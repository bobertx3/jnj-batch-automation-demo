import { useState } from 'react'
import { X, AlertTriangle, CheckCircle, Shield } from 'lucide-react'
import type { Batch } from '../types'

interface Props {
  batch: Batch
  onClose: () => void
  onRelease: (batchId: string, signedBy: string) => Promise<void>
}

export function BatchPanel({ batch, onClose, onRelease }: Props) {
  const [signedBy, setSignedBy] = useState('')
  const [releasing, setReleasing] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)

  const exceptions: { name: string; detail: string; severity: string }[] = []

  if (!batch.temp_check) {
    const deviation = Math.abs(batch.temp_actual - 37.0)
    exceptions.push({
      name: 'Temperature Excursion',
      detail: `Recorded ${batch.temp_actual.toFixed(1)}\u00B0C (deviation: \u00B1${deviation.toFixed(2)}\u00B0C from 37.0\u00B0C target). Acceptable range: 36.5\u00B0C\u201337.5\u00B0C.`,
      severity: deviation > 1.0 ? 'Critical' : 'Major',
    })
  }

  if (!batch.purity_check) {
    exceptions.push({
      name: 'Purity Below Threshold',
      detail: `Measured purity: ${batch.purity_actual.toFixed(1)}%. Minimum required: 98.0%.`,
      severity: batch.purity_actual < 96 ? 'Critical' : 'Major',
    })
  }

  const handleRelease = async () => {
    if (!signedBy.trim()) return
    setReleasing(true)
    try {
      await onRelease(batch.batch_id, signedBy.trim())
    } finally {
      setReleasing(false)
      setShowConfirm(false)
    }
  }

  const allChecksPass = batch.temp_check && batch.purity_check

  return (
    <div className="batch-panel">
      <div className="panel-header">
        <div>
          <h3>Batch Review</h3>
          <span className="panel-batch-id">{batch.batch_id}</span>
        </div>
        <button className="panel-close" onClick={onClose}>
          <X size={18} />
        </button>
      </div>

      <div className="panel-body">
        {/* Batch Info */}
        <div className="panel-section">
          <h4>Batch Information</h4>
          <div className="info-grid">
            <div className="info-item">
              <span className="info-label">Drug</span>
              <span className="info-value">{batch.drug_name}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Batch Name</span>
              <span className="info-value">{batch.batch_name}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Manufactured</span>
              <span className="info-value">{new Date(batch.manufactured_date).toLocaleDateString()}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Expiry</span>
              <span className="info-value">{new Date(batch.expiry_date).toLocaleDateString()}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Cycle Time</span>
              <span className="info-value">{batch.cycle_time_hours.toFixed(1)} hours</span>
            </div>
            <div className="info-item">
              <span className="info-label">Status</span>
              <span className="info-value">{batch.status}</span>
            </div>
          </div>
        </div>

        {/* Checks */}
        <div className="panel-section">
          <h4>Quality Checks</h4>
          <div className="checks-list">
            <div className={`check-item ${batch.temp_check ? 'pass' : 'fail'}`}>
              <div className="check-icon">
                {batch.temp_check ? <CheckCircle size={18} color="#2E7D32" /> : <AlertTriangle size={18} color="#C62828" />}
              </div>
              <div className="check-content">
                <span className="check-name">Temperature Control</span>
                <span className="check-value">{batch.temp_actual.toFixed(2)}&deg;C</span>
              </div>
              <span className={`check-status ${batch.temp_check ? 'compliant' : 'non-compliant'}`}>
                {batch.temp_check ? 'Compliant' : 'Non-Compliant'}
              </span>
            </div>

            <div className={`check-item ${batch.purity_check ? 'pass' : 'fail'}`}>
              <div className="check-icon">
                {batch.purity_check ? <CheckCircle size={18} color="#2E7D32" /> : <AlertTriangle size={18} color="#C62828" />}
              </div>
              <div className="check-content">
                <span className="check-name">Purity Analysis</span>
                <span className="check-value">{batch.purity_actual.toFixed(2)}%</span>
              </div>
              <span className={`check-status ${batch.purity_check ? 'compliant' : 'non-compliant'}`}>
                {batch.purity_check ? 'Compliant' : 'Non-Compliant'}
              </span>
            </div>
          </div>
        </div>

        {/* Exceptions - Review by Exception */}
        {exceptions.length > 0 && (
          <div className="panel-section exceptions-section">
            <h4>
              <AlertTriangle size={16} color="#C62828" style={{ marginRight: 6, verticalAlign: 'middle' }} />
              Exceptions ({exceptions.length})
            </h4>
            {exceptions.map((exc, i) => (
              <div key={i} className="exception-card">
                <div className="exception-header">
                  <span className="exception-name">{exc.name}</span>
                  <span className={`exception-severity ${exc.severity.toLowerCase()}`}>
                    {exc.severity}
                  </span>
                </div>
                <p className="exception-detail">{exc.detail}</p>
              </div>
            ))}
          </div>
        )}

        {allChecksPass && (
          <div className="panel-section all-pass">
            <CheckCircle size={20} color="#2E7D32" />
            <span>All quality checks passed. Batch is ready for release.</span>
          </div>
        )}

        {/* Digital Sign-Off — only for Pending batches */}
        {batch.status === 'Pending' && (
          <div className="panel-section sign-off-section">
            <h4>
              <Shield size={16} style={{ marginRight: 6, verticalAlign: 'middle' }} />
              Digital Sign-Off
            </h4>

            {!showConfirm ? (
              <>
                <div className="sign-off-input">
                  <label>Reviewer Name</label>
                  <input
                    type="text"
                    placeholder="Enter your name for sign-off..."
                    value={signedBy}
                    onChange={(e) => setSignedBy(e.target.value)}
                  />
                </div>
                <button
                  className="release-btn"
                  disabled={!signedBy.trim()}
                  onClick={() => setShowConfirm(true)}
                >
                  Release Batch
                </button>
              </>
            ) : (
              <div className="confirm-dialog">
                <p>
                  Are you sure you want to release <strong>{batch.batch_id}</strong>?
                  {exceptions.length > 0 && (
                    <span className="confirm-warning">
                      {' '}This batch has {exceptions.length} exception(s).
                    </span>
                  )}
                </p>
                <div className="confirm-actions">
                  <button
                    className="confirm-btn"
                    onClick={handleRelease}
                    disabled={releasing}
                  >
                    {releasing ? 'Releasing...' : 'Confirm Release'}
                  </button>
                  <button className="cancel-btn" onClick={() => setShowConfirm(false)}>
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Released confirmation */}
        {batch.status === 'Released' && (
          <div className="panel-section all-pass">
            <CheckCircle size={20} color="#2E7D32" />
            <div>
              <div>Batch released{batch.signed_by ? ` by ${batch.signed_by}` : ''}</div>
              <div style={{ fontSize: 11, color: '#5F6B7A', marginTop: 2 }}>
                {new Date(batch.last_updated).toLocaleString()}
              </div>
            </div>
          </div>
        )}

        {/* Rejected info */}
        {batch.status === 'Rejected' && (
          <div className="panel-section" style={{ display: 'flex', alignItems: 'center', gap: 10, background: '#FFEBEE', border: '1px solid #FFCDD2', borderRadius: 6, padding: 14 }}>
            <X size={20} color="#C62828" />
            <div>
              <div style={{ fontWeight: 700, color: '#C62828' }}>Batch Rejected</div>
              <div style={{ fontSize: 11, color: '#5F6B7A', marginTop: 2 }}>
                {new Date(batch.last_updated).toLocaleString()}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
