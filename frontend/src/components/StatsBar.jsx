import { useEffect, useState } from 'react'
import { riskApi } from '../services/api'

function StatPill({ label, value, color }) {
  return (
    <div style={{
      display:    'flex',
      alignItems: 'center',
      gap:        8,
      padding:    '4px 14px',
      borderRight: '1px solid rgba(255,255,255,0.15)',
    }}>
      <span style={{
        width: 10, height: 10,
        borderRadius: '50%',
        background: color,
        flexShrink: 0,
      }} />
      <span style={{ fontSize: 12, opacity: 0.8 }}>{label}</span>
      <span style={{ fontSize: 13, fontWeight: 500 }}>{value}</span>
    </div>
  )
}

export default function StatsBar() {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    riskApi.getStats().then(r => setStats(r.data)).catch(() => {})
  }, [])

  if (!stats) return null

  return (
    <div style={{
      display:    'flex',
      alignItems: 'center',
      flexWrap:   'wrap',
      gap:        0,
    }}>
      <StatPill
        label="Total zones"
        value={stats.total_zones?.toLocaleString()}
        color="#B5D4F4"
      />
      <StatPill
        label="High risk"
        value={stats.by_level?.high?.toLocaleString()}
        color="#E24B4A"
      />
      <StatPill
        label="Medium risk"
        value={stats.by_level?.medium?.toLocaleString()}
        color="#EF9F27"
      />
      <StatPill
        label="Low risk"
        value={stats.by_level?.low?.toLocaleString()}
        color="#1D9E75"
      />
      <StatPill
        label="Avg risk"
        value={`${((stats.avg_risk ?? 0) * 100).toFixed(1)}%`}
        color="#B5D4F4"
      />
    </div>
  )
}