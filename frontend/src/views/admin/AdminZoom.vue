<template>
  <AdminLayout>
    <template #title>Zoom Discussions</template>
    <div class="card">
    <h2 style="margin-top:0">Zoom Discussions</h2>
    <form class="toolbar" @submit.prevent>
      <input class="input" v-model="search" placeholder="Cari judul / presenter..." />
      <select class="input" v-model="filterMode">
        <option value="all">Semua</option>
        <option value="up">Upcoming</option>
        <option value="done">Finished</option>
      </select>
      <button class="btn" @click="openNew()">Tambah</button>
    </form>

    <div class="grid cols-4" style="gap:12px;">
      <div v-for="z in paged" :key="z.id" class="zoom-card">
        <div class="thumb" v-if="z.image_url"><img :src="resolve(z.image_url)" alt="presenter" /></div>
        <div class="content">
          <div class="row top">
            <span class="chip" :class="z.status==='Upcoming' ? 'up' : 'done'">{{ z.status }}</span>
            <span class="date-badge">📅 {{ formatLocal(z.start_at) }}</span>
          </div>
          <div class="title">{{ z.title }}</div>
          <div class="presenter">{{ z.presenter_name }}</div>
          <div class="desc">{{ z.description }}</div>
          <div class="actions">
            <button class="btn" @click="edit(z)">Edit</button>
            <button class="btn secondary" @click="remove(z.id)">Delete</button>
          </div>
        </div>
      </div>
    </div>
    <div v-if="filtered.length===0" class="empty">Tidak ada data.</div>
    <div class="pager" v-else>
      <button class="btn secondary" :disabled="page===1" @click="page--">Prev</button>
      <span class="pinfo">Halaman {{ page }} / {{ totalPages }}</span>
      <button class="btn" :disabled="page===totalPages" @click="page++">Next</button>
    </div>

    <div v-if="showEditor" class="modal">
      <div class="panel">
        <div class="head">
          <h3 style="margin:0;">{{ editing?.id ? 'Edit' : 'Tambah' }} Zoom Discussion</h3>
          <button class="btn secondary" @click="closeEditor">Tutup</button>
        </div>
        <form class="form" @submit.prevent="save()">
          <label>Judul<input class="input" v-model="form.title" required /></label>
          <label>Presenter<input class="input" v-model="form.presenter_name" required /></label>
          <label>Deskripsi<textarea class="input textarea" v-model="form.description" /></label>
          <label>Image URL<input class="input" v-model="form.image_url" placeholder="https://... / /uploads/..." /></label>
          <label>Sub Category
            <select class="input" v-model="form.category_id">
              <option :value="null">Tidak ada</option>
              <option v-for="c in subCategories" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </label>
          <label>Mulai (GMT+7)<input class="input" type="datetime-local" v-model="form.start_at_local" required /></label>
          <label>Selesai (opsional)<input class="input" type="datetime-local" v-model="form.end_at_local" /></label>
          <label>Meeting Link (hanya disimpan)<input class="input" v-model="form.meeting_url" /></label>
          <label>Password (opsional)<input class="input" v-model="form.meeting_password" /></label>
          <div class="form-actions">
            <button class="btn" type="submit">Simpan</button>
          </div>
        </form>
      </div>
    </div>
  </div>
  </AdminLayout>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import AdminLayout from '../../components/admin/AdminLayout.vue'
import api from '../../api/client'

const items = ref([])
const search = ref('')
const filterMode = ref('all')
const page = ref(1)
const pageSize = ref(9)

const showEditor = ref(false)
const editing = ref(null)
const form = ref({
  title:'', presenter_name:'', description:'', image_url:'',
  category_id: null,
  start_at_local:'', end_at_local:'', meeting_url:'', meeting_password:''
})
const categories = ref([])
const subCategories = computed(() => (categories.value || []).filter(c => !!c.parent_id))

function resolve(src){
  if (!src) return ''
  const s = String(src)
  if (/^https?:\/\//i.test(s) || s.startsWith('data:image')) return s
  const path = s.startsWith('/') ? s : `/${s}`
  if (path.startsWith('/uploads/')) return `${window.location.origin.replace('5173','8000')}${path}`
  return path
}
function formatLocal(s){ try { return new Date(s).toLocaleString('id-ID', { timeZone: 'Asia/Jakarta', dateStyle: 'medium', timeStyle: 'short' }) } catch { return s } }

const filtered = computed(() => {
  let arr = items.value
  const q = search.value.toLowerCase().trim()
  if (q) arr = arr.filter(z => String(z.title).toLowerCase().includes(q) || String(z.presenter_name).toLowerCase().includes(q))
  if (filterMode.value === 'up') arr = arr.filter(z => z.status === 'Upcoming')
  else if (filterMode.value === 'done') arr = arr.filter(z => z.status !== 'Upcoming')
  return arr
})
const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / pageSize.value)))
const paged = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return filtered.value.slice(start, start + pageSize.value)
})

async function load(){
  const { data } = await api.get('/zoom-discussions/')
  const { data: cats } = await api.get('/categories/')
  categories.value = cats
  items.value = data.sort((a,b)=>{
    if (a.status===b.status) return String(b.start_at).localeCompare(String(a.start_at))
    return a.status==='Upcoming' ? -1 : 1
  })
  page.value = 1
}

function openNew(){
  editing.value = null
  form.value = { title:'', presenter_name:'', description:'', image_url:'', category_id: null, start_at_local:'', end_at_local:'', meeting_url:'', meeting_password:'' }
  showEditor.value = true
}
function edit(z){
  editing.value = z
  // convert ISO -> local datetime-local (Asia/Jakarta)
  const toLocal = (iso) => {
    if (!iso) return ''
    const d = new Date(iso)
    const tz = new Intl.DateTimeFormat('sv-SE', { timeZone: 'Asia/Jakarta', dateStyle:'short', timeStyle:'short', hour12:false }).format(d).replace(' ', 'T')
    return tz.slice(0,16)
  }
  form.value = {
    title: z.title, presenter_name: z.presenter_name, description: z.description || '', image_url: z.image_url || '',
    category_id: z.category_id ?? null,
    start_at_local: toLocal(z.start_at), end_at_local: toLocal(z.end_at),
    meeting_url: z.meeting_url || '', meeting_password: z.meeting_password || ''
  }
  showEditor.value = true
}
function closeEditor(){ showEditor.value = false }

function localToIsoJakarta(local){
  if (!local) return null
  // treat input as Asia/Jakarta and convert to ISO string
  const [date, time] = local.split('T')
  const [y,m,d] = date.split('-').map(Number)
  const [hh,mm] = time.split(':').map(Number)
  const utc = new Date(Date.UTC(y, m-1, d, hh-7, mm))
  return utc.toISOString()
}

async function save(){
  const payload = {
    title: form.value.title,
    presenter_name: form.value.presenter_name,
    description: form.value.description || null,
    image_url: form.value.image_url || null,
    category_id: form.value.category_id ? Number(form.value.category_id) : null,
    start_at: localToIsoJakarta(form.value.start_at_local),
    end_at: localToIsoJakarta(form.value.end_at_local),
    meeting_url: form.value.meeting_url || null,
    meeting_password: form.value.meeting_password || null,
  }
  if (editing.value?.id){
    await api.put(`/zoom-discussions/${editing.value.id}`, payload)
  } else {
    await api.post('/zoom-discussions/', payload)
  }
  showEditor.value = false
  await load()
}

async function remove(id){
  if (!confirm('Hapus jadwal ini?')) return
  await api.delete(`/zoom-discussions/${id}`)
  await load()
}

onMounted(load)
</script>
<style scoped>
.toolbar{ display:flex; gap:8px; align-items:center; margin:8px 0 12px; }
.zoom-card{ background:#fff; border:1px solid #e2e8f0; border-radius:12px; overflow:hidden; box-shadow:0 2px 10px rgba(0,0,0,0.05); display:flex; flex-direction:column; }
.thumb{ width:100%; height:160px; background:#f1f5f9; }
.thumb img{ width:100%; height:100%; object-fit:cover; display:block; }
@media (max-width: 900px){ .thumb{ height:140px; } }
.content{ padding:12px; display:flex; flex-direction:column; gap:6px; }
.row.top{ display:flex; justify-content:space-between; align-items:center; gap:8px; }
.title{ font-weight:800; color:#0f172a; }
.presenter{ font-weight:700; color:#334155; font-size:14px; }
.desc{ color:#64748b; font-size:14px; overflow:hidden; display:-webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 3; }
.chip{ font-size:12px; padding:2px 8px; border-radius:999px; border:1px solid #e2e8f0; }
.chip.up{ background:#ecfeff; color:#155e75; border-color:#a5f3fc; }
.chip.done{ background:#f8fafc; color:#334155; }
.date-badge{ font-size:12px; color:#0f172a; background:#fff; border:1px solid #e2e8f0; border-radius:999px; padding:2px 8px; }
.pager{ display:flex; gap:8px; justify-content:center; align-items:center; margin-top:12px; }
.modal{ position:fixed; inset:0; background:rgba(15,23,42,0.5); display:flex; align-items:center; justify-content:center; z-index:2000; }
.panel{ background:#fff; border-radius:12px; padding:14px; width:min(720px, 96vw); max-height:90vh; overflow:auto; display:flex; flex-direction:column; gap:12px; }
.panel .head{ display:flex; justify-content:space-between; align-items:center; }
.form{ display:grid; grid-template-columns: 1fr 1fr; gap:12px; }
.form label{ display:flex; flex-direction:column; gap:6px; font-weight:600; color:#0f172a; }
.form .textarea{ min-height: 90px; }
.form-actions{ grid-column: 1 / -1; display:flex; justify-content:flex-end; }
@media (max-width: 900px){ .form{ grid-template-columns: 1fr; } }
/* Grid columns like public zoom page */
.grid.cols-4{ display:grid; grid-template-columns: repeat(4,1fr); }
@media (max-width: 1200px){ .grid.cols-4{ grid-template-columns: repeat(3,1fr); } }
@media (max-width: 900px){ .grid.cols-4{ grid-template-columns: repeat(2,1fr); } }
@media (max-width: 640px){ .grid.cols-4{ grid-template-columns: 1fr; } }
</style>
