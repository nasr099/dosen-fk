<template>
  <div class="profile-layout single">

    <!-- Main Content -->
    <main class="main-content">
      <div class="card profile-card">
        <div class="avatar" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="72" height="72" role="img">
            <circle cx="12" cy="12" r="12" fill="#0f172a" />
            <circle cx="12" cy="9" r="4" fill="#ffffff" />
            <path d="M4 20c1.8-3.2 5.2-5 8-5s6.2 1.8 8 5" fill="#ffffff" />
          </svg>
        </div>
        <h2 class="profile-title">My Profile</h2>
        <div class="profile-info">
          <div class="row"><span class="label">Name</span><span class="value">{{ auth.user?.full_name || '-' }}</span></div>
          <div class="row"><span class="label">Phone</span><span class="value">{{ auth.user?.phone || '-' }}</span></div>
          <div class="row"><span class="label">Email</span><span class="value">{{ auth.user?.email || '-' }}</span></div>
          <div class="row"><span class="label">Plan</span>
            <span class="value">
              <span :class="['badge', (auth.user?.plan||'free')==='paid' ? 'ok' : 'off']">{{ (auth.user?.plan||'free')==='paid' ? 'Paid' : 'Free' }}</span>
            </span>
          </div>
          <div class="row"><span class="label">Valid Until</span><span class="value">{{ expiryText || '-' }}</span></div>
        </div>
      </div>
      <div class="card" style="padding:12px; display:flex; justify-content:flex-end;">
        <button class="btn small secondary" @click="pwOpen=!pwOpen">
          {{ pwOpen ? 'Hide Change Password' : 'Change Password' }}
        </button>
      </div>
      <!-- Change Password: redesigned -->
      <div class="card pw-card" v-show="pwOpen">
        <div class="pw-head">
          <div class="pw-title-wrap">
            <div class="pw-icon" aria-hidden="true">🔒</div>
            <h2 class="pw-title">Change Password</h2>
          </div>
          <div class="pw-hint">Use at least 8 characters. Mix upper/lowercase and numbers for a stronger password.</div>
        </div>
        <form class="pw-form" @submit.prevent="changePassword">
          <div class="pw-grid">
            <div class="pw-row">
              <label>Current password</label>
              <div class="input-group">
                <input :type="showPwCurrent ? 'text' : 'password'" v-model="pwCurrent" required autocomplete="current-password" />
                <button type="button" class="toggle" @click="showPwCurrent=!showPwCurrent">{{ showPwCurrent ? 'Hide' : 'Show' }}</button>
              </div>
            </div>
            <div class="pw-row">
              <label>New password</label>
              <div class="input-group">
                <input :type="showPwNew ? 'text' : 'password'" v-model="pwNew" required minlength="8" autocomplete="new-password" />
                <button type="button" class="toggle" @click="showPwNew=!showPwNew">{{ showPwNew ? 'Hide' : 'Show' }}</button>
              </div>
              <div class="strength">
                <div class="bar">
                  <span :class="['s1', strengthLevel>=1?'on':'']"></span>
                  <span :class="['s2', strengthLevel>=2?'on':'']"></span>
                  <span :class="['s3', strengthLevel>=3?'on':'']"></span>
                </div>
                <div class="label" :class="strengthClass">{{ strengthLabel }}</div>
              </div>
            </div>
            <div class="pw-row">
              <label>Confirm new password</label>
              <div class="input-group">
                <input :type="showPwNew2 ? 'text' : 'password'" v-model="pwNew2" required minlength="8" autocomplete="new-password" />
                <button type="button" class="toggle" @click="showPwNew2=!showPwNew2">{{ showPwNew2 ? 'Hide' : 'Show' }}</button>
              </div>
              <div v-if="pwNew && pwNew2 && pwNew!==pwNew2" class="mismatch">Passwords do not match</div>
            </div>
          </div>
          <div class="pw-actions">
            <button class="btn" type="submit" :disabled="pwBusy || !canSubmit">{{ pwBusy ? 'Saving…' : 'Change Password' }}</button>
          </div>
        </form>
      </div>

      <!-- Analytics moved below profile -->
      <div class="card" style="margin: 16px 0;">
        <h2>Analytics</h2>
        <div class="ana-controls">
          <label>Test Set</label>
          <select v-model="chartSet">
            <option value="">Select a set…</option>
            <option v-for="s in allSets" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>
        <div v-if="chartPoints.length === 0" class="ana-empty">Select a set to see your score development.</div>
        <div v-else class="ana-chart-wrap">
          <canvas ref="profileChartRef" class="ana-chart-canvas" height="220"></canvas>
          <div class="ana-legend">
            <div class="stat">
              <div class="label">Set</div>
              <div class="value">{{ chartSet }}</div>
            </div>
            <div class="stat">
              <div class="label">Attempts</div>
              <div class="value">{{ chartPoints.length }}</div>
            </div>
            <div class="stat">
              <div class="label">Best</div>
              <div class="value">{{ bestForSet }}/100</div>
            </div>
          </div>
        </div>

        <div class="top3">
          <h3>Top 3 Best Scores <span v-if="chartSet">(for {{ chartSet }})</span></h3>
          <ul class="top3-list">
            <li v-for="t in top3" :key="t.id">
              <div class="t-main">
                <span class="t-title">{{ t.set_title || '-' }}</span>
                <span class="t-score badge">{{ Math.round(t.score_percentage||0) }}/100</span>
              </div>
              <div class="t-sub">{{ formatDate(t.completed_at || t.started_at) }}</div>
            </li>
          </ul>
        </div>
      </div>

      <div class="card" style="margin-top: 16px;">
        <div class="history-head">
          <h2>Exam History</h2>
          <form class="history-filters" @submit.prevent="applyFilters">
            <input type="text" v-model="searchQuery" placeholder="Search by set name" />
            <select v-model="selectedSet">
              <option value="">All Sets</option>
              <option v-for="s in allSets" :key="s" :value="s">{{ s }}</option>
            </select>
            <input type="date" v-model="startDate" />
            <input type="date" v-model="endDate" />
            <select v-model="sortBy">
              <option value="date">Completed Date</option>
              <option value="score">Score</option>
              <option value="set">Set Name</option>
            </select>
            <select v-model="sortDir">
              <option value="desc">Desc</option>
              <option value="asc">Asc</option>
            </select>
            <button class="btn small" type="submit">Apply</button>
            <button class="btn small secondary" type="button" @click="resetFilters">Reset</button>
          </form>
        </div>
        <div v-if="filteredHistory.length === 0">No matching exams found.</div>
        <div v-else class="table-wrap">
          <table class="history-table">
            <thead>
              <tr>
                <th class="completed-col">Completed</th>
                <th>Set</th>
                <th>Score</th>
                <th>Correct</th>
                <th class="action-col"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="e in paginatedHistory" :key="e.id">
                <td class="completed-col">{{ formatDate(e.completed_at || e.started_at) }}</td>
                <td>{{ e.set_title || '-' }}</td>
                <td>{{ Math.round(e.score_percentage || 0) }}/100</td>
                <td>{{ e.correct_answers }}/{{ e.total_questions }}</td>
                <td class="desktop-action" style="text-align: right;">
                  <router-link :to="{ name: 'result', params: { sessionId: e.id } }"><button class="btn small">View Result</button></router-link>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="history-pager">
          <div class="pager-left">
            <label>Rows</label>
            <select v-model.number="pageSize">
              <option :value="10">10</option>
              <option :value="20">20</option>
              <option :value="50">50</option>
            </select>
          </div>
          <div class="pager-right">
            <button class="btn small secondary" :disabled="page<=1" @click="page=page-1">Prev</button>
            <span>Page {{ page }} / {{ pageCount }}</span>
            <button class="btn small" :disabled="page>=pageCount" @click="page=page+1">Next</button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { onMounted, ref, computed, watch, nextTick } from 'vue';
import api from '../api/client';
import { useAuthStore } from '../store/auth';
import Chart from 'chart.js/auto'

const auth = useAuthStore();
// password change state
const pwCurrent = ref('')
const pwNew = ref('')
const pwNew2 = ref('')
const pwBusy = ref(false)
const pwOpen = ref(false)
const showPwCurrent = ref(false)
const showPwNew = ref(false)
const showPwNew2 = ref(false)

const strengthLevel = computed(()=>{
  const v = pwNew.value || ''
  let score = 0
  if (v.length >= 8) score++
  if (/[A-Z]/.test(v) && /[a-z]/.test(v)) score++
  if (/[0-9]/.test(v)) score++
  return Math.min(3, score)
})
const strengthLabel = computed(()=> ['Too short','Okay','Good','Strong'][strengthLevel.value] )
const strengthClass = computed(()=> ['weak','ok','good','strong'][strengthLevel.value] )
const canSubmit = computed(()=> pwCurrent.value && pwNew.value && pwNew2.value && pwNew.value.length>=8 && pwNew.value===pwNew2.value )

async function changePassword(){
  if (pwNew.value !== pwNew2.value){
    alert('New password and confirmation do not match')
    return
  }
  if ((pwNew.value||'').length < 8){
    alert('New password must be at least 8 characters')
    return
  }
  pwBusy.value = true
  try{
    await api.post('/users/me/change-password', { current_password: pwCurrent.value, new_password: pwNew.value })
    alert('Password changed successfully')
    pwCurrent.value = ''
    pwNew.value = ''
    pwNew2.value = ''
    pwOpen.value = false
  }catch(e){
    alert(e?.response?.data?.detail || 'Failed to change password')
  }finally{
    pwBusy.value = false
  }
}
const originalHistory = ref([]);
const filteredHistory = ref([]);
const allSets = ref([]);
const mobileFiltersOpen = ref(false);
// ---------- Analytics state ----------
const chartSet = ref('')
// intrinsic SVG size (fits container via preserveAspectRatio="none")
const chartW = 700, chartH = 300
const padL = 42, padR = 10, padT = 10, padB = 24

// Filter state
const searchQuery = ref('');
const selectedSet = ref('');
const startDate = ref('');
const endDate = ref('');
const sortBy = ref('date'); // date | score | set
const sortDir = ref('desc'); // asc | desc

const expiryText = computed(() => {
  const raw = auth.user?.active_until
  if (!raw) return '-'
  const d = new Date(raw)
  if (isNaN(d.getTime())) return String(raw)
  const dateStr = d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: '2-digit' })
  const now = new Date()
  return d < now ? `${dateStr} (expired)` : dateStr
})

// ---------- Analytics computed/helpers (for Chart.js) ----------
const chartPoints = computed(() => {
  const set = chartSet.value
  if (!set) return []
  return originalHistory.value
    .filter(e => (e.set_title || '') === set)
    .map(e => ({ t: new Date(e.completed_at || e.started_at).getTime(), s: Number(e.score_percentage || 0), id:e.id }))
    .filter(e => !isNaN(e.t))
    .sort((a,b)=> a.t - b.t)
})
const bestForSet = computed(() => chartPoints.value.reduce((m,p)=> Math.max(m, p.s), 0))
const top3 = computed(() => {
  const source = chartSet.value
    ? originalHistory.value.filter(e => (e.set_title||'') === chartSet.value)
    : originalHistory.value
  return [...source]
    .sort((a,b)=> (Number(b.score_percentage||0) - Number(a.score_percentage||0)))
    .slice(0,3)
})

// ------ Chart.js rendering (match AdminAnalytics style) ------
const profileChartRef = ref(null)
let profileChart = null
function renderProfileChart(){
  const pts = chartPoints.value
  if (!profileChartRef.value) return
  const labels = pts.map(p=> new Date(p.t).toLocaleDateString())
  const data = pts.map(p=> Math.round(p.s||0))
  if (profileChart) profileChart.destroy()
  profileChart = new Chart(profileChartRef.value, {
    type: 'line',
    data: { labels, datasets: [
      { label: 'Score %', data, tension: .25, borderColor: '#2563eb', backgroundColor: 'rgba(99,102,241,0.2)', pointRadius: 2, fill: true }
    ]},
    options: { responsive: true, maintainAspectRatio: false, layout:{ padding: { top: 6, right: 8, bottom: 6, left: 8 } }, interaction:{ mode:'index', intersect:false }, plugins:{ tooltip:{ enabled:true }, legend:{ position:'top', labels:{ usePointStyle:false } } }, scales: { y: { min:0, max:100, grid:{ color:'#eef2f7' } }, x:{ grid:{ display:false } } } }
  })
}

watch([chartPoints, chartSet], async ()=>{ await nextTick(); renderProfileChart() })

// Pagination
const page = ref(1)
const pageSize = ref(10)
const pageCount = computed(() => Math.max(1, Math.ceil(filteredHistory.value.length / pageSize.value)))
const paginatedHistory = computed(() => {
  const p = Math.min(page.value, pageCount.value)
  const start = (p - 1) * pageSize.value
  return filteredHistory.value.slice(start, start + pageSize.value)
})

const applyFilters = () => {
  let tempHistory = [...originalHistory.value];

  // Search
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase();
    tempHistory = tempHistory.filter(e => (e.set_title || '-').toLowerCase().includes(q));
  }

  // Set filter
  if (selectedSet.value) {
    tempHistory = tempHistory.filter(e => e.set_title === selectedSet.value);
  }

  // Date range
  if (startDate.value) {
    const start = new Date(startDate.value).setHours(0, 0, 0, 0);
    tempHistory = tempHistory.filter(e => new Date(e.completed_at || e.started_at) >= start);
  }
  if (endDate.value) {
    const end = new Date(endDate.value).setHours(23, 59, 59, 999);
    tempHistory = tempHistory.filter(e => new Date(e.completed_at || e.started_at) <= end);
  }

  // Sorting
  const dir = sortDir.value === 'asc' ? 1 : -1;
  tempHistory.sort((a, b) => {
    if (sortBy.value === 'date') {
      const da = new Date(a.completed_at || a.started_at).getTime();
      const db = new Date(b.completed_at || b.started_at).getTime();
      return (da - db) * dir;
    }
    if (sortBy.value === 'score') {
      const sa = Number(a.score_percentage || 0);
      const sb = Number(b.score_percentage || 0);
      return (sa - sb) * dir;
    }
    // set name
    const na = String(a.set_title || '').toLowerCase();
    const nb = String(b.set_title || '').toLowerCase();
    return (na > nb ? 1 : na < nb ? -1 : 0) * dir;
  });

  filteredHistory.value = tempHistory;
  page.value = 1;
};

const resetFilters = () => {
  searchQuery.value = '';
  selectedSet.value = '';
  startDate.value = '';
  endDate.value = '';
  sortBy.value = 'date';
  sortDir.value = 'desc';
  applyFilters();
};

onMounted(async () => {
  const { data } = await api.get('/exams/history');
  const enriched = Array.isArray(data) ? data : [];
  const sets = new Set(enriched.map(e => e.set_title).filter(Boolean));

  originalHistory.value = enriched;
  filteredHistory.value = enriched;
  allSets.value = Array.from(sets);
  page.value = 1;
  if (!chartSet.value && allSets.value.length > 0){
    chartSet.value = allSets.value[0]
  }
  await nextTick();
  renderProfileChart()
});

// (moved above to be available before watcher)

function formatDate(dt) {
  try {
    if (!dt) return '-'
    let s = String(dt)
    // Detect if timestamp already has timezone (Z or +HH:MM/-HH:MM)
    const hasTZ = /Z|[+-]\d{2}:?\d{2}$/.test(s)
    // If TZ is present, parse as-is. If not, treat as LOCAL time (do NOT append Z)
    let d = hasTZ
      ? new Date(s)
      : new Date(s.includes('T') ? s : s.replace(' ', 'T'))
    // If parsing failed, try normalizing common UI strings like '4/10/2025, 04.18.05 AM'
    if (isNaN(d.getTime())){
      // Replace time separators '.' with ':'
      const parts = s.split(',')
      if (parts.length >= 2){
        const datePart = parts[0].trim()
        let timePart = parts.slice(1).join(',').trim() // handle possible commas
        timePart = timePart.replace(/\./g, ':')
        s = `${datePart} ${timePart}`
      }
      d = new Date(s)
    }
    if (isNaN(d.getTime())) return s
    return d.toLocaleString('en-GB', {
      timeZone: 'Asia/Jakarta',
      year: 'numeric', month: 'numeric', day: 'numeric',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
      hour12: false
    })
  } catch { return String(dt) }
}
</script>

<style scoped>
.profile-layout { display:grid; grid-template-columns: 1fr; gap:16px; overflow-x:hidden; }
.profile-layout > * { min-width:0; }
.main-content{ min-width:0; }

.mobile-filter-bar { display:none; margin-bottom: 8px; }
.btn.small{ padding:6px 10px; font-size:12px; }
.btn.full{ width:100%; }

.history-filters { display:flex; gap:12px; align-items:center; flex-wrap:wrap; margin:8px 0 12px; }
.history-filters input[type="text"], .history-filters select, .history-filters input[type="date"]{ padding:6px 8px; border:1px solid #cbd5e1; border-radius:8px; font-size:12px; }

.history-pager{ width:100%; display:block; text-align:center; padding:20px 0; margin-top:12px; }
.history-pager .pager-left{ display:inline-flex; align-items:center; gap:8px; margin:0 10px; }
.history-pager select{ padding:4px 8px; border:1px solid #cbd5e1; border-radius:8px; font-size:12px; }
.history-pager .pager-right{ display:inline-flex; align-items:center; gap:14px; margin:0 10px; }

.form-group { margin-bottom: 14px; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }

.form-group label { display: block; font-weight: 600; margin-bottom: 6px; }

.form-group select,
.form-group input { width: 100%; max-width: 100%; min-width: 0; padding: 5px 8px; border: 1px solid #cbd5e1; border-radius: 8px; box-sizing: border-box; font-size: 12px; line-height: 1.2; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.filter-sidebar .form-group select { padding-right: 28px; overflow: hidden; text-overflow: ellipsis; }

.filter-actions {
  display: flex;
  gap: 10px;
  margin-top: 14px;
  flex-wrap: wrap;
}

.table-wrap { overflow: auto; }
.history-table { width: 100%; border-collapse: collapse; table-layout: auto; }
.history-table th, .history-table td { padding: 10px 12px; border-bottom: 1px solid #e2e8f0; text-align: left; vertical-align: top; }
.history-table th { background: #f8fafc; font-weight: 700; color: #0f172a; }
.history-table td, .history-table th{ word-break: break-word; }
.history-table .action-col{ width: 120px; }
.mobile-action{ display:none; margin-top:8px; }
.mobile-action-row{ display:none; }

/* Profile card styles */
.profile-card{ display:flex; flex-direction:column; align-items:center; text-align:center; padding: 28px 20px; gap: 14px; }
.profile-card .avatar{ display:flex; align-items:center; justify-content:center; }
.profile-title{ margin: 4px 0 6px 0; }
.profile-info{ display:flex; flex-direction:column; gap: 12px; width:100%; max-width: 520px; margin-top: 4px; }
.profile-info .row{ display:flex; justify-content:center; gap: 10px; }
.profile-info .label{ font-weight: 700; color:#0f172a; }
.profile-info .value{ color:#334155; }
.badge{ padding:3px 10px; border-radius:999px; font-size:12px; font-weight:800; letter-spacing:.2px; }
.badge.ok{ background:linear-gradient(135deg,#34d399,#10b981); color:#064e3b; border:0; box-shadow:0 0 0 1px rgba(16,185,129,.15) inset, 0 6px 16px rgba(16,185,129,.22); }
.badge.off{ background:linear-gradient(135deg,#e2e8f0,#cbd5e1); color:#0f172a; border:0; box-shadow:0 0 0 1px rgba(148,163,184,.25) inset, 0 2px 8px rgba(15,23,42,.06); }

/* Analytics styles */
.ana-controls{ display:flex; align-items:center; gap:10px; margin-top:8px; }
.ana-controls select{ padding:6px 10px; border:1px solid #cbd5e1; border-radius:8px; font-size:12px; }
.ana-empty{ color:#64748b; font-style:italic; margin:10px 0; }
.ana-chart-wrap{ margin-top:10px; width:100%; max-width:none; }
.ana-chart-canvas{ width:100% !important; height:220px !important; display:block; }
.ana-legend{ display:flex; gap:16px; margin-top:8px; flex-wrap:wrap; }
.ana-legend .stat{ background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:8px 12px; min-width:120px; }
.ana-legend .label{ color:#64748b; font-size:12px; }
.ana-legend .value{ font-weight:800; color:#0f172a; font-size:14px; }
.top3{ margin-top:12px; }
.top3 h3{ margin:8px 0; font-size:16px; }
.top3-list{ list-style:none; padding:0; margin:0; display:flex; flex-direction:column; gap:8px; }
.top3-list li{ border:1px solid #e2e8f0; border-radius:10px; padding:8px 10px; background:#fff; }
.top3-list .t-main{ display:flex; justify-content:space-between; align-items:center; gap:8px; }
.top3-list .t-title{ font-weight:700; color:#0f172a; }
.top3-list .t-score{ background:#e0f2fe; color:#075985; border-radius:999px; padding:2px 8px; font-size:12px; font-weight:800; }
.top3-list .t-sub{ color:#64748b; font-size:12px; margin-top:4px; }

/* Password card beautification */
.pw-card{ margin:16px 0; padding:20px; background:linear-gradient(180deg,#ffffff, #fbfdff); border:1px solid #e2e8f0; border-radius:14px; box-shadow: 0 6px 18px rgba(2,6,23,0.04); }
.pw-head{ display:flex; flex-direction:column; gap:6px; margin-bottom:12px; }
.pw-title-wrap{ display:flex; align-items:center; gap:10px; }
.pw-icon{ width:32px; height:32px; display:flex; align-items:center; justify-content:center; background:#eef2ff; border:1px solid #c7d2fe; color:#3730a3; border-radius:10px; font-size:18px; }
.pw-title{ margin:0; }
.pw-hint{ color:#64748b; font-size:12px; }
.pw-form{ display:block; }
.pw-grid{ display:grid; grid-template-columns: repeat(2, 1fr); gap:14px; }
.pw-row{ display:flex; flex-direction:column; gap:6px; }
.pw-row label{ font-weight:700; color:#0f172a; }
.input-group{ display:flex; align-items:center; gap:8px; background:#fff; border:1px solid #cbd5e1; border-radius:10px; padding:6px 8px; }
.input-group input{ flex:1; border:none; outline:none; font-size:14px; }
.input-group .toggle{ border:none; background:#f1f5f9; color:#0f172a; font-weight:600; padding:6px 10px; border-radius:8px; cursor:pointer; }
.input-group .toggle:hover{ filter:brightness(.97); }
.strength{ display:flex; align-items:center; gap:10px; margin-top:4px; }
.strength .bar{ display:inline-flex; gap:6px; }
.strength .bar span{ width:40px; height:6px; background:#e5e7eb; border-radius:999px; display:inline-block; }
.strength .bar span.on.s1{ background:#f87171; }
.strength .bar span.on.s2{ background:#f59e0b; }
.strength .bar span.on.s3{ background:#10b981; }
.strength .label{ font-size:12px; font-weight:700; color:#64748b; }
.strength .label.ok{ color:#d97706; }
.strength .label.good{ color:#16a34a; }
.strength .label.strong{ color:#0d9488; }
.mismatch{ color:#b91c1c; font-size:12px; margin-top:2px; }
.pw-actions{ display:flex; justify-content:flex-end; margin-top:8px; }

@media (max-width: 900px){
  .pw-grid{ grid-template-columns: 1fr; }
}

/* Responsive */
@media (max-width: 900px) {
  .profile-layout {
    grid-template-columns: 1fr; /* Stack columns */
  }
  .mobile-filter-bar { display:flex; }
  .filter-sidebar { display:none; }
  .filter-sidebar.open { display:block; }
  .filter-actions { display:grid; grid-template-columns: 1fr; gap:10px; }
  .filter-actions .btn { width:100%; }
  .card { padding: 12px; }
  .profile-card{ padding: 20px 14px; }
  /* Hide Completed column to save space */
  .history-table thead th.completed-col{ display:none; }
  .history-table tbody td.completed-col{ display:none; }
  /* Keep action button visible inline */
  .desktop-action{ display:table-cell; }
  .history-table .action-col{ width:auto; }
  .history-table td.desktop-action .btn{ width:100%; }
}

/* Stack row fields on very small screens to avoid overflow */
@media (max-width: 640px) {
  .form-row { grid-template-columns: 1fr; }
  .history-table th, .history-table td { padding: 8px 10px; }
}
</style>
