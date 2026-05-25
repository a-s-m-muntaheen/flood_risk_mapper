import { useState, useCallback, useEffect, useRef } from 'react'
import { MapContainer, TileLayer } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import './App.css'

import L from 'leaflet'
import markerIcon   from 'leaflet/dist/images/marker-icon.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'
L.Marker.prototype.options.icon = L.icon({
  iconUrl:    markerIcon,
  shadowUrl:  markerShadow,
  iconAnchor: [12, 41],
})

import RiskZoneLayer from './components/RiskZoneLayer'
import DrawControl   from './components/DrawControl'
import MapLegend     from './components/MapLegend'
import ScorePanel    from './components/ScorePanel'
import StatsBar      from './components/StatsBar'
import ChatPanel     from './components/ChatPanel'
import { riskApi, default as api } from './services/api'

const DHAKA_CENTER = [23.8103, 90.4125]

const FILTER_LEVELS = [
  { value: '',       label: 'All zones'   },
  { value: 'high',   label: 'High only'   },
  { value: 'medium', label: 'Medium only' },
  { value: 'low',    label: 'Low only'    },
]

export default function App() {
  const [chatOpen,      setChatOpen]      = useState(false)
  const [zones,         setZones]         = useState(null)
  const [zonesLoading,  setZonesLoading]  = useState(false)
  const [filterLevel,   setFilterLevel]   = useState('')
  const [scoreResult,   setScoreResult]   = useState(null)
  const [scoreFeatures, setScoreFeatures] = useState(null)
  const [scoreLoading,  setScoreLoading]  = useState(false)
  const [selectedZone,  setSelectedZone]  = useState(null)

  // Use a ref so loadZones is stable and won't re-trigger useEffect
  const loadZonesRef = useRef(null)
  loadZonesRef.current = (level = '') => {
    setZonesLoading(true)
    riskApi.getZones({ level, limit: 500 })
      .then(r => setZones(r.data))
      .catch(console.error)
      .finally(() => setZonesLoading(false))
  }

  const loadZones = useCallback((level = '') => {
    loadZonesRef.current(level)
  }, [])

  // Seed CSRF + auto-load all zones once on mount
  useEffect(() => {
    api.get('/csrf/').catch(() => {})
    loadZonesRef.current('')
  }, []) // empty deps — runs once only

  const handleFilterChange = (level) => {
    setFilterLevel(level)
    loadZonesRef.current(level)
  }

  const handleShapeDrawn = useCallback((geometry) => {
    setScoreLoading(true)
    setScoreResult(null)
    riskApi.scoreGeometry(geometry)
      .then(r => {
        setScoreResult(r.data.result)
        setScoreFeatures(r.data.features)
      })
      .catch(console.error)
      .finally(() => setScoreLoading(false))
  }, [])

  const handleClearScore = useCallback(() => {
    setScoreResult(null)
    setScoreFeatures(null)
  }, [])

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>

      {/* ── Header ───────────────────────────────── */}
      <div style={{
        background:     '#0C447C',
        color:          'white',
        padding:        '0 16px',
        display:        'flex',
        alignItems:     'center',
        justifyContent: 'space-between',
        flexShrink:     0,
        minHeight:      52,
        gap:            16,
      }}>
        <div style={{ flexShrink: 0 }}>
          <div style={{ fontSize: 15, fontWeight: 500 }}>
            Smart Urban Flood Risk Mapper
          </div>
          <div style={{ fontSize: 11, opacity: 0.65 }}>
            Bangladesh — AI-powered spatial risk analysis
          </div>
        </div>

        <StatsBar />

        <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
          {FILTER_LEVELS.map(f => (
            <button
              key={f.value}
              onClick={() => handleFilterChange(f.value)}
              style={{
                padding:      '4px 10px',
                fontSize:     11,
                borderRadius: 6,
                border:       'none',
                cursor:       'pointer',
                background:   filterLevel === f.value
                  ? 'rgba(255,255,255,0.9)'
                  : 'rgba(255,255,255,0.15)',
                color:        filterLevel === f.value ? '#0C447C' : 'white',
                fontWeight:   filterLevel === f.value ? 500 : 400,
              }}
            >
              {f.label}
            </button>
          ))}

          <button
            onClick={() => loadZones(filterLevel)}
            disabled={zonesLoading}
            style={{
              padding:      '4px 12px',
              fontSize:     11,
              borderRadius: 6,
              border:       'none',
              cursor:       zonesLoading ? 'wait' : 'pointer',
              background:   '#185FA5',
              color:        'white',
              marginLeft:   4,
            }}
          >
            {zonesLoading ? 'Loading...' : 'Reload'}
          </button>
        </div>
      </div>

      {/* ── Map ──────────────────────────────────── */}
      <div style={{ flex: 1, position: 'relative' }}>
        <MapContainer
          center={DHAKA_CENTER}
          zoom={8}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            attribution='&copy; OpenStreetMap contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {zones && (
            <RiskZoneLayer
              geojsonData={zones}
              onZoneClick={setSelectedZone}
            />
          )}

          <DrawControl
            onShapeDrawn={handleShapeDrawn}
            onShapeDeleted={handleClearScore}
          />

          <MapLegend />
        </MapContainer>

        <ScorePanel
          result={scoreResult}
          features={scoreFeatures}
          loading={scoreLoading}
          onClear={handleClearScore}
        />

        {selectedZone && (() => {
          const props = selectedZone.properties || {};
          const riskLevel = props.risk_level || 'unknown';
          const riskScore = props.risk_score || 0;
          const elevation = props.elevation_m;
          
          // Dynamic risk theming
          const theme = riskLevel === 'high' 
            ? { bg: '#FEF2F2', border: '#FCA5A5', text: '#DC2626' }
            : riskLevel === 'medium' 
              ? { bg: '#FFFBEB', border: '#FCD34D', text: '#D97706' }
              : { bg: '#ECFDF5', border: '#6EE7B7', text: '#059669' };

          return (
            <div style={{
              position: 'absolute', bottom: 24, left: '50%', transform: 'translateX(-50%)',
              background: 'rgba(255, 255, 255, 0.95)', borderRadius: 14, padding: '16px 20px',
              boxShadow: '0 8px 30px rgba(0,0,0,0.12), 0 2px 8px rgba(0,0,0,0.06)',
              zIndex: 1000, minWidth: 300, maxWidth: '90vw',
              display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16,
              border: `1px solid ${theme.border}44`, backdropFilter: 'blur(10px)',
              animation: 'fadeSlideUp 0.25s ease-out'
            }}>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                  <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600, color: '#111827', lineHeight: 1.2 }}>
                    {props.name || 'Unknown Zone'}
                  </h3>
                  <span style={{
                    padding: '3px 8px', borderRadius: 999, fontSize: 11, fontWeight: 600, letterSpacing: 0.3,
                    background: theme.bg, color: theme.text, border: `1px solid ${theme.border}`
                  }}>
                    {riskLevel.toUpperCase()}
                  </span>
                </div>
                
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px 12px', fontSize: 13, color: '#4B5563' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ color: '#9CA3AF', fontSize: 12 }}>Score</span>
                    <span style={{ fontWeight: 600, color: theme.text }}>{(riskScore * 100).toFixed(1)}%</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ color: '#9CA3AF', fontSize: 12 }}>Elevation</span>
                    <span style={{ fontWeight: 600 }}>{elevation?.toFixed(1) ?? '—'} m</span>
                  </div>
                </div>
              </div>

              <button 
                onClick={() => setSelectedZone(null)}
                style={{
                  background: 'none', border: 'none', cursor: 'pointer', padding: 4, borderRadius: 6,
                  color: '#9CA3AF', transition: 'all 0.2s', fontSize: 18, lineHeight: 1, flexShrink: 0
                }}
                onMouseEnter={e => e.currentTarget.style.color = '#EF4444'}
                onMouseLeave={e => e.currentTarget.style.color = '#9CA3AF'}
                title="Close panel"
              >
                ✕
              </button>
            </div>
          );
        })()}

        <ChatPanel isOpen={chatOpen} onClose={() => setChatOpen(false)} />

        <button
          onClick={() => setChatOpen(o => !o)}
          style={{
            position:     'absolute',
            bottom:       24,
            right:        12,
            zIndex:       1000,
            background:   '#0C447C',
            color:        'white',
            border:       'none',
            borderRadius: 24,
            padding:      '10px 18px',
            fontSize:     13,
            fontWeight:   500,
            cursor:       'pointer',
            boxShadow:    '0 2px 10px rgba(0,0,0,0.2)',
            display:      chatOpen ? 'none' : 'block',
          }}
        >
          Ask AI assistant
        </button>
      </div>
    </div>
  )
}