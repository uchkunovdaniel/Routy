// A tiny SVG drawing of the route built from its stored coordinates (no map tiles needed).
export default function RouteSketch({ points }) {
  const W = 320, H = 170, P = 26
  const lat0 = points.reduce((s, p) => s + p.lat, 0) / points.length
  const k = Math.cos((lat0 * Math.PI) / 180)
  const xs = points.map((p) => p.lng * k), ys = points.map((p) => -p.lat)
  const minX = Math.min(...xs), maxX = Math.max(...xs), minY = Math.min(...ys), maxY = Math.max(...ys)
  const scale = Math.min((W - 2 * P) / (maxX - minX || 1), (H - 2 * P) / (maxY - minY || 1))
  const ox = (W - (maxX - minX) * scale) / 2, oy = (H - (maxY - minY) * scale) / 2
  const pts = points.map((_, i) => [ox + (xs[i] - minX) * scale, oy + (ys[i] - minY) * scale])
  return (
    <svg className="sketch" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Схема на маршрута">
      {[0.25, 0.5, 0.75].map((f) => (
        <ellipse key={f} cx={W * 0.62} cy={H * 0.55} rx={W * f * 0.7} ry={H * f * 0.62} className="contour" />
      ))}
      <polyline points={pts.map((p) => p.join(',')).join(' ')} className="trail" />
      {pts.map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r={i === 0 || i === pts.length - 1 ? 6 : 3.5} className={i === 0 ? 'start' : i === pts.length - 1 ? 'end' : 'mid'} />
      ))}
    </svg>
  )
}
