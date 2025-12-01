<template>
  <div class="card">
    <div class="head">
      <button class="btn secondary" @click="$router.push('/categories')">← All Heads</button>
      <h2 style="margin-left:8px;">Sub Categories</h2>
    </div>
    <div class="crumbs">Heads / <span class="strong">{{ headName || ('#'+route.params.headId) }}</span></div>
    <div v-if="headBanner" class="hero">
      <img :src="resolve(headBanner)" alt="banner" loading="lazy" decoding="async" />
      <div class="overlay">
        <div class="hero-title">{{ headName }}</div>
        <div class="hero-desc" v-if="headDescription">{{ headDescription }}</div>
      </div>
    </div>
    <div class="grid cols-3" style="gap:16px;">
      <div v-for="c in subs" :key="c.id" class="sub-card" @click="goSub(c)">
        <div class="sub-title">{{ c.name }}</div>
        <div class="sub-desc">{{ c.description || '—' }}</div>
        <div class="meta"><span class="pill small">{{ (setCounts[c.id]||0) }} set</span></div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api/client'
const route = useRoute()
const router = useRouter()
const subs = ref([])
const setCounts = ref({})
const headName = ref('')
const headBanner = ref('')
const headDescription = ref('')
onMounted(async () => {
  const headId = Number(route.params.headId)
  const { data } = await api.get(`/categories/${headId}/children`)
  subs.value = data
  // best effort head name from heads list
  try {
    const { data: heads } = await api.get('/categories/heads')
    const hd = heads.find(x=>x.id===headId) || {}
    headName.value = hd.name || ''
    headBanner.value = hd.banner_url || ''
    headDescription.value = hd.description || ''
  } catch {}
  // count sets per sub
  for (const c of subs.value){
    try{ const { data: sets } = await api.get('/sets/', { params: { category_id: c.id } }); setCounts.value[c.id] = sets.length } catch { setCounts.value[c.id] = 0 }
  }
})
function goSub(c){ router.push(`/categories/${route.params.headId}/${c.id}`) }
function resolve(src){
  if (!src) return ''
  const s = String(src)
  if (/^https?:\/\//i.test(s) || s.startsWith('data:image')) return s
  const path = s.startsWith('/') ? s : `/${s}`
  if (path.startsWith('/uploads/')){
    return `${window.location.origin.replace('5173','8000')}${path}`
  }
  return path
}
</script>
<style scoped>
.head{ display:flex; align-items:center; }
.sub-card{ cursor:pointer; background:white; border:1px solid #e2e8f0; border-radius:12px; padding:14px; box-shadow:0 2px 10px rgba(0,0,0,0.05); }
.sub-card:hover{ box-shadow:0 8px 22px rgba(0,0,0,0.08); }
.sub-title{ font-weight:800; color:#0f172a; font-size:18px; line-height:1.3; }
.sub-desc{ color:#64748b; margin-top:6px; font-size:14px; }
@media (max-width: 640px){
  .hero-title{ font-size:20px; }
}
.meta{ margin-top:8px; }
.crumbs{ color:#64748b; margin:8px 0 12px; }
.crumbs .strong{ color:#0f172a; font-weight:700; }
.hero{ position:relative; width:100%; aspect-ratio:16/9; border-radius:12px; overflow:hidden; margin-bottom:14px; background:#f1f5f9; display:flex; align-items:center; justify-content:center; }
.hero img{ width:100%; height:100%; object-fit:contain; display:block; }
.overlay{ position:absolute; inset:0; background:linear-gradient(180deg, rgba(15,23,42,0.2) 0%, rgba(15,23,42,0.55) 100%); color:white; display:flex; flex-direction:column; justify-content:flex-end; padding:14px; }
.hero-title{ font-weight:800; font-size:28px; line-height:1.2; text-shadow: 0 1px 2px rgba(0,0,0,0.3); }
.hero-desc{ opacity:0.95; margin-top:4px; max-width:70%; font-size:14px; }
.grid.cols-3{ display:grid; grid-template-columns: repeat(3,1fr); }
@media (max-width: 900px){ .grid.cols-3{ grid-template-columns: repeat(2,1fr); } }
@media (max-width: 640px){ .grid.cols-3{ grid-template-columns: 1fr; } }
</style>
