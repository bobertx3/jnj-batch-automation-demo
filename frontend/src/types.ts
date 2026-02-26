export interface Batch {
  batch_id: string
  drug_name: string
  batch_name: string
  status: 'Pending' | 'Released' | 'Rejected'
  temp_actual: number
  temp_check: boolean
  purity_actual: number
  purity_check: boolean
  manufactured_date: string
  expiry_date: string
  cycle_time_hours: number
  last_updated: string
  exceptions: string | null
  signed_by: string | null
}

export interface KPIs {
  pending_count: number
  avg_cycle_time: number
  total_batches: number
  released_count: number
  rejected_count: number
  exception_count: number
}
