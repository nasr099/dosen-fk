<template>
  <div class="card">
    <h2>Categories</h2>

    <div class="header-controls">
      <div class="chips" v-if="!isScopedToSub">
        <button class="pill" :class="{ active: selectedCategoryId===null }" @click="selectCategory(null)">All Program</button>
        <button v-for="c in categories" :key="c.id" class="pill" :class="{ active: selectedCategoryId===c.id }" @click="selectCategory(c.id)">{{ c.name }}</button>
      </div>
      <div class="search-sort">
        <input v-model="searchQuery" class="input" placeholder="Search set..." />
        <select v-model="planFilter" class="input">
          <option value="all">All plans</option>
          <option value="free">Free</option>
          <option value="paid">Paid</option>
        </select>
        <select v-model="statusFilter" class="input">
          <option value="all">All status</option>
          <option value="taken">Taken</option>
          <option value="not">Not taken</option>
        </select>
        <select v-model="sortMode" class="input">
          <option value="recent">Terbaru</option>
          <option value="oldest">Terdahulu</option>
          <option value="az">Judul (A-Z)</option>
          <option value="za">Judul (Z-A)</option>
        </select>
      </div>
    </div>

    <div class="table-wrap">
        <table class="sets-table">
          <thead>
            <tr>
              <th>Set</th>
              <th>Category</th>
              <th>Questions</th>
              <th>Status</th>
              <th>Duration</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in displayedSets" :key="s.id">
              <td>
                <div class="set-title" :title="s.title">{{ s.title }}</div>
                <div class="set-desc" v-if="s.description" :class="{ clamped: !isExpanded(s.id) }">{{ s.description }}</div>
                <button v-if="s.description && shouldShowToggle(s.description)" class="read-more" @click="toggleExpand(s.id)">
                  {{ isExpanded(s.id) ? 'Show less' : 'Read more' }}
                </button>
              </td>
              <td>
                <div style="display:flex; align-items:center; gap:8px;">
                  <span>{{ categoryName(s.category_id) }}</span>
                  <span class="plan-badge" :class="(s.access_level||'free')==='paid' ? 'paid':'free'">{{ (s.access_level||'free')==='paid' ? 'Paid' : 'Free' }}</span>
                </div>
              </td>
              <td>{{ s.count }} item</td>
              <td>
                <div class="status" :class="{ taken: lastResultBySet[s.id]?.taken }">
                  <span class="dot"></span>
                  <span v-if="lastResultBySet[s.id]?.taken">Taken</span>
                  <span v-else>Not taken</span>
                </div>
              </td>
              <td>{{ s.time_limit_minutes }} menit</td>
              <td style="text-align:right;">
                <router-link :to="{ name: 'set-overview', params: { setId: s.id } }"><button class="btn">Simulasi Test</button></router-link>
              </td>
            </tr>
            <tr v-if="displayedSets.length===0">
              <td colspan="5" class="empty">Tidak ada set.</td>
            </tr>
          </tbody>
        </table>
    </div>
  </div>
</template>
<script setup>
import { onMounted, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api/client'
const route = useRoute()
const router = useRouter()
const categories = ref([])
const sets = ref([])
const history = ref([])
const selectedCategoryId = ref(null)
const searchQuery = ref('')
const sortMode = ref('recent') // recent, oldest, az, za
const statusFilter = ref('all') // all | taken | not
const planFilter = ref('all') // all | free | paid
const selectedCategoryIds = ref([])
const sidebarCategoryQuery = ref('')
const isScopedToSub = computed(() => {
  const subId = Number(route.params.subId)
  return !!(subId && Number.isFinite(subId))
})

// track expanded rows for description
const expanded = ref(new Set())

function isExpanded(id){
  return expanded.value.has(id)
}
function toggleExpand(id){
  const s = new Set(expanded.value)
  if (s.has(id)) s.delete(id); else s.add(id)
  expanded.value = s
}
// show toggle only when text is long enough
function shouldShowToggle(text){
  return String(text || '').length > 180
}

function categoryName(id){
  const c = categories.value.find(x => x.id === id)
  return c ? c.name : id
}

function selectCategory(id){
  selectedCategoryId.value = id
}

// sidebar removed; keep simple chips + search/sort

const displayedSets = computed(() => {
  let arr = sets.value
  // chips quick filter
  if (selectedCategoryId.value){ arr = arr.filter(s => s.category_id === selectedCategoryId.value) }
  // sidebar multi-select
  if (selectedCategoryIds.value.length > 0){
    const setIds = new Set(selectedCategoryIds.value.map(Number))
    arr = arr.filter(s => setIds.has(s.category_id))
  }
  // search
  const q = searchQuery.value.toLowerCase().trim()
  if (q){ arr = arr.filter(s => String(s.title||'').toLowerCase().includes(q)) }
  // plan filter
  if (planFilter.value !== 'all'){
    arr = arr.filter(s => (String(s.access_level||'free') === planFilter.value))
  }
  // status filter
  if (statusFilter.value !== 'all'){
    arr = arr.filter(s => {
      const taken = !!lastResultBySet.value?.[s.id]?.taken
      return statusFilter.value === 'taken' ? taken : !taken
    })
  }
  // sort
  const byTitleAsc = (a,b) => String(a.title||'').localeCompare(String(b.title||''))
  const byIdAsc = (a,b) => Number(a.id) - Number(b.id)
  switch (sortMode.value){
    case 'az': arr = [...arr].sort(byTitleAsc); break
    case 'za': arr = [...arr].sort((a,b)=>byTitleAsc(b,a)); break
    case 'oldest': arr = [...arr].sort(byIdAsc); break
    case 'recent': default: arr = [...arr].sort((a,b)=>byIdAsc(b,a)); break
  }
  return arr
})

// Map last result per set id
const pickFirst = (obj, keys) => {
  for (const k of keys){
    const v = obj?.[k]
    if (v !== undefined && v !== null && String(v).trim?.() !== '') return v
  }
  return null
}
const lastResultBySet = computed(() => {
  const by = {}
  for (const h of history.value || []){
    const sid = Number(pickFirst(h, ['question_set_id','set_id','questionSetId','setId']))
    if (!sid || Number.isNaN(sid)) continue
    // keep latest by created_at/updated_at/id if available
    const keyTime = pickFirst(h, ['updated_at','created_at','createdAt','id']) || 0
    const score = Number(pickFirst(h, ['score_percentage','score','scorePercentage']))
    if (!by[sid] || String(keyTime) > String(by[sid].keyTime)){
      by[sid] = { taken: true, score: Number.isFinite(score) ? score : null, keyTime }
    }
  }
  return by
})

onMounted(async () => {
  const { data: cats } = await api.get('/categories/')
  categories.value = cats
  const subId = Number(route.params.subId)
  // If a sub-category id is provided by route, only load that category's sets
  if (subId && Number.isFinite(subId)){
    selectedCategoryId.value = subId
    const { data: s } = await api.get('/sets/', { params: { category_id: subId } })
    const all = []
    for (const one of s){
      const { data: qs } = await api.get('/questions/', { params: { question_set_id: one.id } })
      all.push({ ...one, count: qs.length })
    }
    sets.value = all
  } else {
    // load all sets and their question counts grouped by categories
    const all = []
    for (const c of categories.value){
      const { data: s } = await api.get('/sets/', { params: { category_id: c.id } })
      for (const one of s){
        const { data: qs } = await api.get('/questions/', { params: { question_set_id: one.id } })
        all.push({ ...one, count: qs.length })
      }
    }
    sets.value = all
  }

  // fetch exam history to determine taken status and scores
  try {
    const { data: hist } = await api.get('/exams/history')
    history.value = Array.isArray(hist) ? hist : []
  } catch {}
})
</script>

<style scoped>
.header-controls{ display:flex; gap:12px; align-items:center; justify-content:space-between; margin-bottom:12px; flex-wrap:wrap; }
.chips{ display:flex; flex-wrap:wrap; gap:8px; }
.search-sort{ display:flex; gap:8px; align-items:center; }
.chips .pill{ padding:6px 10px; }
.filters { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:12px; }
.pill { padding:6px 12px; border-radius:9999px; border:1px solid #e2e8f0; background:white; cursor:pointer; }
.pill.active { background:#2563eb; color:white; border-color:#2563eb; }
.table-wrap { overflow:auto; }
.sets-table { width:100%; border-collapse: separate; border-spacing: 0 8px; }
.sets-table th, .sets-table td { padding:10px 12px; text-align:left; }
.sets-table th { background:#f8fafc; font-weight:700; color:#0f172a; }
.sets-table tbody tr { background:#ffffff; border:1px solid #e5e7eb; transition: box-shadow .2s ease, transform .2s ease; cursor:default; }
.sets-table tbody tr:hover { box-shadow: 0 8px 28px rgba(2,6,23,0.08), 0 2px 6px rgba(2,6,23,0.06); transform: translateY(-1px); }
.sets-table tbody td { border-bottom:none; }
.sets-table tbody td:first-child { border-top-left-radius: 12px; border-bottom-left-radius: 12px; }
.sets-table tbody td:last-child { border-top-right-radius: 12px; border-bottom-right-radius: 12px; }
.set-title { font-weight:700; color:#0f172a; max-width: 520px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.set-desc { color:#64748b; font-size:14px; }
.set-desc.clamped { overflow:hidden; display:-webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 1; }
.read-more { display:none; }
.sets-table tbody tr{ height: 92px; }
.status{ display:inline-flex; align-items:center; gap:8px; color:#64748b; font-weight:600; }
.status .dot{ width:10px; height:10px; border-radius:999px; background:#cbd5e1; display:inline-block; }
.status.taken{ color:#065f46; }
.status.taken .dot{ background:#16a34a; }
.empty { text-align:center; color:#94a3b8; padding:16px 0; }
.plan-badge{ font-size:12px; font-weight:800; padding:2px 8px; border-radius:999px; border:1px solid #e2e8f0; background:#f8fafc; color:#0f172a; }
.plan-badge.paid{ background:#fef3c7; color:#92400e; border-color:#fde68a; }
.plan-badge.free{ background:#ecfeff; color:#155e75; border-color:#a5f3fc; }
</style>
