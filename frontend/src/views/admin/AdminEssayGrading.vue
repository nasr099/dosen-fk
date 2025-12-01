<template>
  <AdminLayout>
    <template #title>Essay Grading</template>
    <div class="card">
    <h2 style="margin-top:0">Essay Grading</h2>
    <form class="filters" @submit.prevent="apply">
      <input class="input" v-model="q" placeholder="Search by question text or user email" />
      <select class="input" v-model="origin">
        <option value="all">All (Exam + Tryout)</option>
        <option value="tryout">Tryout only</option>
        <option value="exam">Non-Tryout (Exam) only</option>
      </select>
      <select class="input" v-model.number="setId">
        <option :value="0">All Sets</option>
        <option v-for="s in sets" :key="s.id" :value="s.id">{{ s.title }}</option>
      </select>
      <select class="input" v-model="status">
        <option value="pending">Pending</option>
        <option value="graded">Graded</option>
      </select>
      <button class="btn small" type="submit">Apply</button>
    </form>

    <div v-if="rows.length===0" class="empty">No items</div>
    <table v-else class="table">
      <thead>
        <tr>
          <th>Completed</th>
          <th>User</th>
          <th>Set</th>
          <th>Question</th>
          <th>Answer</th>
          <th>Status</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="it in rows" :key="it.answer_id">
          <td>{{ fmt(it.completed_at) }}</td>
          <td>{{ it.user_email }}</td>
          <td>{{ it.set_title || '-' }}</td>
          <td class="clamp">{{ it.question_text }}</td>
          <td class="clamp">{{ it.user_answer }}</td>
          <td>
            <span v-if="it.grade" class="badge" :class="it.grade.status">{{ it.grade.status }} ({{ it.grade.score }})</span>
            <span v-else class="badge pending">pending</span>
          </td>
          <td><button class="btn tiny" @click="open(it)">Grade</button></td>
        </tr>
      </tbody>
    </table>
    <div class="pager" v-if="rows.length">
      <div class="pager-left">
        <label>Rows</label>
        <select v-model.number="pageSize" @change="toPage(1)">
          <option :value="10">10</option>
          <option :value="20">20</option>
          <option :value="50">50</option>
        </select>
      </div>
      <div class="pager-right">
        <button class="btn small secondary" :disabled="page<=1" @click="toPage(page-1)">Prev</button>
        <span>Page {{ page }} • Total {{ total }}</span>
        <button class="btn small" :disabled="isLastPage" @click="toPage(page+1)">Next</button>
      </div>
    </div>

    <div v-if="show" class="modal">
      <div class="modal-body">
        <h3>Grade Essay</h3>
        <p class="q">{{ current?.question_text }}</p>
        <label>Your answer</label>
        <div class="answer">{{ current?.user_answer }}</div>
        <div class="grid">
          <div>
            <label>Score (0-100)</label>
            <input type="number" class="input" v-model.number="form.score" min="0" max="100" />
          </div>
          <div>
            <label>Status</label>
            <div class="status-readonly">
              <span class="badge" :class="derivedStatus">{{ derivedStatus }}</span>
            </div>
            <div class="hint">Status is auto-calculated from score.</div>
          </div>
        </div>
        <label>Notes</label>
        <textarea class="input textarea" v-model="form.notes" placeholder="Feedback for the learner (or internal notes)"></textarea>
        <div class="actions">
          <button class="btn" @click="save">Save</button>
          <button class="btn" @click="saveAndNext">Save & Next</button>
          <button class="btn secondary" @click="close">Close</button>
        </div>
      </div>
    </div>
  </div>
  </AdminLayout>
</template>
<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import AdminLayout from '../../components/admin/AdminLayout.vue'
import api from '../../api/client'

const rows = ref([])
const status = ref('pending')
const q = ref('')
const origin = ref('all') // all | tryout | exam
const setId = ref(0)
const sets = ref([])
const show = ref(false)
const current = ref(null)
const form = ref({ score: 100, status: 'approved', notes: '' })
const derivedStatus = computed(() => {
  const s = Number(form.value.score) || 0
  if (s >= 70) return 'approved'
  if (s >= 40) return 'partial'
  return 'incorrect'
})
const page = ref(1)
const pageSize = ref(20)
const isLastPage = computed(() => rows.value.length < pageSize.value)
const total = ref(0)

function fmt(s){ try{ return new Date(s).toLocaleString() } catch { return s } }

async function load(){
  const params = { status: status.value, q: q.value, page: page.value, page_size: pageSize.value }
  if (setId.value) params.set_id = setId.value
  if (origin.value === 'tryout') params.is_tryout = 1
  if (origin.value === 'exam') params.is_tryout = 0
  const { data } = await api.get('/essays', { params })
  // data: { total, items }
  total.value = data.total
  rows.value = data.items
}

function toPage(p){
  page.value = Math.max(1, p)
  load()
}

async function loadSets(){
  const { data } = await api.get('/sets')
  sets.value = data
}

function apply(){ page.value = 1; load() }

function open(it){
  current.value = it
  form.value = { score: it?.grade?.score ?? 100, status: it?.grade?.status ?? 'approved', notes: it?.grade?.notes ?? '' }
  show.value = true
}
function close(){ show.value = false }

async function save(){
  if (!current.value) return
  const payload = { score: Number(form.value.score), status: derivedStatus.value, notes: form.value.notes }
  const path = current.value.is_tryout ? `/essays/tryout/${current.value.answer_id}` : `/essays/${current.value.answer_id}`
  await api.put(path, payload)
  show.value = false
  await load()
}

async function saveAndNext(){
  if (!current.value) return
  const id = current.value.answer_id
  await save()
  // find next in current page; if none, go to next page and open first item
  const idx = rows.value.findIndex(r => r.answer_id === id)
  if (idx >= 0 && idx < rows.value.length - 1){
    open(rows.value[idx + 1])
  } else if (!isLastPage.value){
    page.value += 1
    await load()
    if (rows.value.length) open(rows.value[0])
  }
}

onMounted(load)
onMounted(loadSets)

function onKey(e){
  const isSaveNext = (e.key === 'Enter' && (e.metaKey || e.ctrlKey))
  if (show.value && isSaveNext){
    e.preventDefault()
    saveAndNext()
  }
}
document.addEventListener('keydown', onKey)
onBeforeUnmount(() => document.removeEventListener('keydown', onKey))
</script>
<style scoped>
.filters{ display:flex; gap:8px; align-items:center; margin:8px 0; flex-wrap:wrap; }
.table{ width:100%; border-collapse:collapse; }
.table th,.table td{ border-bottom:1px solid #e2e8f0; padding:8px 10px; text-align:left; vertical-align:top; }
.clamp{ max-width:420px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.badge{ display:inline-block; padding:3px 8px; border-radius:999px; font-size:12px; background:#e2e8f0; }
.badge.pending{ background:#fff7ed; color:#9a3412; border:1px solid #fed7aa; }
.badge.approved{ background:#dcfce7; color:#065f46; }
.badge.partial{ background:#fef9c3; color:#713f12; }
.badge.incorrect{ background:#fee2e2; color:#7f1d1d; }
.pager{ display:flex; justify-content:center; align-items:center; gap:16px; padding:14px 0; }
.pager .pager-left{ display:inline-flex; align-items:center; gap:8px; }
.pager .pager-right{ display:inline-flex; align-items:center; gap:12px; }
.modal{ position:fixed; inset:0; background:rgba(15,23,42,.45); display:flex; align-items:center; justify-content:center; padding:20px; }
.modal-body{ background:#fff; border-radius:12px; padding:16px; width:min(720px, 96vw); box-shadow:0 10px 30px rgba(0,0,0,.2); }
.modal .q{ font-weight:700; margin:6px 0 8px; }
.answer{ background:#f1f5f9; border:1px solid #e2e8f0; border-radius:8px; padding:8px; white-space:pre-wrap; }
.grid{ display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-top:10px; }
.textarea{ min-height: 90px; }
.actions{ display:flex; gap:8px; justify-content:flex-end; margin-top:12px; }
@media (max-width: 700px){ .grid{ grid-template-columns:1fr; } }
</style>
