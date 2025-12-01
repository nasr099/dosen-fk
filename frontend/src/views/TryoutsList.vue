<template>
  <div class="card">
    <h2>Tryouts</h2>
    <div class="filters toolbar">
      <div class="filters-left">
        <input class="input search" v-model="q" placeholder="Search tryouts…" @keyup.enter="apply" />
        <select class="input sm" v-model="cat" title="Category">
          <option value="">All Categories</option>
          <option v-for="c in tryoutCats" :key="c" :value="c">{{ c }}</option>
        </select>
        <select class="input sm" v-model="status" title="Status">
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
          <option value="all">All</option>
        </select>
        <select class="input sm" v-model="sortBy" title="Sort by">
          <option value="title">Title</option>
          <option value="sets">Sets</option>
          <option value="duration">Total Duration</option>
        </select>
        <select class="input xs" v-model="sortDir" title="Direction">
          <option value="asc">Asc</option>
          <option value="desc">Desc</option>
        </select>
      </div>
      <div class="filters-right">
        <button class="btn small" @click="apply">Apply</button>
        <button class="btn small secondary" @click="reset">Reset</button>
      </div>
    </div>
    <div v-if="loading" class="muted">Loading tryouts…</div>
    <div v-else-if="error" class="err">{{ error }}</div>
    <div v-else>
      <table class="table">
        <thead>
          <tr>
            <th>Title</th>
            <th>Description</th>
            <th>Category</th>
            <th>Sets</th>
            <th>Total Duration</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in rows" :key="t.id">
            <td>{{ t.title }}</td>
            <td class="desc">{{ shortDesc(t.description) }}</td>
            <td>{{ t.category || 'Uncategorized' }}</td>
            <td>{{ setsCount(t) }}</td>
            <td>{{ totalMinutes(t) }} min</td>
            <td class="action">
              <template v-if="auth.isAuthenticated">
                <button class="btn small" @click="goLobby(t)">Start</button>
              </template>
              <template v-else>
                <button class="btn small secondary" @click="goLogin">Login</button>
              </template>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="!rows.length" class="muted">No tryouts available.</div>
      <div class="pager" v-else>
        <div class="pager-left">
          <label>Rows</label>
          <select v-model.number="pageSize" @change="toPage(1)">
            <option :value="10">10</option>
            <option :value="20">20</option>
            <option :value="50">50</option>
          </select>
        </div>
        <div class="pager-right">
          <button class="btn small secondary" :disabled="page<=1" @click="toPage(page-1)">Prev</button>
          <span>Page {{ page }} / {{ pageCount }}</span>
          <button class="btn small" :disabled="page>=pageCount" @click="toPage(page+1)">Next</button>
        </div>
      </div>
    </div>
  </div>
  </template>
<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/client'
import { useAuthStore } from '../store/auth'

const router = useRouter()
const auth = useAuthStore()
const rows = ref([])
const loading = ref(false)
const error = ref('')
const busyId = ref(0)
const tryoutCats = ref([])
const q = ref('')
const cat = ref('')
const status = ref('active') // active | inactive | all
const sortBy = ref('title') // title | sets | duration
const sortDir = ref('asc') // asc | desc
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

async function load(){
  loading.value = true
  error.value = ''
  try{
    const params = {
      include_all: 1,
      paginated: 1,
      q: q.value || '',
      category: cat.value || '',
      status: status.value || 'active',
      sort_by: sortBy.value === 'title' ? 'title' : (sortBy.value === 'sets' ? 'sets' : (sortBy.value === 'duration' ? 'duration' : 'created_at')),
      sort_dir: sortDir.value || 'asc',
      limit: pageSize.value,
      offset: (page.value - 1) * pageSize.value,
    }
    const [t1, t2] = await Promise.all([
      api.get('/tryouts/', { params }),
      api.get('/tryouts/categories'),
    ])
    const data = t1.data || {}
    rows.value = Array.isArray(data.items) ? data.items : (Array.isArray(data) ? data : [])
    total.value = Number(data.total || rows.value.length || 0)
    tryoutCats.value = Array.isArray(t2.data) ? t2.data : []
  }catch(e){
    error.value = e?.response?.data?.detail || e?.message || 'Failed to load tryouts'
  }finally{
    loading.value = false
  }
}

const pageCount = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

function apply(){ page.value = 1; load() }
function reset(){ q.value=''; cat.value=''; status.value='active'; sortBy.value='title'; sortDir.value='asc'; page.value=1; load() }
function toPage(p){ page.value = Math.max(1, Math.min(pageCount.value, p)); load() }

function shortDesc(html){
  const s = String(html||'').replace(/<[^>]*>/g,'').trim()
  return s.length>140 ? (s.slice(0,140)+'…') : s
}

function totalMinutes(t){
  const api = Number(t?.duration_minutes)
  if (!Number.isNaN(api) && api > 0) return api
  try{ return (t.sets||[]).reduce((sum,s)=> sum + Number(s.duration_minutes||0), 0) }catch{ return 0 }
}

function setsCount(t){
  const api = Number(t?.sets_count)
  if (!Number.isNaN(api) && api >= 0) return api
  try{ return (t.sets||[]).length }catch{ return 0 }
}

function goLobby(t){ if (t && t.id) router.push({ path: `/tryout/${t.id}` }) }

function goLogin(){ router.push('/login') }

onMounted(load)
</script>
<style scoped>
.filters.toolbar{ display:flex; align-items:center; justify-content:space-between; gap:12px; margin:8px 0 12px; }
.filters-left{ display:flex; align-items:center; gap:8px; flex-wrap:wrap; flex:1; }
.filters-right{ display:flex; align-items:center; gap:8px; }
.input.search{ min-width:260px; flex:1; }
.input.sm{ width:180px; }
.input.xs{ width:120px; }
.table{ width:100%; border-collapse:separate; border-spacing:0; margin-top:10px; border:1px solid #e5e7eb; border-radius:12px; overflow:hidden; background:#fff; }
.table thead th{ background:#f8fafc; font-weight:700; color:#0f172a; }
.table th{ text-align:left; padding:10px 12px; border-bottom:1px solid #e2e8f0; }
.table td{ padding:10px 12px; border-bottom:1px solid #e2e8f0; }
.table td.desc{ max-width:480px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.table tbody tr:nth-child(2n){ background:#fafafa; }
.table tbody tr:hover{ background:#f1f5f9; }
.table td.action{ text-align:right; }
.muted{ color:#64748b; }
.err{ color:#b91c1c; }
/* Pager: center buttons */
.pager{ position:relative; margin-top:8px; min-height:40px; }
.pager-left{ display:inline-flex; align-items:center; gap:8px; }
.pager-right{ position:absolute; left:50%; transform: translateX(-50%); display:inline-flex; align-items:center; gap:10px; }
@media (max-width: 720px){
  .input.search{ min-width:180px; }
  .input.sm{ width:150px; }
  .filters.toolbar{ flex-direction:column; align-items:stretch; }
  .filters-right{ justify-content:flex-end; }
  .pager{ padding-top:6px; }
  .pager-right{ position:static; transform:none; justify-content:center; width:100%; margin-top:6px; }
}
</style>
