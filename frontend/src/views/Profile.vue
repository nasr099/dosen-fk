<template>
  <div class="profile-layout">
    <!-- Left Sidebar for Filters -->
    <aside class="filter-sidebar card">
      <h3>Filter History</h3>
      <form @submit.prevent="applyFilters">
        <div class="form-group">
          <label for="search">Search</label>
          <input id="search" type="text" v-model="searchQuery" placeholder="Search by set name" />
        </div>
        <div class="form-group">
          <label for="test-set">Test Set</label>
          <select id="test-set" v-model="selectedSet">
            <option value="">All Sets</option>
            <option v-for="s in allSets" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label for="start-date">Start Date</label>
            <input type="date" id="start-date" v-model="startDate">
          </div>
          <div class="form-group">
            <label for="end-date">End Date</label>
            <input type="date" id="end-date" v-model="endDate">
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label for="sort-by">Sort By</label>
            <select id="sort-by" v-model="sortBy">
              <option value="date">Completed Date</option>
              <option value="score">Score</option>
              <option value="set">Set Name</option>
            </select>
          </div>
          <div class="form-group">
            <label for="sort-dir">Order</label>
            <select id="sort-dir" v-model="sortDir">
              <option value="desc">Descending</option>
              <option value="asc">Ascending</option>
            </select>
          </div>
        </div>
        <div class="filter-actions">
          <button type="submit" class="btn">Apply</button>
          <button type="button" class="btn secondary" @click="resetFilters">Reset</button>
        </div>
      </form>
    </aside>

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
          <div class="row"><span class="label">Status</span>
            <span class="value">
              <span :class="['badge', auth.user?.is_active ? 'ok' : 'off']">{{ auth.user?.is_active ? 'Active' : 'Inactive' }}</span>
            </span>
          </div>
          <div class="row"><span class="label">Active Until</span><span class="value">{{ expiryText }}</span></div>
        </div>
      </div>

      <div class="card" style="margin-top: 16px;">
        <h2>Exam History</h2>
        <div v-if="filteredHistory.length === 0">No matching exams found.</div>
        <div v-else class="table-wrap">
          <table class="history-table">
            <thead>
              <tr>
                <th>Completed</th>
                <th>Set</th>
                <th>Score</th>
                <th>Correct</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="e in filteredHistory" :key="e.id">
                <td>{{ formatDate(e.completed_at || e.started_at) }}</td>
                <td>{{ e.set_title || '-' }}</td>
                <td>{{ Math.round(e.score_percentage || 0) }}/100</td>
                <td>{{ e.correct_answers }}/{{ e.total_questions }}</td>
                <td style="text-align: right;">
                  <router-link :to="{ name: 'result', params: { sessionId: e.id } }"><button class="btn">View Result</button></router-link>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue';
import api from '../api/client';
import { useAuthStore } from '../store/auth';

const auth = useAuthStore();
const originalHistory = ref([]);
const filteredHistory = ref([]);
const allSets = ref([]);

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
  const enriched = [];
  const sets = new Set();

  for (const e of data) {
    let set_title = null;
    if (e.question_set_id) {
      try {
        const { data: s } = await api.get(`/sets/${e.question_set_id}`);
        set_title = s.title;
        if (set_title) sets.add(set_title);
      } catch {}
    }
    enriched.push({ ...e, set_title });
  }

  originalHistory.value = enriched;
  filteredHistory.value = enriched; // Initially, show all
  allSets.value = Array.from(sets);
});

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
.profile-layout {
  display: grid;
  /* More compact sidebar width */
  grid-template-columns: clamp(180px, 24vw, 220px) 1fr;
  gap: 16px;
  overflow-x: hidden; /* prevent accidental horizontal scroll */
}

.filter-sidebar { overflow-x: hidden; padding: 8px; max-width: 100%; box-sizing: border-box; }
.filter-sidebar * { min-width: 0; }
.filter-sidebar h3 {
  margin-top: 0;
  border-bottom: 1px solid var(--border);
  padding-bottom: 10px;
}

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
.history-table { width: 100%; border-collapse: collapse; }
.history-table th, .history-table td { padding: 10px 12px; border-bottom: 1px solid #e2e8f0; text-align: left; }
.history-table th { background: #f8fafc; font-weight: 700; color: #0f172a; }

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

/* Responsive */
@media (max-width: 900px) {
  .profile-layout {
    grid-template-columns: 1fr; /* Stack columns */
  }
}

/* Stack row fields on very small screens to avoid overflow */
@media (max-width: 640px) {
  .form-row { grid-template-columns: 1fr; }
}
</style>
