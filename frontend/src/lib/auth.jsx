import { createContext, useContext, useState } from 'react'
import { api } from './api.js'

const Ctx = createContext(null)
export const useAuth = () => useContext(Ctx)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('tg_session')) } catch { return null }
  })
  const start = (u) => { localStorage.setItem('tg_session', JSON.stringify(u)); setUser(u); return u }
  const value = {
    user,
    login: async (f) => start(await api.login(f)),
    register: async (f) => start(await api.register(f)),
    logout: () => { localStorage.removeItem('tg_session'); setUser(null) },
  }
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}
