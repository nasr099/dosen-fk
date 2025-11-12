<template>
  <AdminLayout>
    <template #title>Tryouts</template>
    <!-- Separate section: Add Category -->
    <div class="card">
      <h2 style="margin-top:0">Add Tryout Category</h2>
      <div class="cat-add">
        <label>Add New Category</label>
        <div class="cat-add-row">
          <input v-model="newTryoutCat" class="input" placeholder="e.g., CBT Simulation, Full Tryout, Mini Tryout" />
          <button class="btn" type="button" @click="createTryoutCategory" :disabled="!newTryoutCat.trim()">Add</button>
        </div>
      </div>

      <div class="cat-list" v-if="tryoutCatsFull.length">
        <table class="table small">
          <thead>
            <tr><th style="width:60%">Category</th><th style="width:40%; text-align:right;">Actions</th></tr>
          </thead>
          <tbody>
            <tr v-for="c in tryoutCatsFull" :key="c.id">
              <td>
                <template v-if="editCatId===c.id">
                  <input v-model="editCatName" class="input" />
                </template>
                <template v-else>{{ c.name }}</template>
              </td>
              <td style="text-align:right;">
                <template v-if="editCatId===c.id">
                  <button class="btn tiny" @click="saveCatEdit(c)">Save</button>
                  <button class="btn tiny secondary" @click="cancelCatEdit">Cancel</button>
                </template>
                <template v-else>
                  <button class="btn tiny" @click="beginCatEdit(c)">Edit</button>
                  <button class="btn tiny secondary" @click="removeCat(c)">Delete</button>
                </template>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="card" style="margin-top: 12px;">
      <h2 style="margin-top:0">Create/Edit Tryout</h2>

      <div class="form-grid">
        <div class="row full"><label>Title</label><input v-model="form.title" class="input" /></div>
        <div class="row full"><label>Description</label><RichTextEditor v-model="form.description" placeholder="Write a rich description..." /></div>
        <div class="row">
          <label>Tryout Category</label>
          <select v-model="form.category" class="input">
            <option value="">-- Select a category --</option>
            <option v-for="c in tryoutCategories" :key="c" :value="c">{{ c }}</option>
          </select>
        </div>
        <div class="row"><label><input type="checkbox" v-model="form.is_active" /> Active</label></div>
      </div>

      <div class="sets-builder">
        <div class="sb-head">
          <strong>Sets in this Tryout</strong>
          <button class="btn secondary" @click="addSet">+ Add set</button>
        </div>
        <div class="note">Only sets with “Available for tryouts” enabled are listed.</div>
        <div class="sb-item" v-for="(s,i) in form.sets" :key="i">
          <div class="sb-row">
            <label>Order</label>
            <input type="number" class="input small" v-model.number="s.order_index" min="1" />
          </div>
          <div class="sb-row grow">
            <label>Question Set</label>
            <select v-model.number="s.question_set_id" class="input">
              <option :value="0" disabled>Select set</option>
              <option v-for="opt in tryoutSets" :key="opt.id" :value="opt.id">{{ opt.title }} ({{ categoryName(opt.category_id) }})</option>
            </select>
          </div>
          <div class="sb-row">
            <label>Duration (min)</label>
            <input type="number" class="input small" v-model.number="s.duration_minutes" min="1" />
          </div>
          <div class="sb-row full">
            <label>Intermission text (shown during 60s break)</label>
            <RichTextEditor v-model="s.intermission_text" placeholder="Write intermission instructions..." />
          </div>
          <button class="btn tiny secondary" @click="removeSet(i)">Remove</button>
        </div>
      </div>

      <div style="display:flex; gap:8px; margin-top:12px;">
        <button class="btn" :disabled="!canSave" @click="save">Save Tryout</button>
        <button class="btn secondary" @click="reset">Reset</button>
      </div>

    </div>

    <!-- Existing Tryouts (separate section) -->
    <div class="card" style="margin-top: 16px;">
      <h2 style="margin-top:0">Existing Tryouts</h2>
      <table class="table">
        <thead>
          <tr><th>Title</th><th>Category</th><th>Status</th><th>Sets</th><th>Actions</th></tr>
        </thead>
        <tbody>
          <tr v-for="t in tryouts" :key="t.id">
            <td>{{ t.title }}</td>
            <td>{{ t.category || 'Uncategorized' }}</td>
            <td>{{ t.is_active ? 'Active' : 'Inactive' }}</td>
            <td>{{ (t.sets||[]).length || '-' }}</td>
            <td>
              <div style="display:flex; gap:6px; justify-content:flex-start;">
                <button class="btn tiny" @click="editTryout(t.id)">Edit</button>
                <button class="btn tiny secondary" @click="doToggleActive(t)">{{ t.is_active ? 'Deactivate' : 'Activate' }}</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </AdminLayout>
</template>
<script setup>
import { onMounted, ref, computed } from 'vue'
import AdminLayout from '../../components/admin/AdminLayout.vue'
import api from '../../api/client'
import RichTextEditor from '../../components/RichTextEditor.vue'

const categories = ref([])
const tryoutCategories = ref([]) // names only (for select)
const tryoutCatsFull = ref([])   // [{id,name}] for management
const newTryoutCat = ref('')
const editCatId = ref(null)
const editCatName = ref('')
const tryoutSets = ref([])
const tryouts = ref([])
const editingId = ref(null)

const form = ref({ title:'', description:'', category:'', is_active:true, sets: [] })

function addSet(){ form.value.sets.push({ order_index: form.value.sets.length+1, question_set_id: 0, duration_minutes: 60, intermission_text: '' }) }
function removeSet(i){ form.value.sets.splice(i,1) }

const canSave = computed(() => {
  if (!form.value.title) return false
  if (!(form.value.sets||[]).length) return false
  return form.value.sets.every(s => s.order_index>=1 && s.duration_minutes>=1 && s.question_set_id>0)
})

function categoryName(id){
  const c = categories.value.find(x => x.id === id)
  return c ? c.name : id
}

async function load(){
  const [{ data: cats }, { data: sets }, { data: ts }, { data: trCats }, { data: trCatsFull }] = await Promise.all([
    api.get('/categories/'),
    api.get('/sets/', { params: { allow_in_tryout: true } }),
    // include all statuses so inactive items appear in the admin list
    api.get('/tryouts/', { params: { include_all: 1, status: 'all' } }),
    api.get('/tryouts/categories'),
    api.get('/tryouts/categories/all')
  ])
  categories.value = cats
  tryoutSets.value = sets
  tryouts.value = ts
  tryoutCategories.value = Array.isArray(trCats) ? trCats : []
  tryoutCatsFull.value = Array.isArray(trCatsFull) ? trCatsFull : []
}

async function save(){
  const payload = JSON.parse(JSON.stringify(form.value))
  // sort server side by order_index anyway, but send as is
  if (editingId.value){
    await api.put(`/tryouts/${editingId.value}`, payload)
  } else {
    await api.post('/tryouts/', payload)
  }
  await load()
  reset()
}
function reset(){ form.value = { title:'', description:'', category:'', is_active:true, sets: [] }; editingId.value = null }

async function editTryout(id){
  const { data } = await api.get(`/tryouts/${id}`)
  editingId.value = data.id
  const sets = Array.isArray(data.sets) ? data.sets.slice().sort((a,b)=> (a.order_index||0)-(b.order_index||0)) : []
  form.value = {
    title: data.title || '',
    description: data.description || '',
    category: data.category || '',
    is_active: !!data.is_active,
    sets: sets.map(s => ({
      order_index: Number(s.order_index || 1),
      question_set_id: Number(s.question_set_id || 0),
      duration_minutes: Number(s.duration_minutes || 60),
      intermission_text: s.intermission_text || ''
    }))
  }
}

async function createTryoutCategory(){
  const name = (newTryoutCat.value || '').trim()
  if (!name) return
  try{
    const { data } = await api.post('/tryouts/categories', null, { params: { name } })
    if (data){
      if (!tryoutCategories.value.includes(data)) tryoutCategories.value.push(data)
      if (!tryoutCatsFull.value.find(x=>x.name===data)) tryoutCatsFull.value.push({ id: Math.random(), name: data })
      form.value.category = data
      newTryoutCat.value = ''
    }
  }catch(e){
    alert(e?.response?.data?.detail || 'Failed to create category')
  }
}

function beginCatEdit(c){ editCatId.value = c.id; editCatName.value = c.name }
function cancelCatEdit(){ editCatId.value = null; editCatName.value = '' }
async function saveCatEdit(c){
  const name = (editCatName.value||'').trim()
  if (!name) return
  try{
    const { data } = await api.put(`/tryouts/categories/${c.id}`, null, { params: { name } })
    // update local lists
    const row = tryoutCatsFull.value.find(x=>x.id===c.id); if (row) row.name = data
    const ix = tryoutCategories.value.indexOf(c.name); if (ix>=0) tryoutCategories.value.splice(ix,1,data)
    if (form.value.category === c.name) form.value.category = data
    cancelCatEdit()
  }catch(e){ alert(e?.response?.data?.detail || 'Failed to update category') }
}
async function removeCat(c){
  if (!confirm(`Delete category "${c.name}"?`)) return
  try{
    await api.delete(`/tryouts/categories/${c.id}`)
    tryoutCatsFull.value = tryoutCatsFull.value.filter(x=>x.id!==c.id)
    tryoutCategories.value = tryoutCategories.value.filter(x=>x!==c.name)
    if (form.value.category === c.name) form.value.category = ''
  }catch(e){ alert(e?.response?.data?.detail || 'Failed to delete category') }
}

async function doToggleActive(t){
  const to = !t.is_active
  const label = to ? 'activate' : 'deactivate'
  if (!confirm(`Do you want to ${label} "${t.title}"?`)) return
  try{
    await api.put(`/tryouts/${t.id}`, { is_active: to })
    await load()
  }catch(e){
    alert(e?.response?.data?.detail || 'Failed to update status')
  }
}

onMounted(load)
</script>
<style scoped>
.form-grid{ display:grid; grid-template-columns: repeat(2,1fr); gap:12px; }
.form-grid .row{ display:flex; flex-direction:column; gap:6px; }
.form-grid .row.full{ grid-column: 1 / -1; }
.cat-add{ margin: 8px 0 14px; }
.cat-add label{ display:block; font-weight:600; margin-bottom:6px; }
.cat-add-row{ display:flex; gap:10px; align-items:center; }
.cat-add-row .input{ flex:1; }
.cat-list{ margin-top: 12px; }
.table.small th,.table.small td{ padding:6px 10px; }
.sets-builder{ margin-top:12px; }
.sb-head{ display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; }
.note{ color:#64748b; font-size:13px; margin-bottom:8px; }
.sb-item{ border:1px solid #e2e8f0; border-radius:12px; padding:10px; background:#f8fafc; display:grid; grid-template-columns: 120px 1fr 160px auto; gap:8px; align-items:end; margin-bottom:10px; }
.sb-row{ display:flex; flex-direction:column; gap:6px; }
.sb-row.full{ grid-column: 1 / -1; }
.input.small{ max-width:110px; }
.table{ width:100%; border-collapse:separate; border-spacing:0; margin-top:10px; }
.table th{ text-align:left; padding:8px 10px; border-bottom:2px solid #e2e8f0; }
.table td{ padding:8px 10px; border-bottom:1px solid #e2e8f0; }
</style>
