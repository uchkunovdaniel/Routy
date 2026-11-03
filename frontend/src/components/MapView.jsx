import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// Pass onAdd(lat, lng) to make the map clickable (used when publishing a route).
export default function MapView({ points, onAdd, height = 380 }) {
  const el = useRef(null)
  const map = useRef(null)
  const layer = useRef(null)
  const onAddRef = useRef(onAdd)
  onAddRef.current = onAdd

  useEffect(() => {
    const m = L.map(el.current, { scrollWheelZoom: false }).setView([42.7, 25.3], 7)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '&copy; OpenStreetMap', maxZoom: 18 }).addTo(m)
    layer.current = L.layerGroup().addTo(m)
    map.current = m
    m.on('click', (e) => onAddRef.current?.(+e.latlng.lat.toFixed(6), +e.latlng.lng.toFixed(6)))
    return () => m.remove()
  }, [])

  useEffect(() => {
    layer.current.clearLayers()
    const ll = points.map((p) => [p.lat, p.lng])
    if (ll.length > 1) L.polyline(ll, { color: '#D7263D', weight: 4, dashArray: '1 9', lineCap: 'round' }).addTo(layer.current)
    points.forEach((p, i) => {
      // Tooltip content is built with textContent – Leaflet would otherwise treat a string as HTML (XSS).
      const tip = document.createElement('span')
      tip.textContent = p.name || `Точка ${i + 1}`
      L.marker([p.lat, p.lng], { icon: L.divIcon({ className: 'pin', html: `<span>${i + 1}</span>`, iconSize: [26, 26] }) })
        .bindTooltip(tip).addTo(layer.current)
    })
    if (ll.length && !onAddRef.current) map.current.fitBounds(ll, { padding: [40, 40], maxZoom: 13 })
  }, [points])

  return <div ref={el} className="map" style={{ height }} />
}
