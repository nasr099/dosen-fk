<template>
  <AdminLayout>
    <template #title>Team</template>
    <div class="card">
    <h2 style="margin-top:0">Team Page</h2>
    <p class="muted">Manage team members displayed on the public Team page.</p>

    <form class="new" @submit.prevent="add">
      <input v-model="form.name" class="input" placeholder="Name" required />
      <input v-model="form.role" class="input" placeholder="Role" required />
      <textarea v-model="form.headline" class="input" placeholder="Headline (supports HTML)"></textarea>
      <textarea v-model="form.quote" class="input" placeholder="Quote (supports HTML)"></textarea>
      <CdnUploader v-model="form.photo_url" />
      <input v-model="form.linkedin" class="input" placeholder="LinkedIn URL" />
      <input v-model="form.twitter" class="input" placeholder="Twitter/X URL" />
      <input v-model="form.website" class="input" placeholder="Website" />
      <label class="toggle"><input type="checkbox" v-model="form.is_visible"/> Visible</label>
      <button class="btn">Add Member</button>
    </form>

    <div class="list">
      <div
        v-for="(m,i) in members"
        :key="m.id"
        class="row"
        draggable="true"
        @dragstart="dragStart(i)"
        @dragover.prevent
        @drop="drop(i)"
      >
        <div class="left">
          <img :src="resolveImg(m.photo_url)" v-if="m.photo_url" class="avatar"/>
          <div v-else class="avatar placeholder">{{ initials(m.name) }}</div>
          <div class="info">
            <div class="name">{{ m.name }}</div>
            <div class="role">{{ m.role }}</div>
            <div class="headline" v-html="m.headline"></div>
          </div>
        </div>
        <div class="actions">
          <label class="toggle"><input type="checkbox" :checked="m.is_visible" @change="toggleVisible(m)"/> Show</label>
          <button class="btn" @click="edit(i)">Edit</button>
          <button class="btn secondary" @click="remove(m.id)">Delete</button>
        </div>
      </div>
      <div v-if="members.length===0" class="empty">No team members yet.</div>
    </div>

    <div class="row-actions" v-if="members.length>1">
      <button class="btn" @click="saveOrder">Save Order</button>
    </div>

    <div v-if="editingIndex!==null" class="modal">
      <div class="modal-card">
        <h3>Edit Member</h3>
        <form @submit.prevent="saveEdit">
          <input v-model="editForm.name" class="input" placeholder="Name" required />
          <input v-model="editForm.role" class="input" placeholder="Role" required />
          <textarea v-model="editForm.headline" class="input" placeholder="Headline (supports HTML)"></textarea>
          <textarea v-model="editForm.quote" class="input" placeholder="Quote (supports HTML)"></textarea>
          <CdnUploader v-model="editForm.photo_url" />
          <input v-model="editForm.linkedin" class="input" placeholder="LinkedIn URL" />
          <input v-model="editForm.twitter" class="input" placeholder="Twitter/X URL" />
          <input v-model="editForm.website" class="input" placeholder="Website" />
          <label class="toggle"><input type="checkbox" v-model="editForm.is_visible"/> Visible</label>
          <div class="row-actions">
            <button class="btn" type="submit">Save</button>
            <button class="btn secondary" type="button" @click="cancelEdit">Cancel</button>
          </div>
        </form>
      </div>
    </div>
  </div>
  </AdminLayout>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import AdminLayout from '../../components/admin/AdminLayout.vue'
import api from '../../api/client'
import CdnUploader from '../../components/CdnUploader.vue'

const members = ref([])
const form = ref({ name:'', role:'', headline:'', quote:'', photo_url:'', linkedin:'', twitter:'', website:'', is_visible:true })
const editingIndex = ref(null)
const editForm = ref({})
let dragIndex = -1

onMounted(load)

async function load(){
  const { data } = await api.get('/team/all')
  members.value = data
}

async function add(){
  const { data } = await api.post('/team/', form.value)
  members.value.push(data)
  form.value = { name:'', role:'', headline:'', quote:'', photo_url:'', linkedin:'', twitter:'', website:'', is_visible:true }
}
async function remove(id){
  await api.delete(`/team/${id}`)
  members.value = members.value.filter(x => x.id !== id)
}
function edit(i){ editingIndex.value = i; editForm.value = { ...members.value[i] } }
async function saveEdit(){
  const id = editForm.value.id
  const { data } = await api.put(`/team/${id}`, editForm.value)
  members.value[editingIndex.value] = data
  editingIndex.value = null
}
function cancelEdit(){ editingIndex.value = null }

function dragStart(i){ dragIndex = i }
function drop(i){
  if (dragIndex === -1) return
  const tmp = members.value[dragIndex]
  members.value.splice(dragIndex,1)
  members.value.splice(i,0,tmp)
  dragIndex = -1
}
async function saveOrder(){
  const ids = members.value.map(m => m.id)
  await api.post('/team/reorder', { ids })
  await load()
}
async function toggleVisible(m){
  const { data } = await api.put(`/team/${m.id}`, { is_visible: !m.is_visible })
  m.is_visible = data.is_visible
}

// File upload handled by CdnUploader

function resolveImg(src){
  if (!src) return ''
  const s = String(src)
  if (/^https?:\/\//i.test(s) || s.startsWith('data:image')) return s
  const path = s.startsWith('/') ? s : `/${s}`
  if (path.startsWith('/uploads/')) return `${window.location.origin.replace('5173','8000')}${path}`
  return path
}
function initials(name){ return (name||'').split(' ').map(x=>x[0]).slice(0,2).join('').toUpperCase() }
</script>
<style scoped>
.muted{ color:#64748b }
.new{ display:grid; grid-template-columns: repeat(3, 1fr); gap:10px; align-items:end; margin-top:8px }
.upload-row{ display:grid; grid-template-columns: 1fr auto; gap:8px }
.list{ margin-top:16px; display:flex; flex-direction:column; gap:8px }
.row{ display:flex; justify-content:space-between; align-items:center; border:1px solid #e2e8f0; border-radius:10px; padding:8px 10px; background:white }
.left{ display:flex; align-items:center; gap:10px }
.avatar{ width:48px; height:48px; border-radius:999px; object-fit:cover }
.avatar.placeholder{ background:#e2e8f0; color:#334155; font-weight:800; display:flex; align-items:center; justify-content:center }
.info .name{ font-weight:700 }
.info .role{ color:#475569 }
.toggle{ display:inline-flex; align-items:center; gap:6px; font-size:14px; }
.modal{ position:fixed; inset:0; background:rgba(0,0,0,0.5); display:flex; align-items:center; justify-content:center; z-index:1000 }
.modal-card{ background:white; border-radius:12px; padding:16px; width:min(680px, 92vw); box-shadow: 0 10px 24px rgba(2,6,23,0.3) }
.row-actions{ display:flex; gap:8px; margin-top:10px }
@media (max-width: 900px){ .new{ grid-template-columns: 1fr } }
</style>
