import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api } from '../lib/api.js'
import { useAuth } from '../lib/auth.jsx'
import { fileToDataUrl } from '../lib/image.js'
import MapView from '../components/MapView.jsx'

// Publish a new route (/routes/new) or edit an existing one (/routes/:id/edit).
export default function RouteForm() {
  const { id } = useParams()
  const editing = Boolean(id)
  const { user } = useAuth()
  const nav = useNavigate()
  const [f, setF] = useState({ title: '', destination: '', impressions: '', tips: '' })
  const [points, setPoints] = useState([])
  const [photos, setPhotos] = useState([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  // Edit mode: 'loading' | 'ready' | 'missing' | 'forbidden' | error message
  const [load, setLoad] = useState(editing ? 'loading' : 'ready')

  useEffect(() => {
    if (!editing) return
    let stale = false
    api.getRoute(id).then((r) => {
      if (stale) return
      if (!r) return setLoad('missing')
      if (r.authorId !== user.id) return setLoad('forbidden')
      setF({ title: r.title, destination: r.destination, impressions: r.impressions, tips: r.tips })
      setPoints(r.waypoints)
      setPhotos(r.photos)
      setLoad('ready')
    }).catch((err) => { if (!stale) setLoad(err.message) })
    return () => { stale = true }
  }, [editing, id, user.id])

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
      const data = { ...f, waypoints: points, photos }
      const r = editing ? await api.updateRoute(id, data) : await api.createRoute(data)
      nav(`/routes/${r.id}`)
    } catch (err) { setError(err.message); setBusy(false) }
  }

  if (load === 'loading') return <p className="empty">Зареждане…</p>
  if (load === 'missing') return <p className="empty">Маршрутът не е намерен. <Link to="/">Към маршрутите</Link></p>
  if (load === 'forbidden') return <p className="empty">Можете да променяте само собствените си маршрути. <Link to={`/routes/${id}`}>Към маршрута</Link></p>
  if (load !== 'ready') return <p className="error wrap" role="alert">{load}</p>

  return (
    <form className="wrap form" onSubmit={submit}>
      <h1>{editing ? 'Редактирай маршрут' : 'Публикувай маршрут'}</h1>
      <div className="row">
        <label>Заглавие<input value={f.title} onChange={set('title')} maxLength={120} required /></label>
        <label>Дестинация<input value={f.destination} onChange={set('destination')} maxLength={120} placeholder="напр. Пирин, България" required /></label>
      </div>

      <div>
        <h2>Маршрут на картата</h2>
        <p className="muted">Кликнете на картата, за да добавите точка. Редът на добавяне е редът на маршрута.</p>
        <MapView points={points} onAdd={addPoint} height={360} fitOnLoad={editing} />
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
      <div className="form-actions">
        <button className="btn btn-red" disabled={busy}>
          {editing ? (busy ? 'Запазване…' : 'Запази промените') : (busy ? 'Публикуване…' : 'Публикувай')}
        </button>
        {editing && <Link className="btn btn-ghost" to={`/routes/${id}`}>Отказ</Link>}
      </div>
    </form>
  )
}
