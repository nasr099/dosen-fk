<template>
  <header class="site-header">
    <div class="container-fluid navbar">
      <router-link to="/" class="brand-link">
        <img :src="logoSrc" alt="logo" class="brand-logo" />
        <span class="brand-text">MedExam</span>
      </router-link>

      <nav class="links">
        <router-link to="/">Home</router-link>
        <router-link to="/categories">Categories</router-link>
        <router-link to="/tryouts">Tryouts</router-link>
        <router-link to="/zoom">Zoom Discussion</router-link>
        <router-link to="/blog">Blog</router-link>
        <div class="dropdown" ref="supportMenuRef">
          <a href="#" class="drop-toggle" @click.prevent="toggleSupportMenu" :aria-expanded="showSupportMenu">Support ▾</a>
          <div class="menu" v-show="showSupportMenu">
            <router-link to="/#faq">FAQ</router-link>
            <router-link to="/team">Team</router-link>
          </div>
        </div>
        <div v-if="auth.isAdmin || auth.isTeacher" class="dropdown" ref="adminMenuRef">
          <a href="#" class="drop-toggle" @click.prevent="toggleAdminMenu" :aria-expanded="showAdminMenu">Admin ▾</a>
          <div class="menu" v-show="showAdminMenu">
            <template v-if="auth.isAdmin">
              <router-link to="/admin/branding">Branding</router-link>
              <router-link to="/admin/users">Users</router-link>
              <router-link to="/admin/categories">Categories</router-link>
              <router-link to="/admin/readings">Readings</router-link>
              <router-link to="/admin/questions">Questions</router-link>
              <router-link to="/admin/tryouts">Tryouts</router-link>
              <router-link to="/admin/essays">Essays Grading</router-link>
              <router-link to="/admin/analytics">Analytics</router-link>
              <router-link to="/admin/llm">Questions Generator</router-link>
              <router-link to="/admin/llm-scan">Question Scanner</router-link>
              <router-link to="/admin/promos">Promos</router-link>
              <router-link to="/admin/zoom">Zoom Discussions</router-link>
              <router-link to="/admin/team">Team</router-link>
              <router-link to="/admin/blog">Blog</router-link>
            </template>
            <template v-else>
              <router-link to="/admin/categories">Categories</router-link>
              <router-link to="/admin/readings">Readings</router-link>
              <router-link to="/admin/questions">Questions</router-link>
              <router-link to="/admin/tryouts">Tryouts</router-link>
              <router-link to="/admin/llm">Questions Generator</router-link>
              <router-link to="/admin/llm-scan">Question Scanner</router-link>
              <router-link to="/admin/essays">Essays Grading</router-link>
              <router-link to="/admin/zoom">Zoom Discussions</router-link>
              <router-link to="/admin/blog">Blog</router-link>
            </template>
          </div>
        </div>
      </nav>

      <button class="hamb" @click="showMobile = !showMobile" aria-label="Toggle menu">☰</button>

      <div class="actions">
        <router-link v-if="!auth.isAuthenticated" to="/login" class="link-login">Log in</router-link>
        <router-link v-if="!auth.isAuthenticated" to="/register"><button class="btn cta">Get Started</button></router-link>
        <router-link v-if="resumeSessionId" :to="`/tryout/run/${resumeSessionId}`"><button class="btn resume">Resume Tryout</button></router-link>
        <router-link v-if="auth.isAuthenticated" to="/profile">Profile</router-link>
        <button v-if="auth.isAuthenticated" class="btn secondary" @click="logout">Logout</button>
      </div>

      <div v-if="showMobile" class="mobile-menu">
        <router-link to="/" @click="closeMobile">Home</router-link>
        <router-link to="/categories" @click="closeMobile">Categories</router-link>
        <router-link to="/tryouts" @click="closeMobile">Tryouts</router-link>
        <router-link to="/zoom" @click="closeMobile">Zoom Discussion</router-link>
        <router-link to="/blog" @click="closeMobile">Blog</router-link>
        <router-link to="/#faq" @click="closeMobile">FAQ</router-link>
        <router-link to="/team" @click="closeMobile">Team</router-link>
        <div v-if="auth.isAdmin || auth.isTeacher" class="mobile-admin-links">
            <hr>
            <template v-if="auth.isAdmin">
              <router-link to="/admin/branding" @click="closeMobile">Branding</router-link>
              <router-link to="/admin/users" @click="closeMobile">Users</router-link>
              <router-link to="/admin/categories" @click="closeMobile">Categories</router-link>
              <router-link to="/admin/readings" @click="closeMobile">Readings</router-link>
              <router-link to="/admin/questions" @click="closeMobile">Questions</router-link>
              <router-link to="/admin/tryouts" @click="closeMobile">Tryouts</router-link>
              <router-link to="/admin/essays" @click="closeMobile">Essays Grading</router-link>
              <router-link to="/admin/analytics" @click="closeMobile">Analytics</router-link>
              <router-link to="/admin/llm" @click="closeMobile">Questions Generator</router-link>
              <router-link to="/admin/llm-scan" @click="closeMobile">Question Scanner</router-link>
              <router-link to="/admin/promos" @click="closeMobile">Promos</router-link>
              <router-link to="/admin/zoom" @click="closeMobile">Zoom Discussions</router-link>
              <router-link to="/admin/team" @click="closeMobile">Team</router-link>
              <router-link to="/admin/blog" @click="closeMobile">Blog</router-link>
            </template>
            <template v-else>
              <router-link to="/admin/categories" @click="closeMobile">Categories</router-link>
              <router-link to="/admin/readings" @click="closeMobile">Readings</router-link>
              <router-link to="/admin/questions" @click="closeMobile">Questions</router-link>
              <router-link to="/admin/tryouts" @click="closeMobile">Tryouts</router-link>
              <router-link to="/admin/llm" @click="closeMobile">Questions Generator</router-link>
              <router-link to="/admin/llm-scan" @click="closeMobile">Question Scanner</router-link>
              <router-link to="/admin/essays" @click="closeMobile">Essays Grading</router-link>
              <router-link to="/admin/zoom" @click="closeMobile">Zoom Discussions</router-link>
              <router-link to="/admin/blog" @click="closeMobile">Blog</router-link>
            </template>
            </div>
        <router-link v-if="!auth.isAuthenticated" to="/login" @click="closeMobile">Log in</router-link>
        <router-link v-if="!auth.isAuthenticated" to="/register" @click="closeMobile">Get Started</router-link>
      </div>
    </div>
  </header>
</template>

<script setup>
import { useAuthStore } from '../store/auth'
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useClickOutside } from '../composables/useClickOutside'
import api from '../api/client'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const logoSrc = ref('/logo.svg')
const showMobile = ref(false)
const showSupportMenu = ref(false)
const showAdminMenu = ref(false)
const resumeSessionId = ref(null)

const supportMenuRef = ref(null)
const adminMenuRef = ref(null)

function closeAllMenus(){
  showSupportMenu.value = false
  showAdminMenu.value = false
}
function logout(){
  try { localStorage.removeItem('active_tryout_session') } catch {}
  auth.logout(); router.push('/')
}
function closeMobile(){ showMobile.value = false }
function handleLogoutMobile(){ logout(); closeMobile() }
function toggleSupportMenu(){ if(!showSupportMenu.value) closeAllMenus(); showSupportMenu.value = !showSupportMenu.value }
function toggleAdminMenu(){ if(!showAdminMenu.value) closeAllMenus(); showAdminMenu.value = !showAdminMenu.value }

watch(() => route.path, () => { closeAllMenus(); closeMobile() })
useClickOutside(supportMenuRef, () => showSupportMenu.value = false)
useClickOutside(adminMenuRef, () => showAdminMenu.value = false)

async function detectResume(){
  resumeSessionId.value = null
  // Priority 1: localStorage key
  try{
    const cached = Number(localStorage.getItem('active_tryout_session') || 0)
    if (cached){
      try{
        const { data } = await api.get(`/tryouts/sessions/${cached}/current`)
        if (String(data.phase||'') !== 'done' && String(data.phase||'') !== 'finished'){
          resumeSessionId.value = cached
          return
        } else {
          localStorage.removeItem('active_tryout_session')
        }
      }catch{}
    }
  }catch{}
  // Fallback: latest unfinished in history
  try{
    const { data: sessions } = await api.get('/tryouts/sessions/history', { params: { limit: 10, offset: 0 } })
    const found = (sessions||[]).find(s => String(s.status||'') !== 'finished')
    if (found){
      try{
        const { data } = await api.get(`/tryouts/sessions/${found.id}/current`)
        if (String(data.phase||'') !== 'done' && String(data.phase||'') !== 'finished'){
          resumeSessionId.value = found.id
        } else {
          resumeSessionId.value = null
        }
      }catch{}
    }
  }catch{}
}

onMounted(() => {
  const l = localStorage.getItem('branding_logo'); if (l) logoSrc.value = l
  detectResume()
})
watch(() => route.path, () => { closeAllMenus(); closeMobile(); detectResume() })
watch(() => auth.isAuthenticated, () => { detectResume() })
</script>

<style scoped>
.site-header { background:#fff; border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 1000; }
.navbar { display:flex; align-items:center; height:60px; padding:0 12px; gap:12px; position:relative; }
.brand-link { display:flex; align-items:center; gap:8px; text-decoration:none; }
.brand-logo { height:30px; width:auto; display:block; }
.brand-text { font-weight:800; color: var(--text); letter-spacing:0.2px; font-size:16px; display:none; }

.links { margin-left:24px; display:none; gap:16px; align-items:center; }
.links a { color: var(--text); text-decoration:none; font-size:14px; white-space:nowrap; }
.links a.router-link-active { font-weight:700; }

.actions { margin-left:auto; display:flex; gap:8px; align-items:center; }
.actions a { color: var(--text); text-decoration:none; }
.actions .link-login { text-decoration:underline; color: var(--muted); }
.actions .btn.cta { background: var(--accent); border-color: rgba(0,0,0,0.08); color:#fff; }
.actions .btn.cta:hover { filter:brightness(0.98); }
.actions .btn.resume{ background:linear-gradient(90deg,#f97316,#fb923c); color:#fff; border:1px solid #fb923c; }

.dropdown { position:relative; }
.drop-toggle { color: var(--text); text-decoration:none; font-size:14px; display:inline-block; padding:6px 4px; cursor:pointer; }
.menu { position:absolute; top:100%; left:0; background:#fff; border:1px solid var(--border); border-radius:12px; box-shadow:0 10px 24px rgba(2,6,23,0.12); min-width:240px; padding:6px; z-index:50; color: var(--text); }
.menu a { display:block; padding:8px 12px; border-radius:10px; color: var(--text); text-decoration:none; font-size:14px; white-space:nowrap; transition:background-color .2s ease; }
.menu a:hover { background: #f3f4f6; }

.hamb { color: var(--text); background:transparent; border:1px solid var(--border); margin-left:auto; font-size:20px; cursor:pointer; }
.mobile-menu { position:absolute; left:0; right:0; top:100%; background:#fff; border-bottom-left-radius:12px; border-bottom-right-radius:12px; border-top:1px solid var(--border); display:flex; flex-direction:column; gap:6px; padding:10px 12px; z-index:2000; box-shadow:0 12px 24px rgba(0,0,0,0.08); }
.mobile-menu a, .mobile-menu .btn { color: var(--text) !important; padding:10px 8px; border-radius:12px; font-size:14px; text-align:left; }
.mobile-menu .btn { width:100%; }
.mobile-menu hr { border:none; border-top:1px solid var(--border); margin:4px 0; }

@media (min-width: 1024px){ .brand-text, .links, .actions { display:flex; } .hamb, .mobile-menu { display:none; } }
</style>