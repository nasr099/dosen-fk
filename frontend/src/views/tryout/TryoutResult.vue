<template>
  <div class="card">
    <h2>Tryout Result</h2>
    <div v-if="loadError" class="err">{{ loadError }}</div>
    <div class="muted" v-else-if="isLoading">Generating result…</div>
    <div class="muted" v-else-if="!rows.length && !summary">No data.</div>
    <!-- Summary panels -->
    <div v-if="summary" class="grid-2">
      <div class="panel">
        <div class="panel-title">Objective (MCQ + Multi + Short)</div>
        <div class="donut-wrap">
          <svg class="donut" viewBox="0 0 42 42" role="img" aria-label="Objective score">
            <circle class="ring" cx="21" cy="21" r="16" />
            <circle class="slice" :stroke-dasharray="score100 + ' ' + (100-score100)" cx="21" cy="21" r="16" />
            <text x="21" y="22" text-anchor="middle" class="donut-text">{{ score100 }}%</text>
          </svg>
          <div class="breakdown">
            <div class="brow"><span class="dot ok"></span> Correct <strong>{{ summary.correct_answers }}</strong></div>
            <div class="brow"><span class="dot bad"></span> Incorrect <strong>{{ objectiveIncorrect }}</strong></div>
            <div class="brow total">Total <strong>{{ summary.total_questions }}</strong></div>
          </div>
        </div>
      </div>
      <div class="panel">
        <div class="panel-title">Essays</div>
        <div class="donut-wrap">
          <svg class="donut" viewBox="0 0 42 42" role="img" aria-label="Essay average">
            <circle class="ring" cx="21" cy="21" r="16" />
            <circle class="slice" :stroke-dasharray="essayAvg + ' ' + (100-essayAvg)" cx="21" cy="21" r="16" />
            <text x="21" y="22" text-anchor="middle" class="donut-text">{{ essayAvg }}%</text>
          </svg>
          <div class="breakdown">
            <div class="brow"><span class="dot ok"></span> Graded <strong>{{ summary.essay_graded_count || 0 }}</strong></div>
            <div class="brow"><span class="dot idle"></span> Pending <strong>{{ (summary.essay_count||0) - (summary.essay_graded_count||0) }}</strong></div>
            <div class="brow total">Total <strong>{{ summary.essay_count || 0 }}</strong></div>
          </div>
        </div>
      </div>
    </div>

    <table v-if="rows.length" class="table">
      <thead>
        <tr>
          <th>Set</th>
          <th>Type</th>
          <th>Total</th>
          <th>Answered</th>
          <th>Correct/Graded</th>
          <th>Score</th>
        </tr>
      </thead>
      <tbody>
        <template v-for="r in rows" :key="'set-'+r.order_index">
          <!-- Objective row (MCQ + Multi + Short) -->
          <tr>
            <td>{{ r.title || r.set_title || (r.set && r.set.title) || ('#' + r.order_index) }}</td>
            <td>Objective</td>
            <td>{{ n(r.objective_total_questions, r.total_questions) }}</td>
            <td>{{ n(r.objective_answered_count, answeredOf(r)) }}</td>
            <td>{{ n(r.objective_correct_count, r.correct_count) }}</td>
            <td>{{ pct(r.objective_score_percentage, r.score_percentage) }}</td>
          </tr>
          <!-- Essays row -->
          <tr>
            <td>{{ r.title || r.set_title || (r.set && r.set.title) || ('#' + r.order_index) }}</td>
            <td>Essays</td>
            <td>{{ n(r.essay_total_questions, 0) }}</td>
            <td>{{ n(r.essay_answered_count, 0) }}</td>
            <td>{{ n(r.essay_graded_count, 0) }}</td>
            <td>{{ pct(r.essay_avg_score, 0) }}</td>
          </tr>
        </template>
      </tbody>
    </table>
    <router-link class="btn" to="/profile" style="margin-top:12px; display:inline-block;">Back to Profile</router-link>
  </div>
</template>
<script setup>
import { onMounted, ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import api from '../../api/client'

const route = useRoute()
const sessionId = Number(route.params.sessionId)
const loaded = ref(false)
const rows = ref([])
const overall = ref(0)
const loadError = ref('')
const isLoading = ref(false)
let retryTimer = null
const summary = ref(null)

// Summary computed
const score100 = computed(() => Math.round(summary.value?.score_percentage ?? (overall.value || 0)))
const essayAvg = computed(() => Math.round(summary.value?.essay_avg_score ?? 0))
const objectiveIncorrect = computed(() => {
  const total = Number(summary.value?.total_questions || 0)
  const correct = Number(summary.value?.correct_answers || 0)
  const inc = total - correct
  return inc < 0 ? 0 : inc
})

async function fetchResult(){
  try{
    isLoading.value = true
    const { data } = await api.get(`/tryouts/sessions/${sessionId}/result`)
    const list = Array.isArray(data) ? data : (data.sets || data.results || [])
    rows.value = Array.isArray(list) ? list : []
    overall.value = data.overall_score ?? data.overall ?? data.score ?? 0
    summary.value = {
      total_questions: data.total_questions ?? 0,
      correct_answers: data.correct_answers ?? 0,
      score_percentage: data.score_percentage ?? overall.value,
      essay_count: data.essay_count ?? 0,
      essay_graded_count: data.essay_graded_count ?? 0,
      essay_avg_score: data.essay_avg_score ?? 0,
    }
    if (!rows.value.length){
      // If backend not ready yet, retry a few times
      scheduleRetry()
    } else {
      clearRetry()
    }
  } catch (e) {
    const status = e?.response?.status
    // If 404/204 or transient, retry briefly
    if ([202,204,404,409].includes(Number(status))){ scheduleRetry() }
    else {
      const msg = e?.response?.data?.detail || e?.message || 'Failed to load result'
      loadError.value = `Error ${status || ''} ${msg}`.trim()
      clearRetry()
    }
  } finally {
    isLoading.value = false
    loaded.value = true
  }
}

function scheduleRetry(){
  clearRetry()
  retryTimer = setTimeout(fetchResult, 1200)
}
function clearRetry(){
  try{ if (retryTimer) clearTimeout(retryTimer) }catch{}
  retryTimer = null
}

onMounted(fetchResult)

// Helpers: compute answered when detailed answers are provided in payload
function answeredOf(row){
  // Prefer explicit API field if no details provided
  const arr = Array.isArray(row.answers) ? row.answers : []
  if (!arr.length) return row.answered_count ?? 0
  // Many APIs return multiple records per question (edit history). Count unique question_ids with a non-empty final selection.
  const latestByQ = new Map()
  for (const a of arr){
    const qid = a?.question_id ?? a?.qid ?? a?.question?.id
    if (!qid) continue
    latestByQ.set(qid, a)
  }
  let n = 0
  latestByQ.forEach((a) => {
    const s1 = String(a?.selected_answer || '').trim()
    const s2 = String(a?.selected_multi || '').trim()
    const essay = String(a?.essay_answer || '').trim()
    if (s1 || s2 || essay) n++
  })
  return n
}

// Safe number helpers (module scope)
function n(primary, fallback){
  const a = Number(primary)
  if (!Number.isNaN(a) && a !== undefined && a !== null) return a
  const b = Number(fallback)
  return Number.isNaN(b) ? 0 : b
}
function pct(primary, fallback){
  const a = Number(primary)
  const val = (!Number.isNaN(a) && a !== undefined && a !== null) ? a : Number(fallback || 0)
  return `${val.toFixed(1)}%`
}
</script>
<style scoped>
.table{ width:100%; border-collapse:separate; border-spacing:0; margin-top:12px; border:1px solid #e5e7eb; border-radius:12px; overflow:hidden; background:#fff; }
.table thead th{ background:#f8fafc; font-weight:700; color:#0f172a; }
.table th{ text-align:left; padding:10px 12px; border-bottom:1px solid #e2e8f0; }
.table td{ padding:10px 12px; border-bottom:1px solid #e2e8f0; }
.table tbody tr:nth-child(2n){ background:#fafafa; }
.table tbody tr:hover{ background:#f1f5f9; }
.muted{ color:#64748b }
.err{ color:#b91c1c }
/* Panels styling similar to exam Result */
.grid-2{ display:grid; grid-template-columns: repeat(2,1fr); gap:18px; margin:14px 0 10px; }
.panel{ border:1px solid #e5e7eb; border-radius:12px; padding:14px; background:#fff; }
.panel-title{ font-weight:700; margin-bottom:10px; }
.donut-wrap{ display:flex; align-items:center; gap:18px; }
.donut{ width:130px; height:130px; }
.ring{ fill:none; stroke:#e5e7eb; stroke-width:6; }
.slice{ fill:none; stroke:#16a34a; stroke-width:6; stroke-linecap:round; transform: rotate(-90deg); transform-origin: 50% 50%; }
.donut-text{ font-size:12px; dominant-baseline:middle; font-weight:800; fill:#111827; }
.breakdown{ display:flex; flex-direction:column; gap:6px; font-size:14px; }
.brow{ display:flex; align-items:center; gap:8px; }
.brow.total{ margin-top:6px; font-weight:700; }
.dot{ width:10px; height:10px; border-radius:999px; display:inline-block; border:1px solid #cbd5e1; }
.dot.ok{ background:#16a34a; border-color:#16a34a; }
.dot.bad{ background:#ef4444; border-color:#ef4444; }
.dot.idle{ background:#e5e7eb; }
@media (max-width: 600px){
  .grid-2{ grid-template-columns: 1fr; }
  .table td, .table th{ font-size: 14px; }
}
</style>
