<template>
  <AdminLayout>
    <template #title>Users</template>
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
      <div class="tabs">
        <button type="button" class="tab-btn" :class="{ active: activeTab==='list' }" @click="activeTab='list'">User List</button>
        <button type="button" class="tab-btn" :class="{ active: activeTab==='bulk' }" @click="activeTab='bulk'">Bulk Import</button>
      </div>
      <div style="margin-left:auto; display:flex; gap:8px; align-items:center;">
        <select v-model.number="bulkMonths" class="input">
          <option v-for="m in monthsOptions" :key="m" :value="m">{{ m }} month{{ m>1? 's':'' }}</option>
        </select>
        <button class="btn-sm" :disabled="selectedIds.length===0" @click="setPlanSelected('paid')">Set Selected Paid</button>
        <button class="btn-sm gray" :disabled="selectedIds.length===0" @click="setPlanSelected('free')">Set Selected Free</button>
      </div>
    </div>
    <div v-if="activeTab==='list'" class="table-wrap">
    <table style="width:100%; border-collapse:collapse;">
      <thead>
        <tr>
          <th style="text-align:left; border-bottom:1px solid #e2e8f0; padding:8px; width:28px;"><input type="checkbox" :checked="allVisibleChecked" @change="toggleAll($event.target.checked)"/></th>
          <th class="col-email" style="text-align:left; border-bottom:1px solid #e2e8f0; padding:8px;">Email</th>
          <th class="col-name" style="text-align:left; border-bottom:1px solid #e2e8f0; padding:8px;">Name</th>
          <th style="text-align:left; border-bottom:1px solid #e2e8f0; padding:8px;">Phone</th>
          <th style="text-align:left; border-bottom:1px solid #e2e8f0; padding:8px;">Admin</th>
          <th style="text-align:left; border-bottom:1px solid #e2e8f0; padding:8px;">Teacher</th>
          <th style="text-align:left; border-bottom:1px solid #e2e8f0; padding:8px;">Plan</th>
          <th style="text-align:left; border-bottom:1px solid #e2e8f0; padding:8px;">Validity</th>
          <th class="actions-col" style="text-align:right; border-bottom:1px solid #e2e8f0; padding:8px;">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="u in filteredSorted" :key="u.id">
          <td style="padding:8px; width:28px;"><input type="checkbox" :checked="selectedIds.includes(u.id)" @change="toggleOne(u.id, $event.target.checked)"/></td>
          <td class="td-email" style="padding:8px;">
            <span class="truncate email" :title="u.email">{{ u.email }}</span>
          </td>
          <td class="td-name" style="padding:8px;">
            <span class="clamp2" :title="u.full_name">{{ u.full_name }}</span>
          </td>
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
          <td class="actions-cell actions-col">
            <div class="actions">
              <button class="btn-sm" @click="setPaid(u)" title="Set Paid">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="16" height="16" aria-hidden="true">
                  <path d="M12 1v22M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
                </svg>
              </button>
              <button class="btn-sm gray" @click="setFree(u)" title="Set Free">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="16" height="16" aria-hidden="true">
                  <path d="M3 12h18"/>
                </svg>
              </button>
              <button class="btn-sm warn" title="Reset Password" @click="resetPassword(u)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="16" height="16" aria-hidden="true">
                  <path d="M12 11a4 4 0 1 0-4-4"/>
                  <rect x="6" y="11" width="12" height="10" rx="2"/>
                  <path d="M12 16v2"/>
                </svg>
              </button>
              <button class="btn-sm warn" title="Generate Temporary Password" @click="generatePassword(u)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="16" height="16" aria-hidden="true">
                  <path d="M13 2L3 14h7l-1 8 11-12h-7l1-8z"/>
                </svg>
              </button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
    </div>

    <div v-else class="bulk-card">
      <div class="bulk-header">
        <div>
          <h3>Bulk Create Users</h3>
          <p>Upload a CSV with columns <code>email,full_name,phone</code>. New accounts start on the Free plan and share the password you set.</p>
        </div>
        <button type="button" class="btn-sm gray bulk-template-btn" @click="downloadBulkTemplate">Download template CSV</button>
      </div>
      <div class="bulk-body">
        <label class="bulk-field">
          <span class="bulk-label">CSV file</span>
          <input type="file" accept=".csv" @change="onBulkFileChange" />
        </label>
        <label class="bulk-field">
          <span class="bulk-label">Initial password</span>
          <input v-model="bulkPassword" type="password" placeholder="Min 8 characters" class="input" />
        </label>
        <div class="bulk-actions">
          <button class="btn-sm" :disabled="!bulkFile || !bulkPassword || bulkLoading" @click="submitBulkCreate">
            {{ bulkLoading ? 'Creating accounts…' : 'Create Accounts from CSV' }}
          </button>
        </div>
        <div v-if="bulkError" class="bulk-error">{{ bulkError }}</div>
        <div v-if="bulkResult" class="bulk-result">
          <div v-if="bulkResult.created?.length">Created: {{ bulkResult.created.length }} user(s).</div>
          <div v-if="bulkResult.skipped?.length">Skipped: {{ bulkResult.skipped.length }} ({{ bulkResult.skipped.map(x=>x.email).join(', ') }}).</div>
        </div>
      </div>
    </div>
  </AdminLayout>
</template>
<script setup>
import { onMounted, ref, computed } from 'vue'
import api from '../../api/client'
import AdminLayout from '../../components/admin/AdminLayout.vue'
const users = ref([])
const q = ref('')
const filterAdmin = ref('all')
const sortBy = ref('created_desc')
const activeTab = ref('list')
const selectedIds = ref([])
const monthsOptions = [1,2,3,4,5,6,7,8,9,10,11,12]
const monthsById = ref({})
const bulkMonths = ref(1)
const bulkFile = ref(null)
const bulkPassword = ref('')
const bulkLoading = ref(false)
const bulkResult = ref(null)
const bulkError = ref('')

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

function onBulkFileChange(e){
  const files = e.target.files || []
  bulkFile.value = files.length ? files[0] : null
  bulkResult.value = null
  bulkError.value = ''
}

async function submitBulkCreate(){
  if (!bulkFile.value || !bulkPassword.value) return
  const pwd = String(bulkPassword.value || '').trim()
  if (pwd.length < 8){
    bulkError.value = 'Password must be at least 8 characters.'
    return
  }
  bulkLoading.value = true
  bulkError.value = ''
  bulkResult.value = null
  try {
    const text = await bulkFile.value.text()
    const lines = text.split(/\r?\n/).map(l=>l.trim()).filter(Boolean)
    if (!lines.length){
      bulkError.value = 'CSV file is empty.'
      bulkLoading.value = false
      return
    }
    let startIndex = 0
    const first = lines[0].toLowerCase()
    if (first.includes('email') && first.includes('full') ){
      startIndex = 1
    }
    const usersPayload = []
    for (let i=startIndex; i<lines.length; i++){
      const row = lines[i]
      const parts = row.split(',')
      if (parts.length < 2) continue
      const email = String(parts[0] || '').trim()
      const fullName = String(parts[1] || '').trim()
      const phone = String(parts[2] || '').trim() || null
      if (!email || !fullName) continue
      usersPayload.push({ email, full_name: fullName, phone })
    }
    if (!usersPayload.length){
      bulkError.value = 'No valid rows found. Expected columns: email,full_name,phone.'
      bulkLoading.value = false
      return
    }
    const { data } = await api.post('/users/bulk-create', {
      users: usersPayload,
      password: pwd,
    })
    bulkResult.value = data
    await refresh()
  } catch (e) {
    bulkError.value = 'Failed to create users in bulk.'
  } finally {
    bulkLoading.value = false
  }
}

function downloadBulkTemplate(){
  const header = 'email,full_name,phone\n'
  const example = 'student1@example.com,Student One,+628123456789\nstudent2@example.com,Student Two,\n'
  const csv = header + example
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'users_template.csv'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
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
.btn-sm{ padding:4px 8px; border-radius:8px; background:#2563eb; color:#fff; border:none; cursor:pointer; font-weight:600; display:inline-flex; align-items:center; justify-content:center; }
.btn-sm.gray{ background:#e2e8f0; color:#0f172a; }
.btn-sm.warn{ background:#f59e0b; color:#0f172a; }
.btn-sm:hover{ filter:brightness(.95); }
.sep{ display:inline-block; width:8px; }

/* Make long text look neat with ellipsis */
.truncate{ display:inline-block; max-width:100%; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; vertical-align:bottom; }
.truncate.email{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 13px; }
.clamp2{ display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 2; overflow: hidden; max-width: 100%; }
/* Responsive content constraints so table columns can auto-size */
.td-email .truncate{ max-width: clamp(180px, 30vw, 320px); }
.td-name .clamp2{ max-width: clamp(140px, 22vw, 260px); }

/* Prevent awkward wrapping inside table cells */
.table-wrap table td{ vertical-align:top; }

/* Prevent overflow in Actions column */
.actions-cell{ padding:8px; text-align:right; vertical-align:top; }
.actions{
  display:flex;
  flex-wrap:wrap;
  gap:6px;
  justify-content:flex-end;
  margin-left:auto;
  max-width:240px;
}

/* Sticky right column for Actions */
.actions-col{ position:sticky; right:0; background:#fff; z-index:1; }
thead .actions-col{ z-index:2; }

.table-wrap{ overflow-x:auto; }

.bulk-card{
  margin-top:16px;
  padding:14px 16px;
  border-radius:12px;
  border:1px solid #e2e8f0;
  background:#f8fafc;
  max-width:640px;
}
.bulk-header{
  display:flex;
  align-items:flex-start;
  justify-content:space-between;
  gap:12px;
  margin-bottom:10px;
}
.bulk-header h3{
  margin:0 0 4px;
  font-size:14px;
  font-weight:600;
}
.bulk-header p{
  margin:0;
  font-size:13px;
  color:#64748b;
}
.bulk-template-btn{
  padding:4px 10px;
  font-size:12px;
}
.bulk-body{
  display:flex;
  flex-direction:column;
  gap:10px;
}
.bulk-field{
  display:flex;
  flex-direction:column;
  gap:4px;
  font-size:13px;
}
.bulk-label{
  font-weight:500;
  color:#0f172a;
}
.bulk-actions{
  margin-top:4px;
}
.bulk-error{
  font-size:13px;
  color:#b91c1c;
  white-space:pre-wrap;
}
.bulk-result{
  font-size:13px;
  color:#0f172a;
  white-space:pre-wrap;
}

/* Tabs above table for switching between list and bulk import */
.tabs{
  display:flex;
  gap:4px;
}
.tab-btn{
  padding:4px 10px;
  border-radius:999px;
  border:1px solid #e2e8f0;
  background:#f8fafc;
  font-size:12px;
  font-weight:500;
  color:#475569;
  cursor:pointer;
}
.tab-btn.active{
  background:#2563eb;
  color:#fff;
  border-color:#2563eb;
}

@media (max-width: 700px){
  .bulk-card{ max-width:100%; }
  .bulk-header{ flex-direction:column; align-items:flex-start; }
  .bulk-template-btn{ align-self:flex-start; }
}

/* Make buttons compact and wrap nicely on narrow screens */
@media (max-width: 900px){
  .actions{ max-width: 100%; justify-content:flex-start; }
}
</style>
