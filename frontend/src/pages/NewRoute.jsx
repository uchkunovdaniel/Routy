import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api.js'
import { fileToDataUrl } from '../lib/image.js'
import MapView from '../components/MapView.jsx'

export default function NewRoute() {
  const nav = useNavigate()
  const [f, setF] = useState({ title: '', destination: '', impressions: '', tips: '' })
  const [points, setPoints] = useState([])
  const [photos, setPhotos] = useState([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })
  const addPoint = (lat, lng) => setPoints((p) => [...p, { name: '', lat, lng }])
  const rename = (i, name) => setPoints((p) => p.map((x, j) => (j === i ? { ...x, name } : x)))
  const remove = (i) => setPoints((p) => p.filter((_, j) => j !== i))

  const onPhotos = async (e) => {
    setError('')
    try {
      const urls = await Promise.all([...e.target.files].slice(0, 6 - photos.length).map((file) => fileToDataUrl(file)))
      setPhotos((p) => [...p, ...urls].slice(0, 6))
    } catch (err) { setError(err.message) }
    e.target.value = ''
  }

  const submit = async (e) => {
    e.preventDefault()
    setError(''); setBusy(true)
    try {
      const r = await api.createRoute({ ...f, waypoints: points, photos })
      nav(`/routes/${r.id}`)
    } catch (err) { setError(err.message); setBusy(false) }
  }

  return (
    <form className="wrap form" onSubmit={submit}>
      <h1>Публикувай маршрут</h1>
      <div className="row">
        <label>Заглавие<input value={f.title} onChange={set('title')} maxLength={120} required /></label>
        <label>Дестинация<input value={f.destination} onChange={set('destination')} maxLength={120} placeholder="напр. Пирин, България" required /></label>
      </div>

      <div>
        <h2>Маршрут на картата</h2>
        <p className="muted">Кликнете на картата, за да добавите точка. Редът на добавяне е редът на маршрута.</p>
        <MapView points={points} onAdd={addPoint} height={360} />
        {points.length > 0 && (
          <ol className="point-list">
            {points.map((p, i) => (
              <li key={i}>
                <input aria-label={`Име на точка ${i + 1}`} value={p.name} onChange={(e) => rename(i, e.target.value)} placeholder={`Точка ${i + 1}`} maxLength={80} />
                <span className="muted">{p.lat}, {p.lng}</span>
                <button type="button" className="link-btn" onClick={() => remove(i)}>Премахни</button>
              </li>
            ))}
          </ol>
        )}
      </div>

      <label>Лични впечатления<textarea rows={4} value={f.impressions} onChange={set('impressions')} maxLength={4000} /></label>
      <label>Съвети за пътуването<textarea rows={3} value={f.tips} onChange={set('tips')} maxLength={2000} /></label>

      <div>
        <label>Снимки (до 6)<input type="file" accept="image/jpeg,image/png,image/webp" multiple onChange={onPhotos} disabled={photos.length >= 6} /></label>
        {photos.length > 0 && (
          <div className="gallery small">
            {photos.map((src, i) => (
              <figure key={i}><img src={src} alt={`Снимка ${i + 1}`} />
                <button type="button" className="link-btn" onClick={() => setPhotos(photos.filter((_, j) => j !== i))}>Премахни</button>
              </figure>
            ))}
          </div>
        )}
      </div>

      {error && <p className="error" role="alert">{error}</p>}
      <button className="btn btn-red" disabled={busy}>{busy ? 'Публикуване…' : 'Публикувай'}</button>
    </form>
  )
}
