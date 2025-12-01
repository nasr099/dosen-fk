<template>
  <section class="card">
    <h2 class="title">Teams and people</h2>
    <p class="subtitle">Meet the people behind the product</p>

    <div class="grid team-grid">
      <div v-for="(m, i) in members" :key="i" class="member">
        <img :src="resolveImg(m.photo_url)" alt="photo" class="avatar" v-if="m.photo_url"/>
        <div v-else class="avatar placeholder">{{ initials(m.name) }}</div>
        <div class="headline" v-html="m.headline"></div>
        <div class="quote" v-html="m.quote"></div>
        <router-link v-if="m.more" :to="m.more" class="more">Read more</router-link>
        <div class="name">{{ m.name }}</div>
        <div class="role">{{ m.role }}</div>
        <div class="links">
          <a v-if="m.linkedin" :href="m.linkedin" target="_blank" rel="noreferrer">in</a>
          <a v-if="m.twitter" :href="m.twitter" target="_blank" rel="noreferrer">X</a>
          <a v-if="m.website" :href="m.website" target="_blank" rel="noreferrer">↗</a>
        </div>
      </div>
    </div>
  </section>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import api from '../api/client'

const members = ref([])

onMounted(async () => {
  try {
    const { data } = await api.get('/team/')
    members.value = data
  } catch {
    members.value = []
  }
})

function resolveImg(src){
  if (!src) return ''
  const s = String(src)
  if (/^https?:\/\//i.test(s) || s.startsWith('data:image')) return s
  const path = s.startsWith('/') ? s : `/${s}`
  if (path.startsWith('/uploads/')){
    return `${window.location.origin.replace('5173','8000')}${path}`
  }
  return path
}
function initials(name){
  return (name||'').split(' ').map(x=>x[0]).slice(0,2).join('').toUpperCase()
}
</script>
<style scoped>
.title{ text-align:center; margin:0; }
.subtitle{ text-align:center; color:#64748b; margin-top:6px; }
.member{ background: white; border:1px solid #e5e7eb; border-radius:14px; padding:16px; display:flex; flex-direction:column; align-items:center; text-align:center; gap:8px; box-shadow: 0 6px 16px rgba(2,6,23,0.06); }
.avatar{ width:96px; height:96px; object-fit:cover; border-radius:999px; }
.avatar.placeholder{ display:flex; align-items:center; justify-content:center; background:#e2e8f0; color:#334155; font-weight:800; font-size:28px; }
.headline{ font-weight:800; color:#0f172a; margin-top:6px; }
.quote{ color:#475569; font-style:italic; min-height:44px; }
.more{ color:#ea580c; font-weight:700; text-decoration:none; }
.name{ font-weight:800; margin-top:8px; }
.role{ color:#475569; }
.links{ display:flex; gap:10px; margin-top:6px; }
.links a{ color:#2563eb; text-decoration:none; font-weight:700; }
/* New styles for the team grid */
.team-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 18px;
  margin-top: 16px;
}
</style>
