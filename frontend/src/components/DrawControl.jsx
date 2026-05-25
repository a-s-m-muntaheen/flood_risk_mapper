import { useEffect, useRef } from 'react'
import { useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet-draw/dist/leaflet.draw.css'
import 'leaflet-draw'

export default function DrawControl({ onShapeDrawn, onShapeDeleted }) {
  const map      = useMap()
  const drawnRef = useRef(new L.FeatureGroup())

  useEffect(() => {
    const drawnItems = drawnRef.current
    map.addLayer(drawnItems)

    const drawControl = new L.Control.Draw({
      edit: {
        featureGroup: drawnItems,
        edit: {
            selectedPathOptions: {
            maintainColor: true,
            opacity: 0.3,
            }
        },
        remove: true,
        },
      draw: {
        polygon:   {
          allowIntersection: false,
          shapeOptions: {
            color:       '#185FA5',
            fillColor:   '#378ADD',
            fillOpacity: 0.2,
            weight:      2,
          },
        },
        rectangle:  {
          shapeOptions: {
            color:       '#185FA5',
            fillColor:   '#378ADD',
            fillOpacity: 0.2,
            weight:      2,
          },
        },
        circle:    false,
        polyline:  false,
        marker:    false,
        circlemarker: false,
      },
    })

    map.addControl(drawControl)

    map.on(L.Draw.Event.CREATED, (e) => {
      drawnItems.clearLayers()
      drawnItems.addLayer(e.layer)
      const geojson = e.layer.toGeoJSON().geometry
      onShapeDrawn && onShapeDrawn(geojson)
    })

    map.on(L.Draw.Event.DELETED, () => {
      onShapeDeleted && onShapeDeleted()
    })

    return () => {
      map.removeControl(drawControl)
      map.removeLayer(drawnItems)
    }
  }, [map, onShapeDrawn, onShapeDeleted])

  return null
}