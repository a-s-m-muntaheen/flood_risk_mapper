import { getRiskColor } from '../utils/riskColors'

const FEATURE_LABELS = {
  avg_elevation_m:     { label: 'Avg elevation',    unit: 'm',  invert: true  },
  avg_rainfall_mm:     { label: 'Monsoon rainfall', unit: 'mm', invert: false },
  avg_slope_degrees:   { label: 'Avg slope',        unit: '°',  invert: true  },
  distance_to_river_m: { label: 'River distance',   unit: 'm',  invert: true  },
  land_use_code:       { label: 'Land use code',    unit: '',   invert: false },
}

const LAND_USE_LABELS = {
  0: 'Water body',
  1: 'Low agriculture',
  2: 'Urban / mixed',
  3: 'Highland agri.',
  4: 'Forest / hills',
}

function FeatureBar({ name, value, invert }) {
  const max = {
    avg_elevation_m: 200, avg_rainfall_mm: 600,
    avg_slope_degrees: 45, distance_to_river_m: 50000,
    land_use_code: 4,
  }
  const pct   = Math.min(100, (value / max[name]) * 100)
  const color = invert
    ? pct > 60 ? '#1D9E75' : pct > 30 ? '#EF9F27' : '#E24B4A'
    : pct > 60 ? '#E24B4A' : pct > 30 ? '#EF9F27' : '#1D9E75'

  return (
    <div style={{ marginBottom: 8 }}>
      <div style={{
        display: 'flex', justifyContent: 'space-between',
        fontSize: 12, marginBottom: 3,
        color: '#444',
      }}>
        <span>{FEATURE_LABELS[name]?.label}</span>
        <span style={{ fontWeight: 500 }}>
          {name === 'land_use_code'
            ? LAND_USE_LABELS[value] ?? value
            : `${typeof value === 'number' ? value.toFixed(1) : value} ${FEATURE_LABELS[name]?.unit}`
          }
        </span>
      </div>
      <div style={{
        height: 5, background: '#eee',
        borderRadius: 3, overflow: 'hidden',
      }}>
        <div style={{
          height: '100%', width: `${pct}%`,
          background: color, borderRadius: 3,
          transition: 'width 0.4s ease',
        }} />
      </div>
    </div>
  )
}

export default function ScorePanel({ result, features, loading, onClear }) {
  if (!result && !loading) return null

  const color = result ? getRiskColor(result.risk_level) : null

  return (
    <div style={{
      position:     'absolute',
      top:          70,
      right:        12,
      width:        260,
      background:   'white',
      borderRadius: 10,
      boxShadow:    '0 2px 12px rgba(0,0,0,0.15)',
      zIndex:       1000,
      overflow:     'hidden',
    }}>
      {/* Header */}
      <div style={{
        background:  result ? color.fill : '#888',
        color:       'white',
        padding:     '10px 14px',
        display:     'flex',
        justifyContent: 'space-between',
        alignItems:  'center',
      }}>
        <div>
          <div style={{ fontSize: 11, opacity: 0.85 }}>
            Flood risk score
          </div>
          {loading
            ? <div style={{ fontSize: 16, fontWeight: 500 }}>
                Analysing...
              </div>
            : <div style={{ fontSize: 22, fontWeight: 600 }}>
                {(result.risk_score * 100).toFixed(1)}%
                <span style={{ fontSize: 13, marginLeft: 6, opacity: 0.9 }}>
                  {result.risk_level}
                </span>
              </div>
          }
        </div>
        <button
          onClick={onClear}
          style={{
            background: 'rgba(255,255,255,0.25)',
            border: 'none', borderRadius: 6,
            color: 'white', cursor: 'pointer',
            padding: '4px 8px', fontSize: 12,
          }}
        >
          Clear
        </button>
      </div>

      {!loading && result && (
        <div style={{ padding: '12px 14px' }}>

          {/* Confidence bar */}
          <div style={{
            fontSize: 11, color: '#888',
            marginBottom: 10,
          }}>
            Model confidence: {(result.confidence * 100).toFixed(0)}%
          </div>

          {/* Probability pills */}
          <div style={{
            display: 'flex', gap: 6,
            marginBottom: 14,
          }}>
            {Object.entries(result.probabilities).map(([level, prob]) => (
              <div key={level} style={{
                flex: 1, textAlign: 'center',
                background: getRiskColor(level).fill + '22',
                border: `1px solid ${getRiskColor(level).fill}`,
                borderRadius: 6, padding: '4px 0',
              }}>
                <div style={{
                  fontSize: 11,
                  color: getRiskColor(level).stroke,
                  fontWeight: 500,
                }}>
                  {level}
                </div>
                <div style={{
                  fontSize: 13,
                  color: getRiskColor(level).stroke,
                }}>
                  {(prob * 100).toFixed(0)}%
                </div>
              </div>
            ))}
          </div>

          {/* Feature bars */}
          <div style={{
            borderTop: '1px solid #eee',
            paddingTop: 10,
          }}>
            <div style={{
              fontSize: 11, color: '#888',
              marginBottom: 8, fontWeight: 500,
            }}>
              Contributing factors
            </div>
            {features && Object.entries(FEATURE_LABELS).map(([key]) => (
              features[key] !== undefined && (
                <FeatureBar
                  key={key}
                  name={key}
                  value={features[key]}
                  invert={FEATURE_LABELS[key].invert}
                />
              )
            ))}
          </div>
        </div>
      )}
    </div>
  )
}