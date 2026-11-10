import { Link } from 'react-router-dom'
import RouteSketch from './RouteSketch.jsx'
import { Stars } from './Stars.jsx'

export default function RouteCard({ route }) {
  const cover = route.photos?.[0]
  return (
    <Link to={`/routes/${route.id}`} className="card">
      <div className="card-media">
        {cover ? <img src={cover} alt="" /> : <RouteSketch points={route.waypoints} />}
      </div>
      <div className="card-body">
        <p className="muted">{route.destination}</p>
        <h3>{route.title}</h3>
        <div className="card-foot">
          {route.ratingCount ? (
            <><Stars value={route.rating} size={15} /><span className="muted">{route.rating.toFixed(1)} ({route.ratingCount})</span></>
          ) : <span className="muted">Още без оценки</span>}
          <span className="muted push">{route.waypoints.length} точки · {route.author}</span>
        </div>
      </div>
    </Link>
  )
}
