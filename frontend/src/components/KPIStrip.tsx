import type { KPIs } from '../types'
import { Activity, Clock, CheckCircle, XCircle, AlertTriangle, BarChart3 } from 'lucide-react'

interface Props {
  kpis: KPIs | null
  loading: boolean
}

export function KPIStrip({ kpis, loading }: Props) {
  if (loading || !kpis) {
    return (
      <div className="kpi-strip">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="kpi-card skeleton" />
        ))}
      </div>
    )
  }

  const cards = [
    { label: 'Batches Pending Release', value: kpis.pending_count, icon: Activity, color: '#E8A317' },
    { label: 'Average Cycle Time', value: `${kpis.avg_cycle_time}h`, icon: Clock, color: '#1B3A5C' },
    { label: 'Total Batches', value: kpis.total_batches, icon: BarChart3, color: '#1B3A5C' },
    { label: 'Released', value: kpis.released_count, icon: CheckCircle, color: '#2E7D32' },
    { label: 'Rejected', value: kpis.rejected_count, icon: XCircle, color: '#C62828' },
    { label: 'With Exceptions', value: kpis.exception_count, icon: AlertTriangle, color: '#E8A317' },
  ]

  return (
    <div className="kpi-strip">
      {cards.map((card) => (
        <div key={card.label} className="kpi-card">
          <div className="kpi-icon" style={{ color: card.color }}>
            <card.icon size={20} />
          </div>
          <div className="kpi-content">
            <div className="kpi-value" style={{ color: card.color }}>{card.value}</div>
            <div className="kpi-label">{card.label}</div>
          </div>
        </div>
      ))}
    </div>
  )
}
