import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api.js'
import RouteCard from '../components/RouteCard.jsx'
import { useAuth } from '../lib/auth.jsx'

export default function Home() {
  const { user } = useAuth()
  const [q, setQ] = useState('')
  const [sort, setSort] = useState('new')
  const [routes, setRoutes] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let stale = false // ignore responses that arrive after a newer search
    api.listRoutes({ q, sort })
      .then((list) => { if (!stale) { setRoutes(list); setError('') } })
      .catch((err) => { if (!stale) { setRoutes([]); setError(err.message) } })
    return () => { stale = true }
  }, [q, sort])

  return (
    <>
      <section className="hero">
        <div className="hero-text">
          <h1>Маршрути, които някой вече е извървял за вас</h1>
          <p>Разгледайте пътувания на други туристи, вижте ги на картата и споделете своите.</p>
          <div className="hero-actions">
            <Link className="btn btn-red" to={user ? '/routes/new' : '/auth'}>Публикувай маршрут</Link>
            <a className="btn btn-ghost" href="#routes">Разгледай</a>
          </div>
        </div>
        <div className="blaze-art" aria-hidden="true"><i /><i /><i /></div>
      </section>

      <section id="routes" className="wrap">
        <div className="toolbar">
          <input type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Търсене по дестинация или заглавие" aria-label="Търсене" />
          <select value={sort} onChange={(e) => setSort(e.target.value)} aria-label="Подредба">
            <option value="new">Най-нови</option>
            <option value="top">Най-високо оценени</option>
          </select>
        </div>
        {error ? <p className="error" role="alert">{error}</p>
          : routes === null ? <p className="empty">Зареждане…</p>
          : routes.length === 0 ? <p className="empty">Няма маршрути за „{q}“. Опитайте с друга дестинация или публикувайте първия.</p>
          : <div className="grid">{routes.map((r) => <RouteCard key={r.id} route={r} />)}</div>}
      </section>
    </>
  )
}
