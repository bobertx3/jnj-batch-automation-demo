import { useState, useEffect, useCallback } from 'react'
import { KPIStrip } from './components/KPIStrip'
import { BatchTable } from './components/BatchTable'
import { BatchPanel } from './components/BatchPanel'
import { QualityEvents } from './components/QualityEvents'
import { Reports } from './components/Reports'
import type { Batch, KPIs } from './types'
import './App.css'

type Tab = 'batch-release' | 'quality-events' | 'reports'

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('batch-release')
  const [batches, setBatches] = useState<Batch[]>([])
  const [kpis, setKpis] = useState<KPIs | null>(null)
  const [selectedBatch, setSelectedBatch] = useState<Batch | null>(null)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('All')
  const [loading, setLoading] = useState(true)

  const fetchData = useCallback(async () => {
    try {
      const params = new URLSearchParams()
      if (search) params.set('search', search)
      if (statusFilter !== 'All') params.set('status', statusFilter)

      const [batchRes, kpiRes] = await Promise.all([
        fetch(`/api/batches?${params}`),
        fetch('/api/kpis'),
      ])
      setBatches(await batchRes.json())
      setKpis(await kpiRes.json())
    } catch (err) {
      console.error('Failed to fetch data:', err)
    } finally {
      setLoading(false)
    }
  }, [search, statusFilter])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const handleRelease = async (batchId: string, signedBy: string) => {
    const res = await fetch(`/api/batches/${batchId}/release`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ batch_id: batchId, signed_by: signedBy }),
    })
    if (res.ok) {
      setSelectedBatch(null)
      await fetchData()
    }
  }

  const handleTabChange = (tab: Tab) => {
    setActiveTab(tab)
    setSelectedBatch(null)
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-left">
          <div className="header-logo">
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
              <rect width="28" height="28" rx="6" fill="#1B3A5C" />
              <path d="M7 8h14v2H7zM7 13h10v2H7zM7 18h12v2H7z" fill="white" />
            </svg>
            <span className="header-title">Stelara<sup>&reg;</sup> Batch Release</span>
          </div>
          <nav className="header-nav">
            <a
              className={`nav-link ${activeTab === 'batch-release' ? 'active' : ''}`}
              onClick={() => handleTabChange('batch-release')}
            >
              Batch Release
            </a>
            <a
              className={`nav-link ${activeTab === 'quality-events' ? 'active' : ''}`}
              onClick={() => handleTabChange('quality-events')}
            >
              Quality Events
            </a>
            <a
              className={`nav-link ${activeTab === 'reports' ? 'active' : ''}`}
              onClick={() => handleTabChange('reports')}
            >
              Reports
            </a>
          </nav>
        </div>
        <div className="header-right">
          <span className="header-env">GMP Production <span className="header-env-detail">Good Manufacturing Practice</span></span>
        </div>
      </header>

      <main className="app-main">
        {activeTab === 'batch-release' && (
          <>
            <KPIStrip kpis={kpis} loading={loading} />
            <div className="content-area">
              <div className={`table-section ${selectedBatch ? 'with-panel' : ''}`}>
                <div className="table-toolbar">
                  <h2>Batch Disposition</h2>
                  <div className="toolbar-controls">
                    <div className="search-box">
                      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                        <circle cx="6.5" cy="6.5" r="5.5" stroke="#8896A7" strokeWidth="1.5" />
                        <path d="M10.5 10.5L15 15" stroke="#8896A7" strokeWidth="1.5" strokeLinecap="round" />
                      </svg>
                      <input
                        type="text"
                        placeholder="Search batches..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                      />
                    </div>
                    <select
                      className="status-filter"
                      value={statusFilter}
                      onChange={(e) => setStatusFilter(e.target.value)}
                    >
                      <option value="All">All Statuses</option>
                      <option value="Pending">Pending</option>
                      <option value="Released">Released</option>
                      <option value="Rejected">Rejected</option>
                    </select>
                  </div>
                </div>
                <BatchTable
                  batches={batches}
                  loading={loading}
                  onSelectBatch={setSelectedBatch}
                  selectedBatchId={selectedBatch?.batch_id}
                />
              </div>

              {selectedBatch && (
                <BatchPanel
                  batch={selectedBatch}
                  onClose={() => setSelectedBatch(null)}
                  onRelease={handleRelease}
                />
              )}
            </div>
          </>
        )}

        {activeTab === 'quality-events' && <QualityEvents />}
        {activeTab === 'reports' && <Reports />}
      </main>
    </div>
  )
}

export default App
