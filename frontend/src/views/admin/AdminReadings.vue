<template>
  <AdminLayout>
    <template #title>Readings</template>
    <div class="card">
      <h2 style="margin-top:0">Readings</h2>
      <div class="toolbar">
        <input class="input" v-model="q" placeholder="Search by title" />
        <button class="btn" @click="openNew">+ New</button>
      </div>

      <table class="table">
        <thead>
          <tr>
            <th style="width:90px;">ID</th>
            <th>Title</th>
            <th style="width:180px;">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in rows" :key="r.id">
            <td class="id-cell" @click="copyId(r.id)" title="Click to copy">
              <span class="id-badge">#{{ r.id }}</span>
              <span class="id-hint">Copy</span>
            </td>
            <td><strong>{{ r.title }}</strong></td>
            <td>
              <div class="actions">
                <button class="btn tiny action edit" @click="edit(r)">Edit</button>
                <button class="btn tiny action danger" @click="del(r.id)">Delete</button>
              </div>
            </td>
          </tr>
          <tr v-if="rows.length===0"><td colspan="3" class="muted">No readings found.</td></tr>
        </tbody>
      </table>

      <div class="import-card">
        <h3 style="margin:8px 0 6px;">Bulk Import</h3>
        <p class="muted">Upload an Excel (.xlsx) file with columns: <code>title, content_html</code>.</p>
        <div class="import-row">
          <input ref="fileInput" type="file" accept=".xlsx" @change="onFileChange" />
          <button class="btn" :disabled="!xlsxFile || importing" @click="doImport">{{ importing ? 'Importing…' : 'Import' }}</button>
          <button class="btn secondary" @click="downloadTemplate">Download template</button>
        </div>
        <div v-if="importResult" class="import-result">
          <div><strong>Created:</strong> {{ importResult.created }}</div>
          <div v-if="(importResult.errors||[]).length"><strong>Errors:</strong>
            <ul>
              <li v-for="(e,i) in importResult.errors" :key="i">{{ e }}</li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <div v-if="show" class="modal-overlay" @click.self="close">
      <div class="modal">
        <div class="modal-head">{{ form.id ? 'Edit Reading' : 'New Reading' }}</div>
        <div class="modal-body">
          <div class="form-grid">
            <div class="row full">
              <label>Title</label>
              <input class="input" v-model="form.title" />
            </div>
            <div class="row full">
              <label>Content</label>
              <RichTextEditor v-model="form.content_html" placeholder="Paste or write the reading passage here..." />
            </div>
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn" @click="save">Save</button>
          <button class="btn secondary" @click="close">Cancel</button>
        </div>
      </div>
    </div>
  </AdminLayout>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import AdminLayout from '../../components/admin/AdminLayout.vue'
import RichTextEditor from '../../components/RichTextEditor.vue'
import api from '../../api/client'

const q = ref('')
const rows = ref([])
const xlsxFile = ref(null)
const importing = ref(false)
const importResult = ref(null)

const show = ref(false)
const form = ref({ id:null, title:'', content_html:'', category_id:null })

async function load(){
  await refresh()
}

function onFileChange(e){
  importResult.value = null
  xlsxFile.value = e.target.files?.[0] || null
}
async function doImport(){
  if (!xlsxFile.value) return
  importing.value = true
  try{
    const fd = new FormData()
    fd.append('file', xlsxFile.value)
    const { data } = await api.post('/readings/import-xlsx', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    importResult.value = data
    await refresh()
  }catch(e){
    importResult.value = { created: 0, errors: [ e?.response?.data?.detail || e.message || 'Import failed' ] }
  }finally{
    importing.value = false
  }
}
async function downloadTemplate(){
  try{
    const { data } = await api.get('/readings/import-template.xlsx', { responseType: 'blob' })
    const blob = new Blob([data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'readings-import-template.xlsx'
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  }catch{
    window.open('/api/v1/readings/import-template.xlsx', '_blank', 'noopener')
  }
}
async function refresh(){
  const params = {}
  if (q.value) params.q = q.value
  const { data } = await api.get('/readings/', { params })
  rows.value = data
}

function openNew(){ form.value = { id:null, title:'', content_html:'', category_id:null }; show.value = true }
function edit(r){ form.value = { id:r.id, title:r.title, content_html:r.content_html, category_id:r.category_id || null }; show.value = true }
function close(){ show.value = false }

async function save(){
  const payload = { title: form.value.title, content_html: form.value.content_html }
  if (form.value.category_id) payload.category_id = form.value.category_id
  if (form.value.id){
    await api.put(`/readings/${form.value.id}`, payload)
  } else {
    await api.post('/readings/', payload)
  }
  show.value = false
  await refresh()
}
async function del(id){
  if (!confirm('Delete this reading?')) return
  await api.delete(`/readings/${id}`)
  await refresh()
}

async function copyId(id){
  try{
    await navigator.clipboard.writeText(String(id))
  }catch{
    const ta = document.createElement('textarea')
    ta.value = String(id)
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    ta.remove()
  }
}

onMounted(load)
</script>
<style scoped>
.toolbar{ display:flex; gap:8px; align-items:center; margin:8px 0; }
.table{ width:100%; border-collapse:separate; border-spacing:0; }
.table thead th{ position:sticky; top:0; background:#fff; border-bottom:2px solid #e2e8f0; text-align:left; padding:8px 10px; }
.table td{ border-bottom:1px solid #e2e8f0; padding:8px 10px; }
.muted{ color:#64748b; }
.import-card{ margin-top:18px; padding:12px; border:1px solid #e2e8f0; border-radius:10px; background:#fff; }
.import-row{ display:flex; gap:8px; align-items:center; margin-top:8px; }
.import-result{ margin-top:8px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:8px; }
.modal-overlay{ position:fixed; inset:0; background: rgba(2,6,23,0.55); display:flex; align-items:center; justify-content:center; z-index: 1000; padding: 16px; }
.modal{ width:100%; max-width:820px; background:#fff; border:1px solid #e2e8f0; border-radius:14px; box-shadow: 0 20px 40px rgba(2,6,23,0.18); overflow:hidden; }
.modal-head{ font-weight:800; font-size:18px; padding:16px; border-bottom:1px solid #e2e8f0; color:#0f172a; }
.modal-body{ padding:16px; color:#334155; }
.modal-actions{ padding:12px 16px 16px; display:flex; gap:8px; justify-content:flex-end; }
.form-grid{ display:grid; grid-template-columns: repeat(2, 1fr); gap:12px; }
.form-grid .row{ display:flex; flex-direction:column; gap:6px; }
.form-grid .row.full{ grid-column: 1 / -1; }
/* Actions styling */
.actions{ display:flex; align-items:center; gap:8px; justify-content:flex-end; }
.btn.tiny.action{ padding:4px 10px; border-radius:8px; border:1px solid transparent; font-weight:700; }
.btn.tiny.action.edit{ background: linear-gradient(90deg, #2563eb, #4f46e5); color:#fff; border-color:#3b82f6; box-shadow: 0 4px 12px rgba(37,99,235,0.25); }
.btn.tiny.action.edit:hover{ filter: brightness(1.03); }
.btn.tiny.action.danger{ background:#fee2e2; color:#991b1b; border-color:#fecaca; }
.btn.tiny.action.danger:hover{ background:#fecaca; }
.id-cell{ display:flex; align-items:center; gap:6px; cursor:pointer; user-select:none; }
.id-badge{ display:inline-block; padding:2px 6px; background:#f1f5f9; border:1px solid #e2e8f0; border-radius:6px; font-size:12px; color:#334155; }
.id-hint{ font-size:12px; color:#64748b; }
</style>
