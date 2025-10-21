<template>
  <div class="card">
    <div class="head">
      <h2 style="margin:0;">Zoom Discussion</h2>
      <div class="hint">Daftar diskusi Zoom. Tag menunjukkan status: Upcoming / Live / Finished.</div>
      <div class="controls" style="margin-left:auto; display:flex; gap:8px;">
        <select class="input" v-model="subFilter">
          <option :value="null">Semua Sub Category</option>
          <option v-for="c in subCategories" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
        <select class="input" v-model="filterMode">
          <option value="all">Semua Status</option>
          <option value="up">Upcoming</option>
          <option value="live">Live</option>
          <option value="done">Finished</option>
        </select>
      </div>
    </div>
    <div class="grid cols-4" style="gap:12px; margin-top:12px;">
      <div v-for="z in paged" :key="z.id" class="zoom-card" @click="open(z.id)">
        <div class="thumb" v-if="z.image_url"><img :src="resolve(z.image_url)" alt="presenter" loading="lazy" /></div>
        <div class="content">
          <div class="row top">
            <span class="chip" :class="z.status==='Upcoming' ? 'up' : 'done'">{{ z.status }}</span>
            <span class="date-badge">📅 {{ formatLocal(z.start_at) }}</span>
          </div>
          <div
            class="cat-badge"
            v-if="z.category_id"
            :style="{
              background: 'transparent',
              color: bandColor(categoryName(z.category_id)),
              borderColor: bandColor(categoryName(z.category_id))
            }"
          >
            {{ categoryName(z.category_id) }}
          </div>
          <div class="title" :title="z.title">{{ z.title }}</div>
          <div class="presenter">{{ z.presenter_name }}</div>
          <div class="desc">{{ z.description }}</div>
        </div>
      </div>
    </div>
    <div v-if="filtered.length===0" class="empty">Belum ada jadwal.</div>
    <div class="pager" v-else>
      <button class="btn secondary" :disabled="page===1" @click="page--">Prev</button>
      <span class="pinfo">Halaman {{ page }} / {{ totalPages }}</span>
      <button class="btn" :disabled="page===totalPages" @click="page++">Next</button>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/client'
const router = useRouter()
const items = ref([])
const categories = ref([])
const subCategories = computed(() => (categories.value || []).filter(c => !!c.parent_id))
const filterMode = ref('all') // all | up | live | done
const subFilter = ref(null)
const page = ref(1)
const pageSize = ref(9)
const filtered = computed(() => {
  let arr = items.value
  if (subFilter.value){ arr = arr.filter(z => Number(z.category_id) === Number(subFilter.value)) }
  if (filterMode.value === 'up') arr = arr.filter(z => z.status === 'Upcoming')
  else if (filterMode.value === 'live') arr = arr.filter(z => z.status === 'Live')
  else if (filterMode.value === 'done') arr = arr.filter(z => z.status === 'Finished')
  return arr
})
const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / pageSize.value)))
const paged = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return filtered.value.slice(start, start + pageSize.value)
})
function resolve(src){
  if (!src) return ''
  const s = String(src)
  if (/^https?:\/\//i.test(s) || s.startsWith('data:image')) return s
  const path = s.startsWith('/') ? s : `/${s}`
  if (path.startsWith('/uploads/')) return `${window.location.origin.replace('5173','8000')}${path}`
  return path
}
function formatLocal(s){
  try{ return new Date(s).toLocaleString('id-ID', { timeZone: 'Asia/Jakarta', dateStyle: 'medium', timeStyle: 'short' }) } catch { return s }
}
function open(id){ router.push(`/zoom/${id}`) }
onMounted(async () => {
  const { data } = await api.get('/zoom-discussions/')
  const { data: cats } = await api.get('/categories/')
  categories.value = cats
  // show upcoming first then finished
  items.value = data.sort((a,b)=>{
    if (a.status===b.status) return String(b.start_at).localeCompare(String(a.start_at))
  })
  page.value = 1
})
function categoryName(id){
  const c = (categories.value || []).find(x => x.id === Number(id))
  return c ? c.name : ''
}
// Simple deterministic color mapping (aligned with Home.vue)
function bandColor(name){
  const map = {
    'Anatomy': '#ef4444',
    'Physiology': '#10b981',
    'Pharmacology': '#8b5cf6',
    'Pathology': '#f59e0b',
    'Biochemistry': '#0ea5e9',
    'Microbiology': '#14b8a6',
    'Neurology': '#f43f5e',
    'Radiology': '#6366f1',
    'Surgery': '#22c55e',
    'Pediatrics': '#f97316',
    'Psychiatry': '#06b6d4',
    'Obstetrics': '#a3e635',
  }
  if (map[name]) return map[name]
  const palette = ['#ef4444','#10b981','#8b5cf6','#f59e0b','#0ea5e9','#14b8a6','#f43f5e','#6366f1','#22c55e','#f97316']
  let hash = 0
  const s = String(name || '')
  for (let i = 0; i < s.length; i++) { hash = ((hash << 5) - hash) + s.charCodeAt(i); hash |= 0 }
  const idx = Math.abs(hash * 1315423911) % palette.length
  return palette[idx]
}
</script>
<style scoped>
.pager{ display:flex; gap:10px; justify-content:center; align-items:center; width:100%; margin:22px 0 10px; }
.hint{ color:#64748b; }
.zoom-card{ cursor:pointer; background:#fff; border:1px solid #e2e8f0; border-radius:12px; overflow:hidden; box-shadow:0 2px 10px rgba(0,0,0,0.05); }
.content{ padding:12px; display:flex; flex-direction:column; gap:8px; }
.thumb{ width:100%; height:160px; background:#f1f5f9; }
.thumb img{ width:100%; height:100%; object-fit:cover; display:block; }
@media (max-width: 900px){ .thumb{ height:140px; } }
.title{ font-weight:800; color:#0f172a; line-height:1.4; }
.presenter{ font-weight:700; color:#334155; font-size:14px; line-height:1.5; }
.cat-badge{ font-size:12px; background:transparent; border:1px solid currentColor; border-radius:999px; padding:2px 8px; display:inline-block; margin-bottom:6px; align-self:flex-start; }
.chip{ font-size:12px; padding:2px 8px; border-radius:999px; border:1px solid #e2e8f0; }
.chip.up{ background:#ecfeff; color:#155e75; border-color:#a5f3fc; }
.chip.done{ background:#f8fafc; color:#334155; }
.grid.cols-3{ display:grid; grid-template-columns: repeat(3,1fr); }
@media (max-width: 900px){ .grid.cols-3{ grid-template-columns: repeat(2,1fr); } }
@media (max-width: 640px){ .grid.cols-3{ grid-template-columns: 1fr; } }
.empty{ text-align:center; color:#94a3b8; padding:16px 0; }
/* Grid columns like set cards */
.grid.cols-4{ display:grid; grid-template-columns: repeat(4,1fr); }
@media (max-width: 1200px){ .grid.cols-4{ grid-template-columns: repeat(3,1fr); } }
@media (max-width: 900px){ .grid.cols-4{ grid-template-columns: repeat(2,1fr); } }
@media (max-width: 640px){ .grid.cols-4{ grid-template-columns: 1fr; } }

</style>
