import { Routes, Route, Link, NavLink, Navigate, useLocation, useParams } from 'react-router-dom'
import { useAuth } from './lib/auth.jsx'
import Home from './pages/Home.jsx'
import RouteDetail from './pages/RouteDetail.jsx'
import RouteForm from './pages/RouteForm.jsx'
import AuthPage from './pages/AuthPage.jsx'
import Profile from './pages/Profile.jsx'

function RequireAuth({ children }) {
    const { user } = useAuth()
    const loc = useLocation()
    return user ? children : <Navigate to="/auth" state={{ from: loc.pathname }} replace />
}

// Key the form by route so switching new <-> edit (or between routes) starts with fresh state.
function EditRoute() {
    const { id } = useParams()
    return <RouteForm key={id} />
}

function Header() {
    const { user, logout } = useAuth()
    return (
        <header className="site-header">
            <Link to="/" className="brand" aria-label="Пътеки – начало">
                <span className="blaze" aria-hidden="true" />
                Routy
            </Link>
            <nav>
                <NavLink to="/" end>Маршрути</NavLink>
                {user && <NavLink to="/profile">Моите пътувания</NavLink>}
                {user ? (
                    <>
                        <NavLink to="/routes/new" className="btn btn-red">Публикувай</NavLink>
                        <button className="link-btn" onClick={logout}>Изход ({user.name})</button>
                    </>
                ) : (
                    <NavLink to="/auth" className="btn btn-dark">Вход</NavLink>
                )}
            </nav>
        </header>
    )
}

export default function App() {
    return (
        <>
            <Header />
            <main>
                <Routes>
                    <Route path="/" element={<Home />} />
                    <Route path="/routes/new" element={<RequireAuth><RouteForm key="new" /></RequireAuth>} />
                    <Route path="/routes/:id/edit" element={<RequireAuth><EditRoute /></RequireAuth>} />
                    <Route path="/routes/:id" element={<RouteDetail />} />
                    <Route path="/auth" element={<AuthPage />} />
                    <Route path="/profile" element={<RequireAuth><Profile /></RequireAuth>} />
                    <Route path="*" element={<p className="empty">Страницата не е намерена. <Link to="/">Към маршрутите</Link></p>} />
                </Routes>
            </main>
            <footer className="site-footer">Пътеки · маршрути от хора, които са ги извървели</footer>
        </>
    )
}
