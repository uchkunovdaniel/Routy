import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/auth.jsx'

export default function AuthPage() {
  const { login, register } = useAuth()
  const nav = useNavigate()
  const from = useLocation().state?.from || '/'
  const [mode, setMode] = useState('login')
  const [f, setF] = useState({ name: '', email: '', password: '' })
  const [error, setError] = useState('')

  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })
  const submit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await (mode === 'login' ? login(f) : register(f))
      nav(from, { replace: true })
    } catch (err) { setError(err.message) }
  }

  return (
    <form className="auth" onSubmit={submit}>
      <div className="tabs" role="tablist">
        <button type="button" role="tab" aria-selected={mode === 'login'} onClick={() => setMode('login')}>Вход</button>
        <button type="button" role="tab" aria-selected={mode === 'register'} onClick={() => setMode('register')}>Нов акаунт</button>
      </div>
      {mode === 'register' && <label>Име<input value={f.name} onChange={set('name')} autoComplete="name" required /></label>}
      <label>Имейл<input type="email" value={f.email} onChange={set('email')} autoComplete="email" required /></label>
      <label>Парола<input type="password" value={f.password} onChange={set('password')} autoComplete={mode === 'login' ? 'current-password' : 'new-password'} minLength={6} required /></label>
      {error && <p className="error" role="alert">{error}</p>}
      <button className="btn btn-dark">{mode === 'login' ? 'Вход' : 'Създай акаунт'}</button>
    </form>
  )
}
