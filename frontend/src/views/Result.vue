<template>
  <div class="card result-card" v-if="result">
    <h2 class="result-title">Result</h2>
    <div class="grid-2">
      <div class="panel">
        <div class="panel-title">Objective (MCQ + Multi)</div>
        <div class="donut-wrap">
          <svg class="donut" viewBox="0 0 42 42" role="img" aria-label="Objective score">
            <circle class="ring" cx="21" cy="21" r="16" />
            <circle class="slice" :stroke-dasharray="score100 + ' ' + (100-score100)" cx="21" cy="21" r="16" />
            <text x="21" y="22" text-anchor="middle" class="donut-text">{{ score100 }}%</text>
          </svg>
          <div class="breakdown">
            <div class="brow"><span class="dot ok"></span> Correct <strong>{{ result.correct_answers }}</strong></div>
            <div class="brow"><span class="dot bad"></span> Incorrect <strong>{{ objectiveIncorrect }}</strong></div>
            <div class="brow"><span class="dot idle"></span> Unanswered <strong>{{ objectiveUnanswered }}</strong></div>
            <div class="brow total">Total <strong>{{ result.total_questions }}</strong></div>
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
            <div class="brow"><span class="dot ok"></span> Graded <strong>{{ result.essay_graded_count || 0 }}</strong></div>
            <div class="brow"><span class="dot idle"></span> Pending <strong>{{ (result.essay_count||0) - (result.essay_graded_count||0) }}</strong></div>
            <div class="brow total">Total <strong>{{ result.essay_count || 0 }}</strong></div>
          </div>
        </div>
      </div>
    </div>

    <h3 class="answers-title">Answers</h3>
    <div v-if="(result.answers||[]).length === 0" class="muted">No answers recorded.</div>
    <div v-for="(a, i) in result.answers" :key="a.question_id || i" class="card answer-card">
      <div class="answer-head">
        <div class="left">
          <div class="qnum">Q{{ i + 1 }}</div>
          <div class="qtitle">Question:</div>
        </div>
        <div class="right" v-if="(a.question_type||'mcq') !== 'essay'">
          <span class="abadge" :class="answerStatusClass(a)">{{ answerStatusText(a) }}</span>
        </div>
      </div>
      <div class="qwrap">
        <div v-if="qDetail(a).text" class="qtext" v-html="renderHTML(qDetail(a).text)"></div>
        <img v-if="qDetail(a).img" :src="resolveImg(qDetail(a).img)" alt="Question" class="qimg" />
      </div>

      <template v-if="(a.question_type || 'mcq') === 'essay'">
        <div class="essay-wrap">
          <div class="essay-label"><strong>Your answer:</strong></div>
          <div class="essay-box" v-if="(a.selected_answer||'').trim()">{{ a.selected_answer }}</div>
          <div class="essay-box empty" v-else>-</div>
        </div>
      </template>
      <template v-else-if="(a.question_type || 'mcq') === 'multi'">
        <div class="row">
          <div class="col">
            <div><strong>Selected:</strong></div>
            <div class="chips">
              <span v-for="l in selectedLetters(a)" :key="'s-'+l" class="chip" :class="{ good: correctLetters(a).includes(l), bad: !correctLetters(a).includes(l) }">{{ l }}</span>
              <span v-if="selectedLetters(a).length===0" class="muted">-</span>
            </div>
          </div>
          <div class="col" v-if="isPremium">
            <div><strong>Correct:</strong></div>
            <div class="chips">
              <span v-for="l in correctLetters(a)" :key="'c-'+l" class="chip good">{{ l }}</span>
              <span v-if="correctLetters(a).length===0" class="muted">-</span>
            </div>
          </div>
        </div>
      </template>
      <template v-else>
        <div class="row">
          <div class="col">
            <div><strong>Selected:</strong> <span :class="a.is_correct ? 'good' : 'bad'">{{ a.selected_answer || '-' }}</span></div>
            <div v-if="sDetail(a).text || sDetail(a).img" class="ans-detail">
              <img v-if="sDetail(a).img" :src="resolveImg(sDetail(a).img)" alt="Selected answer" />
              <div v-if="sDetail(a).text" class="text" v-html="renderHTML(sDetail(a).text)"></div>
            </div>
          </div>
          <div class="col" v-if="isPremium">
            <div><strong>Correct:</strong> <span class="good">{{ a.correct_answer }}</span></div>
            <div v-if="cDetail(a).text || cDetail(a).img" class="ans-detail">
              <img v-if="cDetail(a).img" :src="resolveImg(cDetail(a).img)" alt="Correct answer" />
              <div v-if="cDetail(a).text" class="text" v-html="renderHTML(cDetail(a).text)"></div>
            </div>
          </div>
        </div>
      </template>

      <div class="explain" v-if="isPremium && (a.question_type||'mcq') !== 'essay'">
        <div class="explain-label"><strong>Explanation:</strong></div>
        <div v-if="a.explanation" class="explain-box" v-html="renderHTML(a.explanation)"></div>
        <div v-else class="explain-box empty">-</div>
      </div>
      <div v-if="(a.question_type || 'mcq') === 'essay'" class="notes">
        <div class="notes-label"><strong>Essay grade:</strong></div>
        <template v-if="a.essay_grade">
          <div class="grade-row">
            <span class="badge" :class="a.essay_grade.status">{{ a.essay_grade.status }}</span>
            <span class="score">{{ a.essay_grade.score }}/100</span>
          </div>
          <div v-if="isPremium && a.essay_grade.notes" class="notes-box">{{ a.essay_grade.notes }}</div>
          <div v-else-if="isPremium" class="notes-box empty">No notes</div>
        </template>
        <template v-else>
          <div class="notes-box empty">Pending manual review</div>
        </template>
      </div>
    </div>
  </div>
</template>
<script setup>
import { onMounted, ref, computed } from 'vue'
import api from '../api/client'
import { useRoute } from 'vue-router'
import { renderMathHTML } from '../utils/math'
import { useAuthStore } from '../store/auth'

const route = useRoute()
const auth = useAuthStore()
const isPremium = computed(() => {
  // Paid plan OR staff (admin/teacher)
  const planPaid = String(auth.user?.plan || '').toLowerCase() === 'paid'
  return planPaid || auth.isAdmin || auth.isTeacher
})
const result = ref(null)
const score100 = computed(() => Math.round(result.value?.score_percentage ?? 0))
const essayAvg = computed(() => Math.round(result.value?.essay_avg_score ?? 0))

// Objective counters (based on backend payload)
const objectiveAnswered = computed(() => {
  const arr = result.value?.answers || []
  return arr.filter(a => (a.question_type==='mcq' || a.question_type==='multi') && (a.selected_answer||'').trim()).length
})
const objectiveIncorrect = computed(() => {
  const arr = result.value?.answers || []
  return arr.filter(a => (a.question_type==='mcq' || a.question_type==='multi') && (a.selected_answer||'').trim() && !a.is_correct).length
})
const objectiveUnanswered = computed(() => Math.max(0, (result.value?.total_questions||0) - objectiveAnswered.value))

// Heuristics to read answer detail fields coming from backend
const pickFirst = (obj, keys) => {
  for (const k of keys) {
    const v = obj?.[k]
    if (v !== undefined && v !== null && String(v).trim() !== '') return v
  }
  return null
}

function asLetters(val){
  if (!val) return []
  if (Array.isArray(val)) return val.map(x => String(x).toUpperCase())
  return String(val).split(',').map(s => s.trim().toUpperCase()).filter(Boolean)
}
function selectedLetters(a){
  return asLetters(a.selected_multi || a.selected_answer)
}
function correctLetters(a){
  return asLetters(a.correct_multi || a.correct_answer)
}

// Very small sanitizer: allow a limited set of tags/attributes used by our editor
function renderHTML(html){
  const ALLOWED_TAGS = new Set(['P','B','I','U','S','STRONG','EM','UL','OL','LI','H1','H2','H3','H4','BLOCKQUOTE','A','IMG','CODE','PRE','SUB','SUP','HR','BR','DIV','SPAN'])
  const ALLOWED_ATTR = new Set(['href','src','alt','target','rel','style'])
  const div = document.createElement('div')
  div.innerHTML = String(html || '')
  ;[...div.querySelectorAll('script,style')].forEach(n => n.remove())
  ;(function clean(node){
    ;[...node.children].forEach(ch => {
      if (!ALLOWED_TAGS.has(ch.tagName)) { ch.replaceWith(...ch.childNodes); return }
      ;[...ch.attributes].forEach(attr => { if (!ALLOWED_ATTR.has(attr.name) || attr.name.startsWith('on')) ch.removeAttribute(attr.name) })
      clean(ch)
    })
  
  // --- Per-answer correctness label helpers ---
  function hasSelection(a){
    const s1 = String(a?.selected_answer || '').trim()
    const s2 = String(a?.selected_multi || '').trim()
    return !!(s1 || s2)
  }
  function answerStatusClass(a){
    if (!(a && (a.question_type||'mcq') !== 'essay')) return 'idle'
    if (!hasSelection(a)) return 'idle'
    return a.is_correct ? 'ok' : 'bad'
  }
  function answerStatusText(a){
    if (!(a && (a.question_type||'mcq') !== 'essay')) return ''
    if (!hasSelection(a)) return 'Unanswered'
    return a.is_correct ? 'Correct' : 'Not Correct'
  }
  })(div)
  // After sanitizing, render math using KaTeX for $...$ and $$...$$ within text nodes
  return renderMathHTML(div.innerHTML)
}

function resolveImg(src){
  if (!src) return ''
  const s = String(src)
  if (/^https?:\/\//i.test(s) || s.startsWith('data:image')) return s
  // normalize leading slash
  const path = s.startsWith('/') ? s : `/${s}`
  // if points to uploads, prefix backend origin (replace 5173 with 8000)
  if (path.startsWith('/uploads/')){
    return `${window.location.origin.replace('5173','8000')}${path}`
  }
  return path
}
const toDetail = (val) => {
  // Accept object {text, img} | string URL | string text
  if (!val) return { text: '', img: '' }
  if (typeof val === 'object') {
    return { text: val.text || '', img: val.img || val.image || val.image_url || '' }
  }
  const s = String(val)
  const isImg = s.startsWith('data:image') || /(\.png|\.jpg|\.jpeg|\.gif|\.webp|\.svg)(\?.*)?$/i.test(s)
  return isImg ? { text: '', img: s } : { text: s, img: '' }
}
const sDetail = (a) => toDetail(pickFirst(a, ['selected_detail','selected_text','selected_value','selected_content','selectedAnswerDetail','selectedAnswerText']))
const cDetail = (a) => toDetail(pickFirst(a, ['correct_detail','correct_text','correct_value','correct_content','correctAnswerDetail','correctAnswerText']))
const qDetail = (a) => {
  // question_text may be JSON with {text,img} or plain string
  const raw = a?.question_text
  if (!raw) return { text: '', img: '' }
  if (typeof raw === 'object') return toDetail(raw)
  try {
    const obj = JSON.parse(String(raw))
    return toDetail(obj)
  } catch (e) {
    return { text: String(raw), img: '' }
  }
}

// --- Per-answer correctness label helpers (non-essay) ---
function hasSelection(a){
  const s1 = String(a?.selected_answer || '').trim()
  const s2 = String(a?.selected_multi || '').trim()
  return !!(s1 || s2)
}
function answerStatusClass(a){
  if (!(a && (a.question_type||'mcq') !== 'essay')) return 'idle'
  if (!hasSelection(a)) return 'idle'
  return a.is_correct ? 'ok' : 'bad'
}
function answerStatusText(a){
  if (!(a && (a.question_type||'mcq') !== 'essay')) return ''
  if (!hasSelection(a)) return 'Unanswered'
  return a.is_correct ? 'Correct' : 'Not Correct'
}

onMounted(async () => {
  const sessionId = Number(route.params.sessionId)
  try {
    const { data } = await api.get(`/exams/result/${sessionId}`)
    result.value = data
  } catch (e) {
    // fallback: try history (won't include answers)
    const { data } = await api.get('/exams/history')
    const h = data.find(x => x.id === sessionId)
    if (h) {
      result.value = { exam_session_id: h.id, total_questions: h.total_questions, correct_answers: h.correct_answers, score_percentage: h.score_percentage, time_taken_minutes: h.time_taken_minutes || 0, answers: [] }
    }
  }
})
</script>

<style scoped>
.muted { color:#64748b; }
.good { color:#16a34a; }
.bad { color:#dc2626; }
/* Layout spacing */
.result-card{ padding: 22px; }
.result-title{ margin: 0 0 8px 0; }
.result-meta{ margin: 6px 0; }
/* Grid layout for two donuts */
.grid-2{ display:grid; grid-template-columns: repeat(2,1fr); gap:18px; margin:14px 0 4px; }
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

.answers-title{ margin: 18px 0 10px; }
.answer-card{ margin-top:22px; padding:20px; }
.answer-head{ display:flex; justify-content:space-between; align-items:center; gap:10px; margin-bottom:6px; }
.answer-head .left{ display:flex; align-items:center; gap:10px; }
.answer-head .qtitle{ font-weight:700; }
.abadge{ display:inline-block; padding:4px 10px; border-radius:999px; font-size:12px; font-weight:800; border:1px solid #e2e8f0; background:#f8fafc; color:#0f172a; }
.abadge.ok{ background:#dcfce7; border-color:#bbf7d0; color:#065f46; }
.abadge.bad{ background:#fee2e2; border-color:#fecaca; color:#991b1b; }
.abadge.idle{ background:#f1f5f9; color:#475569; }
.qnum{ background:#111827; color:#fff; border-radius:6px; padding:2px 8px; font-weight:800; font-size:12px; letter-spacing:.5px; }
.explain{ margin-top:12px; }
.row{ display:flex; gap:24px; margin-top:8px; }
.col{ flex:1; min-width:0; }
.ans-detail{ margin-top:8px; }
/* Smaller images for answer details */
.ans-detail img{ max-width:100%; width:auto; max-height:160px; height:auto; object-fit:contain; border-radius:8px; border:1px solid #e5e7eb; background:#fff; }
.ans-detail .text{ background:#f8fafc; border:1px solid #e5e7eb; border-radius:8px; padding:10px; white-space:pre-wrap; line-height:1.75; }
.chips{ display:flex; flex-wrap:wrap; gap:8px; margin-top:8px; }
.chip{ display:inline-flex; align-items:center; justify-content:center; min-width:28px; height:28px; padding:0 10px; border-radius:999px; font-weight:800; border:1px solid #e2e8f0; background:#f8fafc; color:#0f172a; }
.chip.good{ background:#dcfce7; border-color:#bbf7d0; color:#065f46; }
.chip.bad{ background:#fee2e2; border-color:#fecaca; color:#991b1b; }
.qtext{ white-space:pre-line; line-height:1.85; letter-spacing:0.1px; }
.explain{ line-height:1.75; }
.qwrap{ display:flex; flex-direction:column; gap:12px; }
.explain-label{ margin-bottom:6px; color:#0f172a; }
.explain-box{ background:#f1f5f9; border:1px solid #e2e8f0; border-radius:10px; padding:12px; overflow:auto; }
.explain-box :where(p,ul,ol,li,h1,h2,h3,h4,blockquote,pre,code){ margin: 0 0 10px 0; }
.explain-box :deep(img){ max-width:100%; width:auto; max-height:160px; height:auto; object-fit:contain; border-radius:8px; border:1px solid #e5e7eb; background:#fff; }
.explain-box.empty{ color:#64748b; font-style:italic; }
.essay-wrap{ margin: 12px 0 14px; }
.essay-label{ margin-bottom:6px; color:#0f172a; }
.essay-box{ background:#f1f5f9; border:1px solid #e2e8f0; border-radius:10px; padding:14px; white-space:pre-wrap; line-height:1.9; }
.essay-box.empty{ color:#64748b; font-style:italic; }
.notes{ margin-top:14px; }
.notes-label{ margin-bottom:6px; color:#0f172a; }
.notes-box{ background:#fff7ed; border:1px solid #fed7aa; border-radius:10px; padding:14px; color:#92400e; }
.notes-box.empty{ color:#b45309; font-style:italic; }
.grade-row{ display:flex; align-items:center; gap:10px; margin-bottom:8px; }
.badge{ display:inline-block; padding:3px 10px; border-radius:999px; font-size:12px; background:#e2e8f0; color:#0f172a; border:1px solid #cbd5e1; }
.badge.approved{ background:#dcfce7; color:#065f46; border-color:#bbf7d0; }
.badge.partial{ background:#fef9c3; color:#713f12; border-color:#fde68a; }
.badge.incorrect{ background:#fee2e2; color:#7f1d1d; border-color:#fecaca; }
.score{ font-weight:700; }
.qimg{ max-width:100%; width:auto; max-height:300px; height:auto; object-fit:contain; border-radius:8px; border:1px solid #e5e7eb; background:#fff; }
@media (max-width: 600px){
  .row{ gap:12px; }
  .grid-2{ grid-template-columns: 1fr; }
  .ans-detail img{ max-height:140px; }
  .qimg{ max-height:220px; }
}
</style>
