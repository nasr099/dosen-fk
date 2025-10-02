import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

import './style.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')

// Global loading animation for buttons
function markButtonLoading(btn){
  if (!btn || btn.classList.contains('is-loading')) return
  btn.classList.add('is-loading')
  // Fallback auto-clear after 1500ms
  setTimeout(() => btn.classList.remove('is-loading'), 1500)
}

document.addEventListener('click', (e) => {
  // Find closest .btn
  const btn = e.target && e.target.closest && e.target.closest('.btn')
  if (btn) markButtonLoading(btn)
})

// Clear loading state after route navigation completes
router.afterEach(() => {
  document.querySelectorAll('.btn.is-loading').forEach(el => el.classList.remove('is-loading'))
})
