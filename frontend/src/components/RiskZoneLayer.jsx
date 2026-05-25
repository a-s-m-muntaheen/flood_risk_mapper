import { useEffect, useRef } from 'react'
import { useMap } from 'react-leaflet'
import L from 'leaflet'
import { getRiskColor, scoreToOpacity } from '../utils/riskColors'

export default function RiskZoneLayer({ geojsonData, onZoneClick }) {
  const map      = useMap()
  const layerRef = useRef(null)

  useEffect(() => {
    if (!geojsonData || !geojsonData.features?.length) return

    // Remove previous layer
    if (layerRef.current) {
      layerRef.current.removeFrom(map)
    }

    const layer = L.geoJSON(geojsonData, {
      style: (feature) => {
        const { risk_level, risk_score } = feature.properties
        const color = getRiskColor(risk_level)
        return {
          fillColor:   color.fill,
          fillOpacity: scoreToOpacity(risk_score),
          color:       color.stroke,
          weight:      0.8,
          opacity:     0.9,
        }
      },
      onEachFeature: (feature, layer) => {
        const p = feature.properties
        layer.bindTooltip(
          `<div style="font-size:12px;line-height:1.6">
            <strong>${p.name}</strong><br/>
            Risk: <strong>${p.risk_level}</strong>
            (${(p.risk_score * 100).toFixed(0)}%)<br/>
            Elevation: ${p.elevation_m?.toFixed(1) ?? '—'}m<br/>
            Rainfall: ${p.rainfall_mm?.toFixed(0) ?? '—'}mm
          </div>`,
          { sticky: true }
        )
        layer.on('click', () => onZoneClick && onZoneClick(feature))
      },
    })

    layer.addTo(map)
    layerRef.current = layer

    return () => {
      if (layerRef.current) layerRef.current.removeFrom(map)
    }
  }, [geojsonData, map, onZoneClick])

  return null
}