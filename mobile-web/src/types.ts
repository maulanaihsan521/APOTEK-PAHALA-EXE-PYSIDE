export interface User {
  id: number
  username: string
  full_name: string
  email: string | null
  role: string
  is_active: boolean
  theme: string
  font_scale: string
}

export interface Kpis {
  revenue: number
  revenue_delta: number | null
  demand: number
  demand_delta: number | null
  priority_count: number
  mape: number | null
  wape: number | null
  accuracy: number | null
  wape_label: string
  wape_medicine_count: number
  mape_label: string
  mape_medicine_count: number
}

export interface TrendPoint {
  label: string
  actual: number
  predicted: number | null
}

export interface TopMedicine {
  medicine_id: number
  name: string
  unit: string
  sold: number
  predicted: number
  sparkline: number[]
}

export interface StockSummary {
  aman: number
  perlu_perhatian: number
  kritis: number
  total: number
  percent_aman: number
  percent_perhatian: number
  percent_kritis: number
}

export interface ActivityItem {
  id: number
  type: string
  description: string
  user: string
  created_at: string
}

export interface DashboardData {
  period: { start: string; end: string; label: string; weeks: number }
  kpis: Kpis
  trend: { labels: string[]; weeks: string[]; actual: number[]; predicted: (number | null)[] }
  prediction_summary: {
    weeks: { label: string; value: number }[]
    total: number
    insight: string
    insight_level: string
    horizon: number
  }
  top_medicines: TopMedicine[]
  stock: StockSummary
  activities: ActivityItem[]
  is_demo: boolean
}

export interface Medicine {
  id: number
  code: string
  name: string
  category: string
  unit: string
  price: number
  min_stock: number
  safety_stock: number
  system_stock: number
  physical_stock: number
  difference: number
  stock_status: 'aman' | 'perlu_perhatian' | 'kritis'
  is_priority: boolean
  is_demo: boolean
}

export interface PredictionResult {
  run_id: number
  medicine: { id: number; code: string; name: string; unit: string; category: string }
  model_name: string
  model_label: string
  horizon_weeks: number
  start_date: string
  train_start: string
  train_end: string
  created_at: string
  is_demo: boolean
  metrics: Record<string, { mae: number; rmse: number; mape: number | null; wape: number | null; accuracy_indikatif: number | null; mape_zero_actual: number }>
  feature_importance: { feature: string; label: string; importance: number }[]
  train_size: number
  test_size: number
  backtest: { week: string; actual: number; predicted: number }[]
  actuals?: { week: string; value: number }[]
  forecast: {
    week_number: number
    date: string
    predicted: number
    lower_bound: number | null
    upper_bound: number | null
  }[]
  params: Record<string, unknown>
}

export interface NotificationItem {
  id: number
  category: string
  title: string
  message: string
  level: string
  is_read: boolean
  created_at: string
}
