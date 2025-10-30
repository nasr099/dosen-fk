<template>
  <div class="card">
    <h2>Users</h2>
    <div class="toolbar" style="display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin-bottom:10px;">
      <input v-model="q" placeholder="Search email/name/phone" class="input" style="max-width:260px;" />
      <select v-model="filterAdmin" class="input">
        <option value="all">All roles</option>
        <option value="admin">Admin</option>
        <option value="teacher">Teacher</option>
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
        <select v-model.number="bulkMonths" class="input">
          <option v-for="m in monthsOptions" :key="m" :value="m">{{ m }} month{{ m>1? 's':'' }}</option>
        </select>
        <button class="btn-sm" :disabled="selectedIds.length===0" @click="setPlanSelected('paid')">Set Selected Paid</button>
        <button class="btn-sm gray" :disabled="selectedIds.length===0" @click="setPlanSelected('free')">Set Selected Free</button>
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
          <th style="text-align:left; border-bottom:1px solid #e2e8f0; padding:8px;">Teacher</th>
          <th style="text-align:left; border-bottom:1px solid #e2e8f0; padding:8px;">Plan</th>
          <th style="text-align:left; border-bottom:1px solid #e2e8f0; padding:8px;">Validity</th>
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
          <td style="padding:8px;">
            <button class="btn-sm" :class="u.is_teacher ? '' : 'gray'" @click="toggleTeacher(u)">{{ u.is_teacher ? 'Yes' : 'No' }}</button>
          </td>
          <td style="padding:8px; white-space:nowrap;">
            <span :class="['badge', u.plan==='paid' ? 'ok' : 'off']">{{ (u.plan||'free')==='paid' ? 'Paid' : 'Free' }}</span>
          </td>
          <td style="padding:8px; white-space:nowrap; display:flex; gap:6px; align-items:center;">
            <select v-model.number="monthsById[u.id]" class="input" style="width:110px;">
              <option v-for="m in monthsOptions" :key="m" :value="m">{{ m }} month{{ m>1? 's':'' }}</option>
            </select>
            <span class="muted" v-if="u.active_until">→ {{ formatDate(u.active_until) }}</span>
          </td>
          <td style="padding:8px; text-align:right; white-space:nowrap;">
            <button class="btn-sm" @click="setPaid(u)">Set Paid</button>
            <button class="btn-sm gray" @click="setFree(u)">Set Free</button>
            <span class="sep"></span>
            <button class="btn-sm warn" title="Set a specific password" @click="resetPassword(u)">Reset PW</button>
            <button class="btn-sm warn" title="Generate a temporary password" @click="generatePassword(u)">Gen Temp</button>
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
const filterAdmin = ref('all')
const sortBy = ref('created_desc')
const selectedIds = ref([])
const monthsOptions = [1,2,3,4,5,6,7,8,9,10,11,12]
const monthsById = ref({})
const bulkMonths = ref(1)

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

async function setPaid(u){
  const months = Number(monthsById.value[u.id] || 1)
  await api.post('/users/activate-bulk', { ids: [u.id], months })
  await refresh()
}
async function setFree(u){
  await api.post('/users/deactivate-bulk', { ids: [u.id] })
  await refresh()
}

async function toggleTeacher(u){
  const next = !u.is_teacher
  await api.patch(`/users/${u.id}/teacher`, { is_teacher: next })
  await refresh()
}

async function resetPassword(u){
  try {
    const pw = window.prompt(`Enter a new password for ${u.email} (min 8 chars):`)
    if (!pw) return
    if (String(pw).length < 8){
      alert('Password must be at least 8 characters')
      return
    }
    await api.post(`/users/${u.id}/reset-password`, { new_password: pw })
    alert('Password updated successfully')
  } catch (e) {
    alert('Failed to reset password')
  }
}

async function generatePassword(u){
  try {
    const ok = window.confirm(`Generate a temporary password for ${u.email}?`)
    if (!ok) return
    const { data } = await api.post(`/users/${u.id}/reset-password`, { generate: true, length: 12 })
    const temp = data?.temporary_password
    if (temp){
      try { await navigator.clipboard.writeText(temp) } catch {}
      alert(`Temporary password (copied to clipboard):\n\n${temp}`)
    } else {
      alert('Temporary password generated')
    }
  } catch (e) {
    alert('Failed to generate temporary password')
  }
}

const filteredSorted = computed(() => {
  let arr = [...users.value]
  // filter text
  const k = q.value.toLowerCase().trim()
  if (k) arr = arr.filter(u => [u.email, u.full_name, u.phone].some(v => String(v||'').toLowerCase().includes(k)))
  // filter role
  if (filterAdmin.value !== 'all'){
    if (filterAdmin.value === 'admin') arr = arr.filter(u => u.is_admin)
    else if (filterAdmin.value === 'teacher') arr = arr.filter(u => u.is_teacher)
    else arr = arr.filter(u => !u.is_admin && !u.is_teacher)
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
async function setPlanSelected(plan){
  if (selectedIds.value.length===0) return
  if (plan === 'paid'){
    const months = Number(bulkMonths.value || 1)
    await api.post('/users/activate-bulk', { ids: selectedIds.value, months })
  } else {
    await api.post('/users/deactivate-bulk', { ids: selectedIds.value })
  }
  await refresh()
}
// no separate bulk extend; use Set Selected Paid with months
</script>

<style scoped>
.badge{ padding:2px 8px; border-radius:999px; font-size:12px; font-weight:700; }
.badge.ok{ background:#ecfdf5; color:#065f46; border:1px solid #a7f3d0; }
.badge.off{ background:#f1f5f9; color:#475569; border:1px solid #e2e8f0; }
.btn-sm{ padding:6px 10px; border-radius:8px; background:#2563eb; color:#fff; border:none; cursor:pointer; font-weight:600; }
.btn-sm.gray{ background:#e2e8f0; color:#0f172a; }
.btn-sm.warn{ background:#f59e0b; color:#0f172a; }
.btn-sm:hover{ filter:brightness(.95); }
.sep{ display:inline-block; width:8px; }
</style>
