// Mock data layer on top of localStorage. Every function is async and returns plain data,
// so you can replace the bodies with fetch() calls to your real API without touching the UI.
import { clean, safeImage, validCoords } from './sanitize.js'

const KEY = 'tg_db_v1'
const uid = () => Math.random().toString(36).slice(2, 10)

const seed = () => ({
  users: [
    { id: 'u1', name: 'Мария', email: 'maria@example.com', password: 'demo1234' },
    { id: 'u2', name: 'Георги', email: 'georgi@example.com', password: 'demo1234' },
  ],
  routes: [
    {
      id: 'r1', authorId: 'u1', title: 'Седемте рилски езера за един ден',
      destination: 'Рила, България', createdAt: '2026-08-14',
      impressions: 'Най-красивата гледка е от върха над Окото. Тръгнахме рано и бяхме сами до Бъбрека.',
      tips: 'Вземете връхна дреха – духа дори през август. Лифтът затваря в 17:00.',
      waypoints: [
        { name: 'Хижа Рилски езера', lat: 42.2086, lng: 23.3222 },
        { name: 'Окото', lat: 42.2033, lng: 23.3189 },
        { name: 'Бъбрека', lat: 42.2008, lng: 23.3156 },
        { name: 'Езерен връх', lat: 42.1969, lng: 23.3111 },
      ],
      photos: [],
      reviews: [
        { id: 'v1', userId: 'u2', userName: 'Георги', rating: 5, text: 'Точно както е описано. Благодаря за съветите!', createdAt: '2026-09-02' },
      ],
    },
    {
      id: 'r2', authorId: 'u2', title: 'Черни връх по билото от Алеко',
      destination: 'Витоша, България', createdAt: '2026-07-03',
      impressions: 'Лесен маршрут с широк изглед към София. Мъглата се спуска бързо след обяд.',
      tips: 'Тръгвайте преди 9 ч. и проверете прогнозата за гръмотевици.',
      waypoints: [
        { name: 'Алеко', lat: 42.5631, lng: 23.2897 },
        { name: 'Резньовете', lat: 42.5547, lng: 23.2736 },
        { name: 'Черни връх', lat: 42.5617, lng: 23.2744 },
      ],
      photos: [],
      reviews: [
        { id: 'v2', userId: 'u1', userName: 'Мария', rating: 4, text: 'Хубав маршрут, но има много хора в събота.', createdAt: '2026-07-20' },
      ],
    },
    {
      id: 'r3', authorId: 'u1', title: 'Родопска приказка: Триград и Дяволското гърло',
      destination: 'Родопи, България', createdAt: '2026-06-21',
      impressions: 'Пещерата е впечатляваща, а ждрелото – прохладно убежище в жегата.',
      tips: 'Обувки с добро сцепление – пътеката е мокра. Опитайте пъстърва в Триград.',
      waypoints: [
        { name: 'Триград', lat: 41.6075, lng: 24.3731 },
        { name: 'Ждрелото', lat: 41.6139, lng: 24.3631 },
        { name: 'Дяволско гърло', lat: 41.6153, lng: 24.3589 },
      ],
      photos: [],
      reviews: [],
    },
  ],
})

const load = () => {
  try {
    const raw = localStorage.getItem(KEY)
    if (raw) return JSON.parse(raw)
  } catch { /* fall through to seed */ }
  const db = seed()
  localStorage.setItem(KEY, JSON.stringify(db))
  return db
}
const save = (db) => localStorage.setItem(KEY, JSON.stringify(db))
const wait = (v) => new Promise((r) => setTimeout(() => r(v), 120))

const decorate = (db, r) => {
  const n = r.reviews.length
  return {
    ...r,
    author: db.users.find((u) => u.id === r.authorId)?.name ?? 'Непознат',
    ratingCount: n,
    rating: n ? r.reviews.reduce((s, x) => s + x.rating, 0) / n : 0,
  }
}

export const api = {
  async listRoutes({ q = '', sort = 'new' } = {}) {
    const db = load()
    const term = q.trim().toLowerCase()
    let list = db.routes.map((r) => decorate(db, r))
    if (term) list = list.filter((r) => `${r.title} ${r.destination}`.toLowerCase().includes(term))
    list.sort(sort === 'top' ? (a, b) => b.rating - a.rating || b.ratingCount - a.ratingCount : (a, b) => b.createdAt.localeCompare(a.createdAt))
    return wait(list)
  },
  async getRoute(id) {
    const db = load()
    const r = db.routes.find((x) => x.id === id)
    return wait(r ? decorate(db, r) : null)
  },
  async createRoute(data, user) {
    const db = load()
    const waypoints = (data.waypoints || [])
      .filter((p) => validCoords(p.lat, p.lng))
      .map((p, i) => ({ name: clean(p.name, 80) || `Точка ${i + 1}`, lat: p.lat, lng: p.lng }))
    if (waypoints.length < 2) throw new Error('Добавете поне две точки от маршрута на картата.')
    const title = clean(data.title, 120)
    const destination = clean(data.destination, 120)
    if (!title || !destination) throw new Error('Заглавието и дестинацията са задължителни.')
    const route = {
      id: uid(), authorId: user.id, title, destination, waypoints,
      impressions: clean(data.impressions, 4000), tips: clean(data.tips, 2000),
      photos: (data.photos || []).map(safeImage).filter(Boolean).slice(0, 6),
      createdAt: new Date().toISOString().slice(0, 10), reviews: [],
    }
    db.routes.unshift(route)
    save(db)
    return wait(route)
  },
  async addReview(routeId, { rating, text }, user) {
    const db = load()
    const r = db.routes.find((x) => x.id === routeId)
    if (!r) throw new Error('Маршрутът не съществува.')
    if (r.authorId === user.id) throw new Error('Не можете да оценявате собствен маршрут.')
    const body = clean(text, 1000)
    if (!body) throw new Error('Напишете няколко думи в отзива.')
    const stars = Math.min(5, Math.max(1, Math.round(Number(rating))))
    r.reviews = r.reviews.filter((v) => v.userId !== user.id) // one review per user, newest wins
    r.reviews.unshift({ id: uid(), userId: user.id, userName: user.name, rating: stars, text: body, createdAt: new Date().toISOString().slice(0, 10) })
    save(db)
    return wait(decorate(db, r))
  },
  async register({ name, email, password }) {
    const db = load()
    const n = clean(name, 40), e = clean(email, 120).toLowerCase()
    if (!n || !/^\S+@\S+\.\S+$/.test(e) || password.length < 6) throw new Error('Попълнете име, валиден имейл и парола от поне 6 символа.')
    if (db.users.some((u) => u.email === e)) throw new Error('Вече има акаунт с този имейл.')
    // DEMO ONLY: a real backend must hash passwords (argon2/bcrypt).
    const user = { id: uid(), name: n, email: e, password }
    db.users.push(user)
    save(db)
    return wait({ id: user.id, name: user.name, email: user.email })
  },
  async login({ email, password }) {
    const db = load()
    const u = db.users.find((x) => x.email === clean(email, 120).toLowerCase() && x.password === password)
    if (!u) throw new Error('Грешен имейл или парола.')
    return wait({ id: u.id, name: u.name, email: u.email })
  },
}
