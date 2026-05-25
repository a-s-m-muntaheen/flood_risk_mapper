import { useMap } from 'react-leaflet'
import { useEffect, useRef } from 'react'
import L from 'leaflet'
import { RISK_COLORS } from '../utils/riskColors'

export default function MapLegend() {
  const map     = useMap()
  const ctrlRef = useRef(null)

  useEffect(() => {
    const legend = L.control({ position: 'bottomleft' })

    legend.onAdd = () => {
      const div = L.DomUtil.create('div')
      div.style.cssText = `
        background: white;
        padding: 10px 14px;
        border-radius: 8px;
        border: 1px solid #ddd;
        font-size: 12px;
        line-height: 1.8;
        min-width: 130px;
      `
      div.innerHTML = `
        <div style="font-weight:500;margin-bottom:6px;color:#222">
          Flood risk level
        </div>
        ${Object.entries(RISK_COLORS)
          .filter(([k]) => k !== 'none')
          .map(([, v]) => `
            <div style="display:flex;align-items:center;gap:8px">
              <span style="
                display:inline-block;
                width:16px;height:16px;
                background:${v.fill};
                border:1px solid ${v.stroke};
                border-radius:3px;
                flex-shrink:0;
              "></span>
              <span style="color:#333">${v.label}</span>
            </div>
          `).join('')}
        <div style="margin-top:6px;color:#888;font-size:11px">
          Draw a polygon to score<br/>any area in real time
        </div>
      `
      return div
    }

    legend.addTo(map)
    ctrlRef.current = legend

    return () => legend.remove()
  }, [map])

  return null
}