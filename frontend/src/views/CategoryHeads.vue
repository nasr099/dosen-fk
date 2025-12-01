<template>
  <div class="card">
    <h2>Categories</h2>
    <div class="grid cols-3" style="gap:16px;">
      <div v-for="h in heads" :key="h.id" class="head-card" @click="goHead(h.id)">
        <div v-if="h.banner_url" class="banner-box">
          <img class="banner" :src="resolve(h.banner_url)" alt="banner" loading="lazy" />
        </div>
        <div class="head-title">{{ h.name }}</div>
        <div class="head-desc">{{ h.description || '—' }}</div>
        <div class="meta">
          <span class="pill small">{{ (subCounts[h.id]||0) }} sub</span>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '../api/client'
const router = useRouter()
const route = useRoute()
const heads = ref([])
const subCounts = ref({})
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
onMounted(async () => {
  const { data } = await api.get('/categories/heads')
  heads.value = data
  // fetch children count per head
  for (const h of heads.value){
    try{
      const { data: subs } = await api.get(`/categories/${h.id}/children`)
      subCounts.value[h.id] = Array.isArray(subs) ? subs.length : 0
    } catch { subCounts.value[h.id] = 0 }
  }
  // If ?headId=123 is present, navigate directly to that head's page
  const qid = Number(route.query.headId)
  if (Number.isFinite(qid) && qid > 0){
    router.push(`/categories/${qid}`)
  }
})
function goHead(id){ router.push(`/categories/${id}`) }
</script>
<style scoped>
.head-card{ cursor:pointer; background:white; border:1px solid #e2e8f0; border-radius:12px; padding:12px; box-shadow:0 2px 10px rgba(0,0,0,0.05); display:flex; flex-direction:column; gap:8px; overflow:hidden; }
.banner-box{ width:100%; aspect-ratio: 16/9; background:#f1f5f9; border-radius:8px; overflow:hidden; display:flex; align-items:center; justify-content:center; }
.banner{ width:100%; height:100%; object-fit:contain; display:block; }
.head-card:hover{ box-shadow:0 8px 22px rgba(0,0,0,0.08); }
.head-title{ font-weight:800; color:#0f172a; font-size:18px; line-height:1.25; }
.head-desc{ color:#64748b; margin-top:6px; font-size:14px; }
.meta{ margin-top:8px; }
.pill.small{ font-size:12px; padding:2px 8px; border:1px solid #e2e8f0; border-radius:999px; background:#f8fafc; color:#0f172a; display:inline-block; }
.grid.cols-3{ display:grid; grid-template-columns: repeat(3,1fr); }
@media (max-width: 900px){ .grid.cols-3{ grid-template-columns: repeat(2,1fr); } }
@media (max-width: 640px){ .grid.cols-3{ grid-template-columns: 1fr; } }
</style>
