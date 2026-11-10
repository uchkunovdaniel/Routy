import { createContext, useContext, useEffect, useState } from 'react'
import { api, session } from './api.js'

const Ctx = createContext(null)
export const useAuth = () => useContext(Ctx)

const USER_KEY = 'tg_session'

const readUser = () => {
  // A cached user without a token (e.g. left over from the old localStorage mock) is not a session.
  if (!session.getToken()) return null
  try { return JSON.parse(localStorage.getItem(USER_KEY)) } catch { return null }
}

const saveUser = (u) => {
  try { u ? localStorage.setItem(USER_KEY, JSON.stringify(u)) : localStorage.removeItem(USER_KEY) } catch { /* ignore */ }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(readUser)

  const end = () => { session.setToken(null); saveUser(null); setUser(null) }
  const start = ({ user: u, token }) => { session.setToken(token); saveUser(u); setUser(u); return u }

  useEffect(() => {
    session.onUnauthorized(end)
    // Re-validate a stored token on load; an expired one logs the user out.
    if (session.getToken()) {
      api.me().then((u) => { saveUser(u); setUser(u) }).catch((err) => { if (err.status === 401) end() })
    }
    return () => session.onUnauthorized(() => {})
  }, [])

  const value = {
    user,
    login: async (f) => start(await api.login(f)),
    register: async (f) => start(await api.register(f)),
    logout: end,
  }
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}
