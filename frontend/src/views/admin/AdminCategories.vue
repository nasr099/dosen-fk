<template>
  <div class="card">
    <h2>Categories</h2>
    <form class="new-cat" @submit.prevent="add">
      <input v-model="form.name" placeholder="Name" class="input" required />
      <input v-model="form.description" placeholder="Description" class="input" />
      <button class="btn">Add Category</button>
    </form>

    <div class="grid cols-3" style="margin-top:16px;">
      <div v-for="c in categories" :key="c.id" class="cat-card">
        <div class="cat-header">
          <div>
            <div class="cat-title">{{ c.name }}</div>
            <div class="cat-desc" :title="c.description">{{ c.description }}</div>
          </div>
          <button class="btn secondary" @click="remove(c.id)">Delete</button>
        </div>
        <div class="branding" v-if="branding[keyOf(c.id)]">
          <div class="branding-title">Logo</div>
          <div class="branding-row">
            <label class="lbl">Emoji</label>
            <input class="input" placeholder="e.g. 🔬" v-model="branding[keyOf(c.id)].icon" @input="touch(c.id)" />
          </div>
          <div class="branding-row">
            <label class="lbl">Image URL</label>
            <input class="input" placeholder="https://.../icon.png or /uploads/.." v-model="branding[keyOf(c.id)].icon_url" @input="touch(c.id)" />
          </div>
          <div class="branding-actions">
            <button class="btn" @click="saveBranding(c.id)">Save Logo</button>
            <button class="btn secondary" @click="resetBranding(c.id)">Reset</button>
          </div>
        </div>
        <div class="sets">
          <div class="sets-title">Sets</div>
          <input class="input small" type="text" placeholder="Search sets…" v-model="search[keyOf(c.id)]" />
          <div v-if="filterSets(c.id).length === 0" class="empty">No sets</div>
          <ul class="sets-list">
            <li v-for="s in filterSets(c.id)" :key="s.id" class="set-item">
              <div>
                <div class="set-title">{{ s.title }}</div>
                <div class="set-meta">Durasi: {{ s.time_limit_minutes }} menit</div>
              </div>
              <div style="display:flex; gap:8px;">
                <router-link class="btn" :to="{ path: `/admin/sets/${s.id}` }">Edit</router-link>
                <button class="btn secondary" @click="deleteSet(s.id, c.id)">Delete</button>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import api from '../../api/client'
const categories = ref([])
const form = ref({ name: '', description: '' })
const setsByCat = ref({})
const branding = ref({})
const search = ref({})

async function load(){
  const { data: cats } = await api.get('/categories/')
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

function filterSets(catId){
  const list = setsByCat.value[catId] || []
  const q = (search.value[keyOf(catId)] || '').toLowerCase().trim()
  if (!q) return list
  return list.filter(s => String(s.title || '').toLowerCase().includes(q))
}
</script>

<style scoped>
.new-cat { display:grid; grid-template-columns: 1fr 2fr auto; gap:12px; align-items:end; }
.cat-card { background:white; border-radius:12px; padding:12px; box-shadow:0 2px 10px rgba(0,0,0,0.06); display:flex; flex-direction:column; gap:12px; }
.cat-header { display:flex; justify-content:space-between; align-items:flex-start; gap:12px; }
.cat-title { font-weight:800; color:#0f172a; }
.cat-desc { color:#475569; overflow:hidden; display:-webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 5; /* number of lines to show */ }
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
</style>
