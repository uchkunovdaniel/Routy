import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api } from '../lib/api.js'
import { useAuth } from '../lib/auth.jsx'
import MapView from '../components/MapView.jsx'
import { Stars, StarInput } from '../components/Stars.jsx'

export default function RouteDetail() {
  const { id } = useParams()
  const { user } = useAuth()
  const nav = useNavigate()
  const [route, setRoute] = useState(undefined)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState('')
  const [rating, setRating] = useState(0)
  const [text, setText] = useState('')
  const [error, setError] = useState('')
  const [loadError, setLoadError] = useState('')

  useEffect(() => {
    setRoute(undefined); setLoadError('')
    api.getRoute(id).then(setRoute).catch((err) => setLoadError(err.message))
  }, [id])

  if (loadError) return <p className="error wrap" role="alert">{loadError}</p>
  if (route === undefined) return <p className="empty">Зареждане…</p>
  if (route === null) return <p className="empty">Маршрутът не е намерен. <Link to="/">Към маршрутите</Link></p>

  const isOwner = user?.id === route.authorId

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    if (!rating) return setError('Изберете оценка от 1 до 5 звезди.')
    try {
      setRoute(await api.addReview(id, { rating, text }))
      setText(''); setRating(0)
    } catch (err) { setError(err.message) }
  }

  const remove = async () => {
    setDeleteError(''); setDeleting(true)
    try {
      await api.deleteRoute(id)
      nav('/profile', { replace: true })
    } catch (err) { setDeleteError(err.message); setDeleting(false) }
  }

  return (
    <article className="wrap detail">
      <p className="muted">{route.destination} · от {route.author} · {route.createdAt}</p>
      <h1>{route.title}</h1>
      <div className="rating-line">
        {route.ratingCount ? <><Stars value={route.rating} /><strong>{route.rating.toFixed(1)}</strong><span className="muted">({route.ratingCount} отзива)</span></> : <span className="muted">Още без оценки</span>}
      </div>

      {isOwner && (
        <div className="owner-actions">
          {confirmDelete ? (
            <>
              <span>Да изтрия ли маршрута заедно с отзивите му? Това е необратимо.</span>
              <button type="button" className="btn btn-red" onClick={remove} disabled={deleting}>{deleting ? 'Изтриване…' : 'Да, изтрий'}</button>
              <button type="button" className="btn btn-ghost" onClick={() => setConfirmDelete(false)} disabled={deleting}>Отказ</button>
            </>
          ) : (
            <>
              <Link className="btn btn-dark" to={`/routes/${id}/edit`}>Редактирай</Link>
              <button type="button" className="btn btn-ghost" onClick={() => setConfirmDelete(true)}>Изтрий</button>
            </>
          )}
          {deleteError && <p className="error" role="alert">{deleteError}</p>}
        </div>
      )}

      <MapView points={route.waypoints} />

      <div className="cols">
        <section>
          <h2>Лични впечатления</h2>
          <p className="prose">{route.impressions || '—'}</p>
          <h2>Съвети за пътуването</h2>
          <p className="prose">{route.tips || '—'}</p>
        </section>
        <aside>
          <h2>Точки от маршрута</h2>
          <ol className="stops">
            {route.waypoints.map((p, i) => (
              <li key={i}><b>{p.name}</b><span className="muted">{p.lat.toFixed(4)}, {p.lng.toFixed(4)}</span></li>
            ))}
          </ol>
        </aside>
      </div>

      {route.photos.length > 0 && (
        <section><h2>Снимки</h2>
          <div className="gallery">{route.photos.map((src, i) => <img key={i} src={src} alt={`Снимка ${i + 1} от маршрута`} loading="lazy" />)}</div>
        </section>
      )}

      <section>
        <h2>Отзиви</h2>
        {user && !isOwner ? (
          <form className="review-form" onSubmit={submit}>
            <StarInput value={rating} onChange={setRating} />
            <label>Отзив
              <textarea value={text} onChange={(e) => setText(e.target.value)} rows={3} maxLength={1000} placeholder="Как мина маршрутът за вас?" />
            </label>
            {error && <p className="error" role="alert">{error}</p>}
            <button className="btn btn-dark">Публикувай отзива</button>
          </form>
        ) : !user ? (
          <p className="muted"><Link to="/auth" state={{ from: `/routes/${id}` }}>Влезте</Link>, за да оставите отзив.</p>
        ) : null}

        {route.reviews.length === 0 ? <p className="empty small">Още няма отзиви. Бъдете първият, който е минал оттук.</p> : (
          <ul className="reviews">
            {route.reviews.map((v) => (
              <li key={v.id}>
                <div className="rev-head"><b>{v.userName}</b><Stars value={v.rating} size={14} /><span className="muted">{v.createdAt}</span></div>
                <p className="prose">{v.text}</p>
              </li>
            ))}
          </ul>
        )}
      </section>
    </article>
  )
}
