import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api.js'
import { useAuth } from '../lib/auth.jsx'
import RouteCard from '../components/RouteCard.jsx'

export default function Profile() {
  const { user } = useAuth()
  const [mine, setMine] = useState(null)
  const [error, setError] = useState('')
  useEffect(() => {
    api.listRoutes({ author: user.id }).then(setMine).catch((err) => { setMine([]); setError(err.message) })
  }, [user.id])

  return (
    <section className="wrap">
      <h1>Моите пътувания</h1>
      {error ? <p className="error" role="alert">{error}</p>
        : mine === null ? <p className="empty">Зареждане…</p>
        : mine.length === 0 ? <p className="empty">Още нямате публикации. <Link to="/routes/new">Споделете първия си маршрут</Link></p>
        : <div className="grid">{mine.map((r) => <RouteCard key={r.id} route={r} />)}</div>}
    </section>
  )
}
