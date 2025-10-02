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
  return config
})

export default api
