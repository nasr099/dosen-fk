<template>
  <div class="card">
    <h2>Categories</h2>
    <form class="new-cat" @submit.prevent="add">
      <input v-model="form.name" placeholder="Name" class="input" required />
      <input v-model="form.description" placeholder="Description" class="input" />
      <button class="btn">Add Category</button>
    </form>

    <div class="section head-section">
    <h3 class="section-title">Head Categories</h3>
    <div class="section-toolbar">
      <input class="input" v-model="headSearch" placeholder="Search head categories…" />
      <select class="input" v-model="headSort">
        <option value="new_old">Sort: New → Old</option>
        <option value="old_new">Sort: Old → New</option>
        <option value="name_asc">Sort: Name A→Z</option>
        <option value="name_desc">Sort: Name Z→A</option>
      </select>
    </div>
    <table class="cat-table">
      <thead>
        <tr>
          <th style="min-width:160px;">Name</th>
          <th>Description</th>
          <th style="min-width:150px;">Parent</th>
          <th style="min-width:90px;">Emoji</th>
          <th style="min-width:200px;">Image URL</th>
          <th style="min-width:220px;">Banner URL</th>
          <th>Sub-categories</th>
          <th style="min-width:220px;">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="c in headRows" :key="c.id">
          <td>
            <template v-if="isEditing(c.id)">
              <input class="input" v-model="editBuffer[c.id].name" />
            </template>
            <template v-else>{{ c.name }}</template>
          </td>
          <td>
            <template v-if="isEditing(c.id)"><textarea class="input textarea" v-model="editBuffer[c.id].description"></textarea></template>
            <template v-else><div class="desc-clamp" :title="c.description">{{ c.description }}</div></template>
          </td>
          <td>
            <select class="input" v-model="c.parent_id">
              <option :value="''">None (Head)</option>
              <option v-for="h in headOptions(c.id)" :key="h.id" :value="h.id">{{ h.name }}</option>
            </select>
            <button class="btn tiny" @click="saveParent(c)">Save</button>
          </td>
          <td>
            <input class="input" placeholder="e.g. 🔬" v-model="branding[keyOf(c.id)].icon" @input="touch(c.id)" />
          </td>
          <td>
            <div class="col-stack">
              <input class="input" placeholder="https://.../icon.png or /uploads/.." v-model="branding[keyOf(c.id)].icon_url" @input="touch(c.id)" />
              <div class="row-actions">
                <button class="btn tiny" @click="saveBranding(c.id)">Save Logo</button>
              </div>
            </div>
          </td>
          <td>
            <div class="col-stack">
              <input class="input" placeholder="https://.../banner.jpg or /uploads/..." v-model="c.banner_url" />
              <div class="row-actions">
                <button class="btn tiny" @click="saveBanner(c)">Save Banner</button>
              </div>
            </div>
          </td>
          <td>
            <span>{{ childCount(c.id) }} sub</span>
          </td>
          <td class="row-actions">
            <button class="btn tiny" @click="isEditing(c.id) ? saveMeta(c) : toggleEdit(c)">{{ isEditing(c.id) ? 'Save Meta' : 'Edit' }}</button>
            <button class="btn tiny secondary" v-if="isEditing(c.id)" @click="cancelEdit(c.id)">Cancel</button>
            <a class="btn tiny secondary" :href="publicLink(c)" target="_blank">View</a>
            <button class="btn tiny secondary" @click="remove(c.id)">Delete</button>
          </td>
        </tr>
      </tbody>
    </table>
    </div>
    <!-- close head-section -->

    <div class="section sub-section">
    <h3 class="section-title with-actions" style="margin-top:16px;">
      <span>Sub Categories</span>
      <span class="row-actions">
        <button class="btn tiny" @click="expandAllSub">Expand all</button>
        <button class="btn tiny secondary" @click="collapseAllSub">Collapse all</button>
      </span>
    </h3>
    <div class="section-toolbar">
      <input class="input" v-model="subSearch" placeholder="Search sub categories…" />
      <select class="input" v-model="subParentFilter">
        <option :value="null">All Parents</option>
        <option v-for="h in heads" :key="h.id" :value="h.id">{{ h.name }}</option>
      </select>
      <select class="input" v-model="subSort">
        <option value="name_asc">Sort: Name A→Z</option>
        <option value="name_desc">Sort: Name Z→A</option>
        <option value="new_old">Sort: New → Old</option>
        <option value="old_new">Sort: Old → New</option>
      </select>
    </div>
    <table class="cat-table">
      <thead>
        <tr>
          <th style="width:80px;">Sets</th>
          <th style="min-width:160px;">Name</th>
          <th>Description</th>
          <th style="min-width:150px;">Parent</th>
          <th style="min-width:90px;">Emoji</th>
          <th style="min-width:200px;">Image URL</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <template v-for="c in subRows" :key="c.id">
        <tr>
          <td>
            <div class="sets-cell">
              <button class="btn tiny" @click="toggleSets(c.id)">{{ expanded[c.id] ? '-' : '+' }}</button>
              <span class="count-badge" :title="(setsByCat[c.id]||[]).length + ' sets'">{{ (setsByCat[c.id]||[]).length }}</span>
            </div>
          </td>
          <td>
            <template v-if="isEditing(c.id)"><input class="input" v-model="editBuffer[c.id].name" /></template>
            <template v-else>{{ c.name }}</template>
          </td>
          <td>
            <template v-if="isEditing(c.id)"><textarea class="input textarea" v-model="editBuffer[c.id].description"></textarea></template>
            <template v-else><div class="desc-clamp" :title="c.description">{{ c.description }}</div></template>
          </td>
          <td>
            <select class="input" v-model="c.parent_id">
              <option :value="''">None (Head)</option>
              <option v-for="h in headOptions(c.id)" :key="h.id" :value="h.id">{{ h.name }}</option>
            </select>
            <button class="btn tiny" @click="saveParent(c)">Save</button>
          </td>
          <td><input class="input" v-model="branding[keyOf(c.id)].icon" placeholder="e.g. 🔬" @input="touch(c.id)" /></td>
          <td>
            <div class="col-stack">
              <input class="input" v-model="branding[keyOf(c.id)].icon_url" placeholder="https://.../icon.png" @input="touch(c.id)" />
              <div class="row-actions">
                <button class="btn tiny" @click="saveBranding(c.id)">Save Logo</button>
              </div>
            </div>
          </td>
          <td class="row-actions">
            <button class="btn tiny" @click="isEditing(c.id) ? saveMeta(c) : toggleEdit(c)">{{ isEditing(c.id) ? 'Save Meta' : 'Edit' }}</button>
            <button class="btn tiny secondary" v-if="isEditing(c.id)" @click="cancelEdit(c.id)">Cancel</button>
            <a class="btn tiny secondary" :href="publicLink(c)" target="_blank">View</a>
            <button class="btn tiny secondary" @click="remove(c.id)">Delete</button>
          </td>
        </tr>
        <tr v-if="expanded[c.id]" class="expanded-row">
          <td></td>
          <td colspan="5">
            <div class="sets-panel">
              <div class="sets-panel-head">
                <strong>Sets for {{ c.name }}</strong>
                <input class="input small" type="text" placeholder="Search sets…" v-model="search[keyOf(c.id)]" />
              </div>
              <div v-if="filterSets(c.id).length === 0" class="empty">No sets</div>
              <ul class="sets-list inline">
                <li v-for="s in paginatedSets(c.id)" :key="s.id" class="set-item">
                  <div>
                    <div class="set-title">{{ s.title }}</div>
                    <div class="set-meta">Durasi: {{ s.time_limit_minutes }} menit</div>
                  </div>
                  <div style="display:flex; gap:8px;">
                    <router-link class="btn tiny" :to="{ path: `/admin/sets/${s.id}` }">Edit</router-link>
                    <button class="btn tiny secondary" @click="deleteSet(s.id, c.id)">Delete</button>
                  </div>
                </li>
              </ul>
              <div class="pagination" v-if="pageCount(c.id) > 1">
                <button class="btn tiny secondary" :disabled="(pageByCat[c.id]||1) <= 1" @click="setPage(c.id, (pageByCat[c.id]||1)-1)">Prev</button>
                <span>Page {{ pageByCat[c.id] || 1 }} / {{ pageCount(c.id) }}</span>
                <button class="btn tiny" :disabled="(pageByCat[c.id]||1) >= pageCount(c.id)" @click="setPage(c.id, (pageByCat[c.id]||1)+1)">Next</button>
              </div>
            </div>
          </td>
          <td></td>
        </tr>
        </template>
      </tbody>
    </table>
    <!-- close sub-section -->
  </div>
  </div>
  <!-- close .card -->
</template>
<script setup>
import { onMounted, ref, computed } from 'vue'
import api from '../../api/client'
const categories = ref([])
const form = ref({ name: '', description: '' })
const setsByCat = ref({})
const branding = ref({})
const search = ref({})
const heads = ref([])
const headCats = computed(() => (categories.value || []).filter(c => !c.parent_id))
const subCats = computed(() => (categories.value || []).filter(c => !!c.parent_id))
const editing = ref({})
const editBuffer = ref({})
const expanded = ref({})
// section filters
const headSearch = ref('')
const headSort = ref('new_old')
const subSearch = ref('')
const subParentFilter = ref(null)
const subSort = ref('new_old')

const headRows = computed(() => {
  let arr = headCats.value
  const q = (headSearch.value || '').toLowerCase().trim()
  if (q) arr = arr.filter(c => String(c.name||'').toLowerCase().includes(q) || String(c.description||'').toLowerCase().includes(q))
  let by
  if (headSort.value === 'name_desc'){
    by = (a,b)=>String(b.name||'').localeCompare(String(a.name||''))
  } else if (headSort.value === 'new_old'){
    by = (a,b)=> Number(b.id) - Number(a.id)
  } else if (headSort.value === 'old_new'){
    by = (a,b)=> Number(a.id) - Number(b.id)
  } else {
    by = (a,b)=>String(a.name||'').localeCompare(String(b.name||''))
  }
  return [...arr].sort(by)
})

const subRows = computed(() => {
  let arr = subCats.value
  if (subParentFilter.value){ arr = arr.filter(c => c.parent_id === subParentFilter.value) }
  const q = (subSearch.value || '').toLowerCase().trim()
  if (q) arr = arr.filter(c => String(c.name||'').toLowerCase().includes(q) || String(c.description||'').toLowerCase().includes(q))
  let by
  if (subSort.value === 'name_desc'){
    by = (a,b)=>String(b.name||'').localeCompare(String(a.name||''))
  } else if (subSort.value === 'new_old'){
    // Assume larger id == newer
    by = (a,b)=> Number(b.id) - Number(a.id)
  } else if (subSort.value === 'old_new'){
    by = (a,b)=> Number(a.id) - Number(b.id)
  } else {
    by = (a,b)=>String(a.name||'').localeCompare(String(b.name||''))
  }
  return [...arr].sort(by)
})

async function load(){
  const { data: cats } = await api.get('/categories/')
  const { data: hd } = await api.get('/categories/heads')
  heads.value = hd
  // load saved branding first
  let saved = {}
  try { saved = JSON.parse(localStorage.getItem('category_branding')||'{}') } catch {}
  // build branding with string keys before rendering categories
  const newBranding = {}
  for (const c of cats){
    const k = String(c.id)
    newBranding[k] = { icon: '', icon_url: '', ...(branding.value[k]||{}), ...(saved[k]||{}) }
    const { data: sets } = await api.get('/sets/', { params: { category_id: c.id } })
    setsByCat.value[c.id] = sets
    if (!search.value[k]) search.value[k] = ''
  }
  branding.value = newBranding
  categories.value = cats
}

function isEditing(id){ return !!editing.value[id] }
function toggleEdit(c){
  const id = c.id
  if (!editing.value[id]){
    editing.value = { ...editing.value, [id]: true }
    editBuffer.value = { ...editBuffer.value, [id]: { name: c.name, description: c.description } }
  } else {
    editing.value = { ...editing.value, [id]: false }
  }
}
function cancelEdit(id){
  editing.value = { ...editing.value, [id]: false }
}
async function saveMeta(c){
  const buf = editBuffer.value[c.id] || {}
  await api.put(`/categories/${c.id}`, { name: buf.name, description: buf.description })
  editing.value = { ...editing.value, [c.id]: false }
  await load()
}

onMounted(load)

async function add(){
  await api.post('/categories/', form.value)
  form.value = { name: '', description: '' }
  await load()
}

async function remove(id){
  await api.delete(`/categories/${id}`)
  await load()
}

async function deleteSet(setId, categoryId){
  await api.delete(`/sets/${setId}`)
  const { data: sets } = await api.get('/sets/', { params: { category_id: categoryId } })
  setsByCat.value[categoryId] = sets
}

function keyOf(id){ return String(id) }
function touch(id){ /* mark dirty in future if needed */ }
function saveBranding(id){
  const store = JSON.parse(localStorage.getItem('category_branding')||'{}')
  const k = keyOf(id)
  store[k] = branding.value[k]
  localStorage.setItem('category_branding', JSON.stringify(store))
}
function resetBranding(id){
  const k = keyOf(id)
  branding.value[k] = { icon: '', icon_url: '' }
  saveBranding(k)
}

function headOptions(currentId){
  // disallow selecting itself as parent
  return heads.value.filter(h => h.id !== currentId)
}
function nameById(id){
  return (categories.value.find(x=>x.id===id)||{}).name || (heads.value.find(x=>x.id===id)||{}).name
}
function childCount(id){
  return (categories.value || []).filter(x => x.parent_id === id).length
}
async function saveParent(c){
  // When parent changed to null, ensure it's sent as null not 0/""
  const val = c.parent_id
  const parent_id = (val === '' || val === undefined) ? null : Number(val)
  const payload = { parent_id }
  await api.put(`/categories/${c.id}`, payload)
  await load()
}

async function saveBanner(c){
  await api.put(`/categories/${c.id}`, { banner_url: c.banner_url || null })
  await load()
}

function publicLink(c){
  if (!c.parent_id) return `/categories/${c.id}`
  return `/categories/${c.parent_id}/${c.id}`
}

function filterSets(catId){
  const list = setsByCat.value[catId] || []
  const q = (search.value[keyOf(catId)] || '').toLowerCase().trim()
  if (!q) return list
  return list.filter(s => String(s.title || '').toLowerCase().includes(q))
}

// ---------- Expand/Collapse & Pagination for Sub Category sets ----------
const pageByCat = ref({})
const pageSize = 6

function toggleSets(id){
  expanded.value = { ...expanded.value, [id]: !expanded.value[id] }
  if (expanded.value[id] && !pageByCat.value[id]) pageByCat.value = { ...pageByCat.value, [id]: 1 }
}
function expandAllSub(){
  const obj = {}
  for (const sc of subCats.value){ obj[sc.id] = true }
  expanded.value = obj
}
function collapseAllSub(){ expanded.value = {} }

function pageCount(id){
  const total = filterSets(id).length
  return Math.max(1, Math.ceil(total / pageSize))
}
function setPage(id, page){
  const max = pageCount(id)
  const p = Math.min(Math.max(1, page), max)
  pageByCat.value = { ...pageByCat.value, [id]: p }
}
function paginatedSets(id){
  const list = filterSets(id)
  const p = pageByCat.value[id] || 1
  const start = (p - 1) * pageSize
  return list.slice(start, start + pageSize)
}
</script>

<style scoped>
.view-toggle{ display:flex; justify-content:flex-end; margin-bottom:8px; }
.cat-table{ width:100%; border-collapse:separate; border-spacing:0; margin-top:8px; table-layout: fixed; }
.cat-table thead th{ position:sticky; top:0; z-index:1; background:#fff; border-bottom:2px solid #e2e8f0; }
.cat-table th, .cat-table td{ border-right:1px solid #e5e7eb; border-bottom:1px solid #e5e7eb; padding:8px 10px; vertical-align:top; overflow:hidden; text-overflow:ellipsis; word-break:break-word; overflow-wrap:anywhere; }
.cat-table th:first-child, .cat-table td:first-child{ border-left:1px solid #e5e7eb; }
.cat-table tbody tr:nth-child(odd){ background:#fafafa; }
.expanded-row td{ background:#f8fafc; }
.row-actions{ display:flex; flex-wrap:wrap; gap:6px; }
.row-actions .btn{ white-space:nowrap; }
.input{ max-width:100%; box-sizing:border-box; }
.textarea{ max-width:100%; box-sizing:border-box; }
.desc-clamp{ display:-webkit-box; -webkit-box-orient:vertical; -webkit-line-clamp:2; overflow:hidden; }
.col-stack{ display:flex; flex-direction:column; gap:6px; }
.sets-panel{ background:#f1f5f9; border:1px dashed #93c5fd; border-radius:8px; padding:10px; }
.sets-panel-head{ display:flex; justify-content:space-between; align-items:center; gap:8px; margin-bottom:8px; }
.sets-list.inline{ max-height:260px; overflow:auto; padding-right:6px; }
.sets-cell{ display:flex; align-items:center; gap:6px; }
.count-badge{ display:inline-flex; align-items:center; justify-content:center; min-width:20px; height:20px; padding:0 6px; border-radius:999px; font-size:12px; background:#e0f2fe; color:#075985; font-weight:700; }
.pagination{ display:flex; align-items:center; gap:8px; margin-top:8px; }

/* Sections */
.section{ border:1px solid #e2e8f0; border-radius:10px; padding:10px; margin-top:12px; background:#fff; }
.head-section{ box-shadow: inset 0 0 0 2px #e0e7ff; }
.sub-section{ box-shadow: inset 0 0 0 2px #dcfce7; }
.section-title{ display:flex; align-items:center; gap:8px; margin:0 0 6px; font-weight:800; color:#0f172a; }
.section-title.with-actions{ justify-content:space-between; }
.section-toolbar{ display:flex; gap:8px; align-items:center; margin:8px 0; }
.new-cat { display:grid; grid-template-columns: 1fr 2fr auto; gap:12px; align-items:end; }
.cat-card { background:white; border-radius:12px; padding:12px; box-shadow:0 2px 10px rgba(0,0,0,0.06); display:flex; flex-direction:column; gap:12px; }
.cat-header { display:flex; justify-content:space-between; align-items:flex-start; gap:12px; }
.cat-title { font-weight:800; color:#0f172a; }
.cat-desc { color:#475569; overflow:hidden; display:-webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 5; /* number of lines to show */ }
.parent-row{ display:grid; grid-template-columns: 100px 1fr; gap:8px; align-items:center; }
.parent-actions{ display:flex; gap:8px; align-items:center; }
.hint{ color:#64748b; font-size:12px; }
.sets { display:flex; flex-direction:column; gap:8px; }
.sets-title { font-weight:700; }
.set-item { display:flex; justify-content:space-between; align-items:center; padding:8px 0; border-bottom:1px solid #e2e8f0; }
.set-title { font-weight:600; }
.set-meta { color:#64748b; font-size:14px; }
.empty { color:#94a3b8; font-style:italic; }

.branding{ background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:10px; display:flex; flex-direction:column; gap:8px; }
.branding-title{ font-weight:700; margin-bottom:4px; }
.branding-row{ display:grid; grid-template-columns: 100px 1fr; gap:8px; align-items:center; }
.branding-actions{ display:flex; gap:8px; }

/* Shorter sets panel: show ~3 items with scroll for more */
.sets-list{ max-height: 210px; overflow:auto; padding-right:6px; }
.btn.tiny{ padding:4px 8px; font-size:12px; }
</style>
