<template>
  <div class="card">
    <h2>Categories</h2>
    <form class="new-cat" @submit.prevent="add">
      <input v-model="form.name" placeholder="Name" class="input" required />
      <input v-model="form.description" placeholder="Description" class="input" />
      <button class="btn">Add Category</button>
    </form>

    <h3 style="margin-top:12px;">Head Categories</h3>
    <div class="grid cols-3" style="margin-top:8px;">
      <div v-for="c in headCats" :key="c.id" class="cat-card">
        <div class="cat-header">
          <div class="meta-block">
            <template v-if="isEditing(c.id)">
              <input class="input" v-model="editBuffer[c.id].name" placeholder="Category name" />
              <textarea class="input textarea" v-model="editBuffer[c.id].description" placeholder="Description"></textarea>
              <div class="edit-actions">
                <button class="btn" @click="saveMeta(c)">Save</button>
                <button class="btn secondary" @click="cancelEdit(c.id)">Cancel</button>
              </div>
            </template>
            <template v-else>
              <div class="cat-title">{{ c.name }}</div>
              <div class="cat-desc" :title="c.description">{{ c.description }}</div>
            </template>
          </div>
          <div class="right-actions">
            <button class="btn secondary" @click="remove(c.id)">Delete</button>
            <button class="btn" @click="toggleEdit(c)">{{ isEditing(c.id) ? 'Editing…' : 'Edit' }}</button>
          </div>
        </div>
        <div class="parent-row">
          <label class="lbl">Parent</label>
          <div class="parent-actions">
            <select class="input" v-model="c.parent_id">
              <option :value="''">None (Head)</option>
              <option v-for="h in headOptions(c.id)" :key="h.id" :value="h.id">{{ h.name }}</option>
            </select>
            <button class="btn" @click="saveParent(c)">Save Parent</button>
            <span class="hint">{{ c.parent_id ? 'Sub of '+(nameById(c.parent_id)||c.parent_id) : 'Head Category' }}</span>
            <a class="btn secondary" :href="publicLink(c)" target="_blank">View public</a>
          </div>
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
          <div class="branding-row">
            <label class="lbl">Banner URL</label>
            <input class="input" placeholder="https://.../banner.jpg or /uploads/..." v-model="c.banner_url" />
          </div>
          <div class="branding-actions">
            <button class="btn" @click="saveBanner(c)">Save Banner</button>
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

    <h3 style="margin-top:16px;">Sub Categories</h3>
    <div class="grid cols-3" style="margin-top:8px;">
      <div v-for="c in subCats" :key="c.id" class="cat-card">
        <div class="cat-header">
          <div class="meta-block">
            <template v-if="isEditing(c.id)">
              <input class="input" v-model="editBuffer[c.id].name" placeholder="Sub category name" />
              <textarea class="input textarea" v-model="editBuffer[c.id].description" placeholder="Description"></textarea>
              <div class="edit-actions">
                <button class="btn" @click="saveMeta(c)">Save</button>
                <button class="btn secondary" @click="cancelEdit(c.id)">Cancel</button>
              </div>
            </template>
            <template v-else>
              <div class="cat-title">{{ c.name }}</div>
              <div class="cat-desc" :title="c.description">{{ c.description }}</div>
            </template>
          </div>
          <div class="right-actions">
            <button class="btn secondary" @click="remove(c.id)">Delete</button>
            <button class="btn" @click="toggleEdit(c)">{{ isEditing(c.id) ? 'Editing…' : 'Edit' }}</button>
          </div>
        </div>
        <div class="parent-row">
          <label class="lbl">Parent</label>
          <div class="parent-actions">
            <select class="input" v-model="c.parent_id">
              <option :value="''">None (Head)</option>
              <option v-for="h in headOptions(c.id)" :key="h.id" :value="h.id">{{ h.name }}</option>
            </select>
            <button class="btn" @click="saveParent(c)">Save Parent</button>
            <span class="hint">{{ c.parent_id ? 'Sub of '+(nameById(c.parent_id)||c.parent_id) : 'Head Category' }}</span>
          </div>
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
</script>

<style scoped>
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
</style>
