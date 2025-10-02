<template>
  <div class="card">
    <h2>Users</h2>
    <div class="toolbar" style="display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin-bottom:10px;">
      <input v-model="q" placeholder="Search email/name/phone" class="input" style="max-width:260px;" />
      <select v-model="filterActive" class="input">
        <option value="all">All</option>
        <option value="active">Active</option>
        <option value="inactive">Inactive</option>
      </select>
      <select v-model="filterAdmin" class="input">
        <option value="all">All roles</option>
        <option value="admin">Admin</option>
        <option value="user">User</option>
      </select>
      <select v-model="sortBy" class="input">
        <option value="created_desc">Newest</option>
        <option value="created_asc">Oldest</option>
        <option value="name_asc">Name A-Z</option>
        <option value="name_desc">Name Z-A</option>
        <option value="email_asc">Email A-Z</option>
        <option value="email_desc">Email Z-A</option>
        <option value="active_until_desc">Valid Until desc</option>
        <option value="active_until_asc">Valid Until asc</option>
      </select>
      <div style="margin-left:auto; display:flex; gap:8px; align-items:center;">
        <button class="btn-sm" :disabled="selectedIds.length===0" @click="bulkActivate">Activate Selected (1 mo)</button>
        <button class="btn-sm gray" :disabled="selectedIds.length===0" @click="bulkDeactivate">Deactivate Selected</button>
      </div>
    </div>
    <table style="width:100%; border-collapse:collapse;">
      <thead>
        <tr>
          <th style="text-align:left; border-bottom:1px solid #e2e8f0; padding:8px; width:28px;"><input type="checkbox" :checked="allVisibleChecked" @change="toggleAll($event.target.checked)"/></th>
          <th style="text-align:left; border-bottom:1px solid #e2e8f0; padding:8px;">Email</th>
          <th style="text-align:left; border-bottom:1px solid #e2e8f0; padding:8px;">Name</th>
          <th style="text-align:left; border-bottom:1px solid #e2e8f0; padding:8px;">Phone</th>
          <th style="text-align:left; border-bottom:1px solid #e2e8f0; padding:8px;">Admin</th>
          <th style="text-align:left; border-bottom:1px solid #e2e8f0; padding:8px;">Active</th>
          <th style="text-align:left; border-bottom:1px solid #e2e8f0; padding:8px;">Valid Until</th>
          <th style="text-align:right; border-bottom:1px solid #e2e8f0; padding:8px;">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="u in filteredSorted" :key="u.id">
          <td style="padding:8px; width:28px;"><input type="checkbox" :checked="selectedIds.includes(u.id)" @change="toggleOne(u.id, $event.target.checked)"/></td>
          <td style="padding:8px;">{{ u.email }}</td>
          <td style="padding:8px;">{{ u.full_name }}</td>
          <td style="padding:8px; white-space:nowrap;">{{ u.phone || '-' }}</td>
          <td style="padding:8px;">{{ u.is_admin ? 'Yes' : 'No' }}</td>
          <td style="padding:8px; white-space:nowrap;">
            <span :class="['badge', u.is_active ? 'ok' : 'off']">{{ u.is_active ? 'Active' : 'Inactive' }}</span>
          </td>
          <td style="padding:8px; white-space:nowrap;">{{ formatDate(u.active_until) || '-' }}</td>
          <td style="padding:8px; text-align:right; white-space:nowrap;">
            <button class="btn-sm" v-if="!u.is_active" @click="activate(u)">Activate (1 mo)</button>
            <button class="btn-sm gray" v-else @click="deactivate(u)">Deactivate</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
<script setup>
import { onMounted, ref, computed } from 'vue'
import api from '../../api/client'
const users = ref([])
const q = ref('')
const filterActive = ref('all')
const filterAdmin = ref('all')
const sortBy = ref('created_desc')
const selectedIds = ref([])

onMounted(async () => {
  const { data } = await api.get('/users/')
  users.value = data
})

function formatDate(val){
  if (!val) return ''
  const d = new Date(val)
  if (isNaN(d.getTime())) return ''
  return d.toLocaleDateString(undefined, { year:'numeric', month:'short', day:'2-digit' })
}

async function refresh(){
  const { data } = await api.get('/users/')
  users.value = data
}

async function activate(u){
  await api.post(`/users/${u.id}/activate`)
  await refresh()
}
async function deactivate(u){
  await api.post(`/users/${u.id}/deactivate`)
  await refresh()
}

const filteredSorted = computed(() => {
  let arr = [...users.value]
  // filter text
  const k = q.value.toLowerCase().trim()
  if (k) arr = arr.filter(u => [u.email, u.full_name, u.phone].some(v => String(v||'').toLowerCase().includes(k)))
  // filter active
  if (filterActive.value !== 'all'){
    arr = arr.filter(u => filterActive.value === 'active' ? u.is_active : !u.is_active)
  }
  // filter role
  if (filterAdmin.value !== 'all'){
    arr = arr.filter(u => filterAdmin.value === 'admin' ? u.is_admin : !u.is_admin)
  }
  const cmp = (a,b, field, dir=1) => (String(a?.[field]||'')).localeCompare(String(b?.[field]||'')) * dir
  switch (sortBy.value){
    case 'created_asc': arr.sort((a,b)=>cmp(a,b,'created_at',1)); break
    case 'name_asc': arr.sort((a,b)=>cmp(a,b,'full_name',1)); break
    case 'name_desc': arr.sort((a,b)=>cmp(b,a,'full_name',1)); break
    case 'email_asc': arr.sort((a,b)=>cmp(a,b,'email',1)); break
    case 'email_desc': arr.sort((a,b)=>cmp(b,a,'email',1)); break
    case 'active_until_desc': arr.sort((a,b)=> new Date(b.active_until||0)-new Date(a.active_until||0)); break
    case 'active_until_asc': arr.sort((a,b)=> new Date(a.active_until||0)-new Date(b.active_until||0)); break
    case 'created_desc': default: arr.sort((a,b)=>cmp(b,a,'created_at',1)); break
  }
  return arr
})

const allVisibleChecked = computed(()=> filteredSorted.value.length>0 && filteredSorted.value.every(u=> selectedIds.value.includes(u.id)))
function toggleAll(val){
  if (val){ selectedIds.value = filteredSorted.value.map(u=>u.id) }
  else { selectedIds.value = [] }
}
function toggleOne(id, val){
  const s = new Set(selectedIds.value)
  if (val) s.add(id); else s.delete(id)
  selectedIds.value = Array.from(s)
}
async function bulkActivate(){
  if (selectedIds.value.length===0) return
  await api.post('/users/activate-bulk', { ids: selectedIds.value, months: 1 })
  await refresh()
}
async function bulkDeactivate(){
  if (selectedIds.value.length===0) return
  await api.post('/users/deactivate-bulk', { ids: selectedIds.value })
  await refresh()
}
</script>

<style scoped>
.badge{ padding:2px 8px; border-radius:999px; font-size:12px; font-weight:700; }
.badge.ok{ background:#ecfdf5; color:#065f46; border:1px solid #a7f3d0; }
.badge.off{ background:#f1f5f9; color:#475569; border:1px solid #e2e8f0; }
.btn-sm{ padding:6px 10px; border-radius:8px; background:#2563eb; color:#fff; border:none; cursor:pointer; font-weight:600; }
.btn-sm.gray{ background:#e2e8f0; color:#0f172a; }
.btn-sm:hover{ filter:brightness(.95); }
</style>
