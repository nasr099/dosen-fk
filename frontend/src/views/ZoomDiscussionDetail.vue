<template>
  <div class="card">
    <div class="detail">
      <div class="left">
        <div class="thumb" v-if="item.image_url"><img :src="resolve(item.image_url)" alt="presenter" /></div>
      </div>
      <div class="right">
        <h2 class="title">{{ item.title }}</h2>
        <div class="presenter">Presenter: <strong>{{ item.presenter_name }}</strong></div>
        <div class="time">Waktu: {{ formatTime(item.start_at) }}</div>
        <div class="desc" v-if="item.description">{{ item.description }}</div>
        <div class="access" v-if="auth.isAuthenticated">
          <template v-if="auth.user?.plan === 'paid'">
            <div class="secret">
              <div><strong>Meeting Link</strong>: <a :href="normalizeLink(access.meeting_url)" target="_blank" rel="noopener noreferrer">{{ normalizeLink(access.meeting_url) }}</a></div>
              <div v-if="access.meeting_password"><strong>Password</strong>: {{ access.meeting_password }}</div>
            </div>
          </template>
          <template v-else>
            <div class="locked">Upgrade ke paket berbayar untuk mengakses link meeting.</div>
          </template>
        </div>
        <div class="access" v-else>
          <div class="locked">Login untuk melihat akses meeting (khusus pengguna berbayar).</div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../store/auth'
import api from '../api/client'
const route = useRoute()
const auth = useAuthStore()
const item = ref({})
const access = ref({})
function resolve(src){
  if (!src) return ''
  const s = String(src)
  if (/^https?:\/\//i.test(s) || s.startsWith('data:image')) return s
  const path = s.startsWith('/') ? s : `/${s}`
  if (path.startsWith('/uploads/')) return `${window.location.origin.replace('5173','8000')}${path}`
  return path
}
function formatTime(s){ try { return new Date(s).toLocaleString('id-ID', { timeZone: 'Asia/Jakarta' }) } catch { return s } }
function normalizeLink(u){
  if (!u) return ''
  const s = String(u).trim()
  if (/^https?:\/\//i.test(s)) return s
  return `https://${s}`
}
onMounted(async () => {
  const id = Number(route.params.id)
  const { data } = await api.get(`/zoom-discussions/${id}`)
  item.value = data
  if (auth.isAuthenticated && auth.user?.plan === 'paid'){
    try{ const { data: acc } = await api.get(`/zoom-discussions/${id}/access`); access.value = acc } catch {}
  }
})
</script>
<style scoped>
.desc{ white-space: pre-line; }
.detail{ display:grid; grid-template-columns: 1fr 1.6fr; gap:16px; }
.thumb{ width:100%; aspect-ratio: 16/9; background:#f1f5f9; border-radius:12px; overflow:hidden; }
.thumb img{ width:100%; height:100%; object-fit:cover; display:block; }
.right .title{ font-weight:800; margin:0; }
.presenter{ color:#334155; margin-top:6px; }
.time{ color:#64748b; margin-top:4px; }
.desc{ margin-top:10px; color:#334155; line-height:1.7; }
.access{ margin-top:14px; }
.locked{ background:#fff7ed; border:1px solid #fed7aa; color:#9a3412; padding:10px 12px; border-radius:10px; }
.secret{ background:#ecfeff; border:1px solid #a5f3fc; color:#155e75; padding:10px 12px; border-radius:10px; display:flex; flex-direction:column; gap:6px; }
@media (max-width: 900px){ .detail{ grid-template-columns: 1fr; } }
</style>
