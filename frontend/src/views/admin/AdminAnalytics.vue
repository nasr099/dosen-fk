<template>
  <AdminLayout>
    <template #title>Analytics</template>
    <div class="card analytics">
    <h2 style="margin-top:0">Analytics</h2>

    <h3>Sets Overview</h3>
    <div class="card" style="padding:12px;">
      <div class="table-wrap">
      <table class="table">
        <thead>
          <tr>
            <th>Set</th>
            <th>Sessions Completed</th>
            <th>Avg Objective</th>
            <th>Avg Essays</th>
            <th>Essay Graded</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in sets" :key="s.set_id">
            <td>{{ s.set_title || '-' }}</td>
            <td>{{ s.sessions_completed }}</td>
            <td>{{ fmtPct(s.avg_objective_score) }}</td>
            <td>{{ fmtPct(s.avg_essay_score) }}</td>
            <td>{{ s.essay_graded_count }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <h3 style="margin-top:18px;">Completed Sessions</h3>
    <form class="filters" @submit.prevent="apply">
      <input class="input" v-model="q" placeholder="Search by user email" />
      <select class="input" v-model.number="setId">
        <option :value="0">All Sets</option>
        <option v-for="s in sets" :key="'sel-'+s.set_id" :value="s.set_id">{{ s.set_title }}</option>
      </select>
      <input class="input" type="datetime-local" v-model="startDate" />
      <input class="input" type="datetime-local" v-model="endDate" />
      <select class="input" v-model="bucket">
        <option value="day">By day</option>
        <option value="week">By week</option>
      </select>
      <button class="btn small" type="submit">Apply</button>
      <button class="btn small secondary" type="button" @click="exportCsv">Export CSV</button>
    </form>

    <div class="grid-2">
      <div class="card card-chart" style="padding:12px;">
        <h4>Trends: Objective vs Essay</h4>
        <canvas ref="trendRef" class="chart-canvas"></canvas>
      </div>
      <div class="card card-chart" style="padding:12px;">
        <h4>Sessions Completed</h4>
        <canvas ref="sessionsRef" class="chart-canvas"></canvas>
      </div>
      </div>
    </div>

    <!-- Insights: 1 top full-width, 2 below -->
    <div style="margin-top:16px;">
      <div class="card" style="padding:12px;">
        <h4>Top Missed MCQs</h4>
        <div class="mini-pager">
          <div class="mini-left">
            <label>Rows</label>
            <select v-model.number="missedPageSize" @change="missedPage=1">
              <option :value="5">5</option>
              <option :value="10">10</option>
              <option :value="20">20</option>
            </select>
          </div>
          <div class="mini-right">
            <button class="btn tiny secondary" :disabled="missedPage<=1" @click="missedPage--">Prev</button>
            <span>{{ missedPage }}</span>
            <button class="btn tiny" :disabled="missedIsLast" @click="missedPage++">Next</button>
          </div>
        </div>
        <div class="table-wrap">
        <table class="table small">
          <thead>
            <tr><th>Set</th><th>Question</th><th>Incorrect</th><th>Attempts</th></tr>
          </thead>
          <tbody>
            <tr v-for="x in missedRows" :key="x.question_id">
              <td class="muted">{{ x.set_title || '-' }}</td>
              <td class="clamp">{{ short(x.question_text) }}</td>
              <td>{{ x.incorrect_count }}</td>
              <td>{{ x.attempts }}</td>
            </tr>
            <tr v-if="topMissed.length===0"><td colspan="4" class="muted">No data</td></tr>
          </tbody>
        </table>
        </div>
      </div>
      <div class="grid-2" style="margin-top:16px; align-items:start;">
      <div class="card" style="padding:12px;">
        <h4>Essay Questions (Lowest Avg)</h4>
        <div class="mini-pager">
          <div class="mini-left">
            <label>Rows</label>
            <select v-model.number="essayPageSize" @change="essayPage=1">
              <option :value="5">5</option>
              <option :value="10">10</option>
              <option :value="20">20</option>
            </select>
          </div>
          <div class="mini-right">
            <button class="btn tiny secondary" :disabled="essayPage<=1" @click="essayPage--">Prev</button>
            <span>{{ essayPage }}</span>
            <button class="btn tiny" :disabled="essayIsLast" @click="essayPage++">Next</button>
          </div>
        </div>
        <div class="table-wrap">
        <table class="table small">
          <thead>
            <tr><th>Set</th><th>Question</th><th>Avg</th><th>Graded</th></tr>
          </thead>
          <tbody>
            <tr v-for="x in essayRows" :key="x.question_id">
              <td class="muted">{{ x.set_title || '-' }}</td>
              <td class="clamp">{{ short(x.question_text) }}</td>
              <td>{{ fmtPct(x.avg_score) }}</td>
              <td>{{ x.graded }}</td>
            </tr>
            <tr v-if="essayQs.length===0"><td colspan="4" class="muted">No data</td></tr>
          </tbody>
        </table>
        </div>
      </div>
      <div class="card" style="padding:12px;">
        <h4>User Progress (Best Delta)</h4>
        <div class="mini-pager">
          <div class="mini-left">
            <label>Rows</label>
            <select v-model.number="progressPageSize" @change="progressPage=1">
              <option :value="5">5</option>
              <option :value="10">10</option>
              <option :value="20">20</option>
            </select>
          </div>
          <div class="mini-right">
            <button class="btn tiny secondary" :disabled="progressPage<=1" @click="progressPage--">Prev</button>
            <span>{{ progressPage }}</span>
            <button class="btn tiny" :disabled="progressIsLast" @click="progressPage++">Next</button>
          </div>
        </div>
        <div class="table-wrap">
        <table class="table small">
          <thead>
            <tr><th>User</th><th>Set</th><th>First</th><th>Last</th><th>Δ</th></tr>
          </thead>
          <tbody>
            <tr v-for="x in progressRows" :key="x.user_email + x.set_title">
              <td class="clamp">{{ x.user_email }}</td>
              <td class="clamp">{{ x.set_title || '-' }}</td>
              <td>{{ fmtPct(x.first_score) }}</td>
              <td>{{ fmtPct(x.last_score) }}</td>
              <td><strong>{{ (Math.round((x.delta||0))) }}%</strong></td>
            </tr>
            <tr v-if="progress.length===0"><td colspan="5" class="muted">No data</td></tr>
          </tbody>
        </table>
        </div>
      </div>
    </div>

    <div class="card" style="padding:12px;">
      <table class="table">
        <thead>
          <tr>
            <th>Completed</th>
            <th>User</th>
            <th>Set</th>
            <th>Objective</th>
            <th>Essays avg</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in rows" :key="r.session_id">
            <td>{{ fmt(r.completed_at) }}</td>
            <td>{{ r.user_email }}</td>
            <td>{{ r.set_title || '-' }}</td>
            <td>{{ fmtPct(r.objective_score) }} ({{ r.objective_correct }}/{{ r.objective_total }})</td>
            <td>{{ fmtPct(r.essay_avg_score) }} ({{ r.essay_graded_count }})</td>
          </tr>
        </tbody>
      </table>
      </div>
      <div class="pager">
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
    </div>
  </div>
  </AdminLayout>
</template>
<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import AdminLayout from '../../components/admin/AdminLayout.vue'
import api from '../../api/client'
import Chart from 'chart.js/auto'

const sets = ref([])
const rows = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const q = ref('')
const setId = ref(0)
const startDate = ref('')
const endDate = ref('')
const bucket = ref('day')
const isLastPage = computed(() => rows.value.length < pageSize.value)

function fmtPct(n){ return `${Math.round((Number(n)||0))}%` }
function fmt(s){ try{ return new Date(s).toLocaleString() } catch { return s } }
function short(s){ s = String(s||''); return s.length>120 ? s.slice(0,117)+'…' : s }

async function loadSets(){
  const { data } = await api.get('/analytics/sets')
  sets.value = data.items
}
async function loadSessions(){
  const params = { page: page.value, page_size: pageSize.value, q: q.value, start_date: startDate.value, end_date: endDate.value }
  if (setId.value) params.set_id = setId.value
  const { data } = await api.get('/analytics/sessions', { params })
  total.value = data.total
  rows.value = data.items
}
function toPage(p){ page.value = Math.max(1, p); loadSessions(); loadCharts(); loadInsights() }
function apply(){ page.value = 1; loadSessions(); loadCharts(); loadInsights() }
async function exportCsv(){
  const params = { }
  if (q.value) params.q = q.value
  if (setId.value) params.set_id = setId.value
  if (startDate.value) params.start_date = startDate.value
  if (endDate.value) params.end_date = endDate.value
  const { data } = await api.get('/analytics/sessions/export', { params, responseType: 'blob' })
  const blob = new Blob([data], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = window.URL.createObjectURL(blob)
  a.download = 'analytics_sessions.csv'
  document.body.appendChild(a)
  a.click()
  a.remove()
}

onMounted(async () => { await loadSets(); await loadSessions() })

// ---------- Charts ----------
const trendRef = ref(null)
const sessionsRef = ref(null)
let trendChart = null
let sessionsChart = null

async function loadCharts(){
  // trends
  const tParams = { bucket: bucket.value, start_date: startDate.value, end_date: endDate.value }
  if (setId.value) tParams.set_id = setId.value
  const { data: tdata } = await api.get('/analytics/trends', { params: tParams })
  const labels = tdata.items.map(i => i.bucket)
  const obj = tdata.items.map(i => Math.round(i.objective_avg || 0))
  const ess = tdata.items.map(i => Math.round(i.essay_avg || 0))
  if (trendChart) trendChart.destroy()
  trendChart = new Chart(trendRef.value, {
    type: 'line',
    data: { labels, datasets: [
      { label: 'Objective %', data: obj, tension: .25, borderColor: '#10b981', backgroundColor: 'rgba(16,185,129,0.2)', pointRadius: 2, fill: true },
      { label: 'Essay %', data: ess, tension: .25, borderColor: '#6366f1', backgroundColor: 'rgba(99,102,241,0.2)', pointRadius: 2, fill: true },
    ]},
    options: { responsive: true, maintainAspectRatio: false, interaction:{ mode:'index', intersect:false }, plugins:{ tooltip:{ enabled:true } }, scales: { y: { min:0, max:100, grid:{ color:'#eef2f7' } }, x:{ grid:{ display:false } } } }
  })
  // sessions completed (per bucket)
  const counts = tdata.items.map(i => i.count || 0)
  if (sessionsChart) sessionsChart.destroy()
  sessionsChart = new Chart(sessionsRef.value, {
    type: 'bar',
    data: { labels, datasets: [{ label: 'Sessions', data: counts, backgroundColor: 'rgba(2,132,199,0.6)' }] },
    options: { responsive: true, maintainAspectRatio: false, plugins:{ tooltip:{ enabled:true } }, scales:{ y:{ beginAtZero:true, grid:{ color:'#eef2f7' } }, x:{ grid:{ display:false } } } }
  })
}

// Auto-update charts and insight tables when filters change (debounced)
let t
watch([setId, startDate, endDate, bucket], () => {
  clearTimeout(t)
  t = setTimeout(() => { loadCharts(); loadInsights() }, 400)
})

onMounted(loadCharts)

// ---------- Insights tables ----------
const topMissed = ref([])
const essayQs = ref([])
const progress = ref([])
// pagination states
const missedPage = ref(1), missedPageSize = ref(10)
const essayPage = ref(1), essayPageSize = ref(10)
const progressPage = ref(1), progressPageSize = ref(10)

const missedRows = computed(() => slicePaginated(topMissed.value, missedPage.value, missedPageSize.value))
const essayRows = computed(() => slicePaginated(essayQs.value, essayPage.value, essayPageSize.value))
const progressRows = computed(() => slicePaginated(progress.value, progressPage.value, progressPageSize.value))
const missedIsLast = computed(() => missedPage.value >= Math.max(1, Math.ceil(topMissed.value.length / missedPageSize.value)))
const essayIsLast = computed(() => essayPage.value >= Math.max(1, Math.ceil(essayQs.value.length / essayPageSize.value)))
const progressIsLast = computed(() => progressPage.value >= Math.max(1, Math.ceil(progress.value.length / progressPageSize.value)))

function slicePaginated(arr, page, size){
  const start = (page-1)*size
  return arr.slice(start, start+size)
}

async function loadInsights(){
  const p = { start_date: startDate.value, end_date: endDate.value }
  if (setId.value) p.set_id = setId.value
  const [{ data: m }, { data: e }, { data: pr }] = await Promise.all([
    api.get('/analytics/insights/top-missed', { params: { ...p, limit: 15 } }),
    api.get('/analytics/insights/essay-questions', { params: { ...p, limit: 15 } }),
    api.get('/analytics/progress', { params: { ...p, limit: 20 } }),
  ])
  topMissed.value = m.items
  essayQs.value = e.items
  progress.value = pr.items
}

onMounted(loadInsights)
</script>
<style scoped>
.analytics{ max-width:100%; overflow-x:hidden; }
.filters{ display:flex; gap:8px; align-items:center; margin:8px 0; flex-wrap:wrap; }
.grid-2{ display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:16px; align-items:start; }
.grid-insights{ display:grid; grid-template-columns: 1fr; gap:16px; }
.grid-insights-2{ display:grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap:16px; }
.grid-3{ display:grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap:16px; }
.table{ width:100%; border-collapse:collapse; }
.table th,.table td{ border-bottom:1px solid #e2e8f0; padding:8px 10px; text-align:left; vertical-align:top; word-break:break-word; }
.table.small{ table-layout: fixed; }
.table.small th,.table.small td{ font-size: 12px; padding:6px 8px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width: 1px; }
.clamp{ max-width:200px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.table-wrap{ width:100%; overflow:auto; max-width:100%; }
.pager{ display:flex; justify-content:space-between; align-items:center; gap:12px; padding:10px 0; }
.pager-left{ display:flex; align-items:center; gap:8px; }
.pager-right{ display:flex; align-items:center; gap:8px; }
.mini-pager{ display:flex; justify-content:space-between; align-items:center; gap:8px; margin:6px 0 8px; }
.mini-left{ display:flex; align-items:center; gap:6px; }
.mini-right{ display:flex; align-items:center; gap:6px; }
.btn.tiny{ padding:4px 8px; font-size:12px; border-radius:8px; }
.card-chart{ min-height: 320px; }
.chart-canvas{ width:100% !important; height:280px !important; display:block; }
@media (min-width: 1200px){ .chart-canvas{ height:320px !important; } }
@media (max-width: 700px){ .chart-canvas{ height:220px !important; } }

@media (max-width: 1100px){
  .grid-2{ grid-template-columns: 1fr; }
  .grid-3{ grid-template-columns: 1fr; }
}

</style>
