<template>
  <div class="auth-wrap">
    <img class="illus left" :src="leftImg" alt="left" />
    <div class="panel card">
      <div class="brand">
        <img :src="logoImg" alt="logo" class="logo" />
        <h2>Login</h2>
      </div>
      <form @submit.prevent="submit" class="form">
        <label>Email</label>
        <input v-model="email" type="email" class="input" required />
        <label>Password</label>
        <input v-model="password" type="password" class="input" required />
        <label class="remember"><input type="checkbox" v-model="remember" /> Remember me</label>
        <button class="btn primary full">Login</button>
        <a class="link" href="#">Lupa password?</a>
      </form>
      <div class="or">or</div>
      <button class="btn google full" @click="googleSignIn">
        <img class="gicon" src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" />
        Continue with Google
      </button>
    </div>
    <img class="illus right" :src="rightImg" alt="right" />

    <!-- Inactive user modal -->
    <div v-if="showInactive" class="modal">
      <div class="modal-card">
        <div class="modal-title">Akun belum aktif</div>
        <div class="modal-body">
          Akun Anda belum diaktifkan. Silakan hubungi admin via WhatsApp untuk aktivasi akun Anda.
          <div class="contact"><a :href="waHref" target="_blank" rel="noopener" class="wa-btn">WhatsApp Admin</a></div>
        </div>
        <div class="modal-actions">
          <button class="btn" @click="showInactive=false">Tutup</button>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '../api/client'
import { useAuthStore } from '../store/auth'
import router from '../router'
import { buildWaLink } from '../config/whatsapp'

const email = ref('')
const password = ref('')
const remember = ref(false)
const auth = useAuthStore()
const logoImg = ref('/logo.svg')
const leftImg = ref('/med-left.svg')
const rightImg = ref('/med-right.svg')
const showInactive = ref(false)
const waHref = computed(() => buildWaLink(`Hai Admin, saya ${email.value || '-'} ingin melakukan aktivasi/upgrade akun.`))

const submit = async () => {
  try {
    const params = new URLSearchParams()
    params.append('username', email.value)
    params.append('password', password.value)
    const { data } = await api.post('/auth/login', params)
    // fetch me (this will fail with 400 if user inactive)
    const me = await api.get('/users/me', { headers: { Authorization: `Bearer ${data.access_token}` }})
    auth.setAuth(data.access_token, me.data)
    router.push('/')
  } catch (e) {
    const msg = e?.response?.data?.detail || ''
    if (e?.response?.status === 400 && String(msg).toLowerCase().includes('inactive')){
      showInactive.value = true
    } else {
      alert('Login gagal. Periksa email/password dan coba lagi.')
      // Optional: console for debugging
      console.error(e)
    }
  }
}

// Google Identity Services
const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID
onMounted(() => {
  // load branding from localStorage if available (always run)
  const l = localStorage.getItem('branding_logo'); if (l) logoImg.value = l
  const il = localStorage.getItem('branding_auth_left'); if (il) leftImg.value = il
  const ir = localStorage.getItem('branding_auth_right'); if (ir) rightImg.value = ir

  // load Google script only when configured
  if (GOOGLE_CLIENT_ID){
    if (!document.getElementById('google-plat')){
      const s = document.createElement('script')
      s.src = 'https://accounts.google.com/gsi/client'
      s.async = true
      s.defer = true
      s.id = 'google-plat'
      document.head.appendChild(s)
    }
  }
})

async function googleSignIn(){
  if (!GOOGLE_CLIENT_ID){
    alert('Google Sign-In not configured. Set VITE_GOOGLE_CLIENT_ID in .env')
    return
  }
  // Use the popup approach
  // eslint-disable-next-line no-undef
  google.accounts.id.initialize({
    client_id: GOOGLE_CLIENT_ID,
    callback: async (resp) => {
      try {
        const { data } = await api.post('/auth/google', { id_token: resp.credential })
        const me = await api.get('/users/me', { headers: { Authorization: `Bearer ${data.access_token}` }})
        auth.setAuth(data.access_token, me.data)
        router.push('/')
      } catch (e) {
        alert('Google login failed. Please try again.')
        console.error(e)
      }
    }
  })
  // eslint-disable-next-line no-undef
  google.accounts.id.prompt() // opens One Tap / prompt
}
</script>

<style scoped>
.auth-wrap{ position:relative; display:flex; align-items:center; justify-content:center; min-height: calc(100vh - 140px); }
.panel{ width: 100%; max-width: 460px; position:relative; z-index:2; }
.brand{ display:flex; flex-direction:column; align-items:center; gap:8px; margin-bottom:8px; }
.logo{ height:44px; }
.form{ display:flex; flex-direction:column; gap:8px; }
.remember{ display:flex; align-items:center; gap:8px; font-size:14px; color:#334155; }
.or{ text-align:center; color:#64748b; margin:10px 0; font-weight:600; }
.btn.full{ width:100%; }
.btn.google{ background:white; color:#1f2937; border:1px solid #e5e7eb; display:flex; align-items:center; justify-content:center; gap:8px; }
.btn.google .gicon{ height:18px; }
.illus{ position:absolute; bottom:0; opacity:.9; max-width: 300px; }
.illus.left{ left: 20px; }
.illus.right{ right: 20px; }
@media (max-width: 900px){ .illus{ display:none; } }
@media (max-width: 480px){
  .auth-wrap{ padding: 0 12px; }
}

/* modal */
.modal{ position:fixed; inset:0; background:rgba(2,6,23,0.5); display:flex; align-items:center; justify-content:center; z-index: 1000; }
.modal-card{ width: min(92vw, 520px); background:#fff; border-radius:16px; border:1px solid #e2e8f0; box-shadow: 0 20px 60px rgba(2,6,23,.25), 0 2px 12px rgba(2,6,23,.12); padding:16px; animation: pop .18s ease-out; }
.modal-title{ font-weight:800; color:#0f172a; margin-bottom:6px; }
.modal-body{ color:#475569; line-height:1.6; }
.modal-body .contact{ margin-top:8px; color:#334155; font-weight:600; }
.modal-actions{ display:flex; justify-content:flex-end; gap:8px; margin-top:14px; }
@keyframes pop{ from{ transform: scale(.96); opacity:0 } to{ transform: scale(1); opacity:1 } }
</style>
