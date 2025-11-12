import axios from 'axios'
import { useAuthStore } from '../store/auth'

// Configure API base URL via Vite env for production deployments (e.g., Netlify)
// Set VITE_API_BASE to your backend URL (e.g., https://your-backend.onrender.com/api/v1)
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api/v1'
})

api.interceptors.request.use(config => {
  const auth = useAuthStore()
  if (auth.token) {
    config.headers.Authorization = `Bearer ${auth.token}`
  }
  try {
    let did = localStorage.getItem('device_id')
    if (!did) {
      // RFC4122 v4-ish simple generator
      did = ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
        (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
      )
      localStorage.setItem('device_id', did)
    }
    config.headers['X-Device-Id'] = did
  } catch {}
  return config
})

// Auto-handle expired/invalid tokens
api.interceptors.response.use(
  res => res,
  err => {
    try {
      const status = err?.response?.status
      const cfg = err?.config || {}
      // Allow callers to handle themselves
      if ((status === 401 || status === 403) && !cfg.skipAuthRedirect) {
        const auth = useAuthStore()
        // Always clear any invalid token
        if (auth?.logout) auth.logout()

        // Only force redirect on protected pages; allow public pages to continue
        const path = window.location.pathname || '/'
        const protectedRoutes = [
          /^\/admin(\/|$)/,
          /^\/exam(\/|$)/,
          /^\/tryout(\/|$)/,
          /^\/zoom\/.+/,
        ]
        const isProtected = protectedRoutes.some(rx => rx.test(path))
        if (isProtected && !path.startsWith('/login')) {
          const next = encodeURIComponent(path + (window.location.search || ''))
          window.location.href = `/login?next=${next}`
        }
      }
    } catch {}
    return Promise.reject(err)
  }
)

export default api
