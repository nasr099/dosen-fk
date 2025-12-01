<template>
  <div class="card">
    <h2>{{ tryout?.title || 'Tryout' }}</h2>
    <div class="desc" v-if="tryout && (tryout.description||'').trim()" v-html="renderHTML(tryout.description)"></div>
    <div class="muted" v-else>Prepare for the tryout. When you click Start, the first set will begin with a 60s intermission.</div>
    <div class="actions">
      <button v-if="resumeSessionId" class="btn warn" @click="resume">Resume</button>
      <button class="btn" :disabled="busy" @click="start">{{ busy ? 'Starting…' : 'Start Tryout' }}</button>
      <router-link class="btn secondary" to="/">Back</router-link>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../../api/client'
import { renderMathHTML } from '../../utils/math'

const route = useRoute()
const router = useRouter()
const busy = ref(false)
const tryout = ref(null)
const resumeSessionId = ref(null)

function renderHTML(html){ return renderMathHTML(String(html||'')) }

async function load(){
  const id = Number(route.params.id)
  try { const { data } = await api.get(`/tryouts/${id}`); tryout.value = data } catch { tryout.value = null }
  // Find unfinished session for this tryout
  try{
    const { data: sessions } = await api.get('/tryouts/sessions/history', { params: { limit: 20, offset: 0 } })
    const found = (sessions||[]).find(s => s.tryout_id === id && String(s.status||'') !== 'finished')
    if (found){
      try{
        const { data } = await api.get(`/tryouts/sessions/${found.id}/current`)
        if (String(data.phase||'') !== 'done' && String(data.phase||'') !== 'finished'){
          resumeSessionId.value = found.id
        } else {
          resumeSessionId.value = null
        }
      }catch{ resumeSessionId.value = null }
    }
  }catch{}
}

async function start(){
  try{
    busy.value = true
    // Request fullscreen as part of the user gesture
    try {
      const el = document.documentElement
      if (!document.fullscreenElement && el?.requestFullscreen) {
        await el.requestFullscreen()
      }
    } catch {}
    const id = Number(route.params.id)
    const { data } = await api.post(`/tryouts/${id}/start`)
    try { localStorage.setItem('active_tryout_session', String(data.tryout_session_id)) } catch {}
    router.push({ path: `/tryout/run/${data.tryout_session_id}` })
  } finally {
    busy.value = false
  }
}

async function resume(){
  if (!resumeSessionId.value) return
  try{
    const { data } = await api.get(`/tryouts/sessions/${resumeSessionId.value}/current`)
    if (String(data.phase||'') === 'done' || String(data.phase||'') === 'finished'){
      resumeSessionId.value = null
      try { localStorage.removeItem('active_tryout_session') } catch {}
      return
    }
  }catch{ return }
  router.push({ path: `/tryout/run/${resumeSessionId.value}` })
}

onMounted(load)
</script>
<style scoped>
.muted{ color:#64748b; }
.desc{ color:#1f2937; line-height:1.85; letter-spacing:0.1px; margin:8px 0 2px; }
.desc :deep(img){ max-width:100%; border-radius:8px; display:block; margin:8px auto; }
.actions{ margin-top:12px; display:flex; gap:8px; align-items:center; }
</style>
