import { useState, useCallback, useEffect } from 'react'
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
import { riskApi, default as api  }   from './services/api'

const DHAKA_CENTER = [23.8103, 90.4125]

const FILTER_LEVELS = [
  { value: '',       label: 'All zones'   },
  { value: 'high',   label: 'High only'   },
  { value: 'medium', label: 'Medium only' },
  { value: 'low',    label: 'Low only'    },
]

export default function App() {
  const [zones,         setZones]         = useState(null)
  const [zonesLoading,  setZonesLoading]  = useState(false)
  const [filterLevel,   setFilterLevel]   = useState('')
  const [scoreResult,   setScoreResult]   = useState(null)
  const [scoreFeatures, setScoreFeatures] = useState(null)
  const [scoreLoading,  setScoreLoading]  = useState(false)
  const [selectedZone,  setSelectedZone]  = useState(null)

  const loadZones = useCallback((level = '') => {
    setZonesLoading(true)
    riskApi.getZones({ level, limit: 500 })
      .then(r => setZones(r.data))
      .catch(console.error)
      .finally(() => setZonesLoading(false))
  }, [])

  const handleFilterChange = (level) => {
    setFilterLevel(level)
    loadZones(level)
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

  // Seed CSRF cookie once on load
  useEffect(() => {
    api.get('/csrf/').catch(() => {})
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

        {/* Filter buttons */}
        <div style={{
          display: 'flex', gap: 6,
          flexShrink: 0,
        }}>
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
                color:        filterLevel === f.value
                  ? '#0C447C'
                  : 'white',
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
            {zonesLoading ? 'Loading...' : 'Load zones'}
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

        {/* Score panel — floats over the map */}
        <ScorePanel
          result={scoreResult}
          features={scoreFeatures}
          loading={scoreLoading}
          onClear={handleClearScore}
        />

        {/* Zone detail panel */}
        {selectedZone && (
          <div style={{
            position:     'absolute',
            bottom:       20,
            left:         '50%',
            transform:    'translateX(-50%)',
            background:   'white',
            borderRadius: 10,
            padding:      '12px 20px',
            boxShadow:    '0 2px 12px rgba(0,0,0,0.15)',
            zIndex:       1000,
            minWidth:     280,
            display:      'flex',
            alignItems:   'center',
            justifyContent: 'space-between',
            gap:          16,
          }}>
            <div>
              <div style={{ fontWeight: 500, fontSize: 14 }}>
                {selectedZone.properties.name}
              </div>
              <div style={{ fontSize: 12, color: '#666', marginTop: 2 }}>
                Risk: {selectedZone.properties.risk_level} —
                Score: {(selectedZone.properties.risk_score * 100).toFixed(1)}% —
                Elev: {selectedZone.properties.elevation_m?.toFixed(1)}m
              </div>
            </div>
            <button
              onClick={() => setSelectedZone(null)}
              style={{
                border: 'none', background: '#eee',
                borderRadius: 6, padding: '4px 10px',
                cursor: 'pointer', fontSize: 12,
              }}
            >
              Close
            </button>
          </div>
        )}

        {/* Draw hint */}
        {!zones && !scoreResult && (
          <div style={{
            position:   'absolute',
            bottom:     80,
            left:       '50%',
            transform:  'translateX(-50%)',
            background: 'rgba(12,68,124,0.85)',
            color:      'white',
            padding:    '8px 18px',
            borderRadius: 20,
            fontSize:   12,
            zIndex:     1000,
            pointerEvents: 'none',
          }}>
            Click "Load zones" to see risk overlay — or draw a polygon to score any area
          </div>
        )}
      </div>
    </div>
  )
}