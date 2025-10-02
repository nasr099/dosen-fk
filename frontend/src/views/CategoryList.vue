<template>
  <div class="card">
    <h2>Categories</h2>

    <div class="header-controls">
      <div class="chips">
        <button class="pill" :class="{ active: selectedCategoryId===null }" @click="selectCategory(null)">All Program</button>
        <button v-for="c in categories" :key="c.id" class="pill" :class="{ active: selectedCategoryId===c.id }" @click="selectCategory(c.id)">{{ c.name }}</button>
      </div>
      <div class="search-sort">
        <input v-model="searchQuery" class="input" placeholder="Search set..." />
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
              <td>{{ categoryName(s.category_id) }}</td>
              <td>{{ s.count }} item</td>
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
import api from '../api/client'
const categories = ref([])
const sets = ref([])
const selectedCategoryId = ref(null)
const searchQuery = ref('')
const sortMode = ref('recent') // recent, oldest, az, za
const selectedCategoryIds = ref([])
const sidebarCategoryQuery = ref('')

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

onMounted(async () => {
  const { data: cats } = await api.get('/categories/')
  categories.value = cats
  // load all sets and their question counts
  const all = []
  for (const c of categories.value){
    const { data: s } = await api.get('/sets/', { params: { category_id: c.id } })
    for (const one of s){
      const { data: qs } = await api.get('/questions/', { params: { question_set_id: one.id } })
      all.push({ ...one, count: qs.length })
    }
  }
  sets.value = all
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
.sets-table { width:100%; border-collapse: collapse; }
.sets-table th, .sets-table td { padding:10px 12px; border-bottom:1px solid #e2e8f0; text-align:left; }
.sets-table th { background:#f8fafc; font-weight:700; color:#0f172a; }
.set-title { font-weight:700; color:#0f172a; max-width: 520px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.set-desc { color:#64748b; font-size:14px; }
.set-desc.clamped { overflow:hidden; display:-webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 1; }
.read-more { display:none; }
.sets-table tbody tr{ height: 92px; }
.empty { text-align:center; color:#94a3b8; padding:16px 0; }
</style>
