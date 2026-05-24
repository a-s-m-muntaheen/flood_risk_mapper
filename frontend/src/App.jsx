import { useState, useEffect } from 'react'
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import api from './services/api'
import 'leaflet/dist/leaflet.css'
import './App.css'

// Fix Leaflet default marker icon on Vite
import L from 'leaflet'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'
L.Marker.prototype.options.icon = L.icon({
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
  iconAnchor: [12, 41],
})

const DHAKA_CENTER = [23.8103, 90.4125]

export default function App() {
  const [apiStatus, setApiStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.get('/flood-zones/health/')
      .then(res => {
        setApiStatus(res.data)
        setLoading(false)
      })
      .catch(err => {
        setError('Django API unreachable. Is the server running?')
        setLoading(false)
      })
  }, [])

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>

      {/* Header */}
      <div style={{
        background: '#0C447C',
        color: '#fff',
        padding: '12px 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexShrink: 0,
      }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 18, fontWeight: 500 }}>
            Smart Urban Flood Risk Mapper
          </h1>
          <p style={{ margin: 0, fontSize: 12, opacity: 0.7 }}>
            Bangladesh — AI-powered flood risk analysis
          </p>
        </div>

        {/* API status pill */}
        <div style={{
          background: loading ? '#444' : error ? '#A32D2D' : '#0F6E56',
          borderRadius: 20,
          padding: '4px 14px',
          fontSize: 12,
        }}>
          {loading ? 'Connecting...' : error ? 'API offline' : 'API connected'}
        </div>
      </div>

      {/* API response panel */}
      {!loading && (
        <div style={{
          background: error ? '#FCEBEB' : '#E1F5EE',
          borderBottom: `1px solid ${error ? '#F09595' : '#5DCAA5'}`,
          padding: '8px 24px',
          fontSize: 13,
          color: error ? '#791F1F' : '#085041',
          flexShrink: 0,
        }}>
          {error
            ? `Error: ${error}`
            : `Django says: "${apiStatus?.message}" — PostGIS: ${apiStatus?.postgis} — Test city: ${apiStatus?.test_coordinate?.city}`
          }
        </div>
      )}

      {/* Map */}
      <MapContainer
        center={DHAKA_CENTER}
        zoom={12}
        style={{ flex: 1 }}
      >
        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Marker position={DHAKA_CENTER}>
          <Popup>
            Dhaka, Bangladesh<br />
            Flood risk analysis center
          </Popup>
        </Marker>
      </MapContainer>

    </div>
  )
}