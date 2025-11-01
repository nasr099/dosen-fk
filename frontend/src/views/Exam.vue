<template>
  <div class="card" v-if="loaded">
    <div class="exam-header">
      <h2>{{ setTitle || 'Exam' }}</h2>
      <div class="time"><strong>Time Left:</strong> {{ minutes }}:{{ seconds.toString().padStart(2,'0') }}</div>
    </div>
    <div class="guard-bar">
      <span class="dot" :class="{ ok: !inViolation, warn: inViolation }"></span>
      Keep the exam in fullscreen and this tab active. Violations {{ violations }} / {{ VIOLATION_LIMIT }}.
    </div>
    <div class="exam-body">
      <div class="left">
        <div v-for="(q, idx) in questions" :key="q.id">
          <div v-if="idx === currentIndex" class="question-card" :id="`qcard-${idx}`">
          <div v-if="q.reading_id && readingById(q.reading_id)" class="reading-card" :class="{ collapsed: collapsedReading[q.reading_id] }">
            <div class="reading-head">
              <strong class="reading-title">{{ readingById(q.reading_id).title }}</strong>
              <button class="btn tiny secondary" @click="toggleReading(q.reading_id)">{{ collapsedReading[q.reading_id] ? 'Show' : 'Hide' }}</button>
            </div>
            <div class="reading-body" v-show="!collapsedReading[q.reading_id]" v-html="renderHTML(readingById(q.reading_id).content_html)"></div>
            <div class="q-divider" style="margin-top:8px;"></div>
          </div>
          <div class="q-top">
            <div class="q-top-left"><span class="pill strong">Soal {{ idx+1 }}</span><span class="of">dari {{ questions.length }}</span></div>
            <div class="q-top-right">
              <span v-if="(q.question_type||'mcq')==='essay'" class="type-pill">Essay</span>
              <span v-else-if="(q.question_type||'mcq')==='multi'" class="type-pill alt">Multi</span>
              <span class="status" :class="statusClass(currentQuestionId)">{{ statusText(currentQuestionId) }}</span>
            </div>
          </div>
          <img
            v-if="parseRich(q.question_text).img"
            :src="resolveImg(parseRich(q.question_text).img)"
            alt="question image"
            class="q-img"
            @click="openLightbox(resolveImg(parseRich(q.question_text).img))"
          />
          <div class="qtext">
            <span v-if="parseRich(q.question_text).text" v-html="renderHTML(parseRich(q.question_text).text)"></span>
          </div>
          <div class="q-divider"></div>
          <div class="answers-label">Jawaban</div>
          <template v-if="(q.question_type||'mcq') === 'essay'">
            <textarea class="essay-input" v-model="answers[q.id]" @input="markAnswered(q.id)" placeholder="Ketik jawaban Anda di sini..."></textarea>
          </template>
          <div v-else-if="(q.question_type||'mcq') === 'multi'" class="options grid-2">
            <label v-for="opt in availableOptions(q)" :key="opt" class="opt" :class="{ selected: (answers[q.id]||[]).includes(opt) }">
              <input class="radio" type="checkbox" :name="`q_${q.id}_${opt}`" :value="opt" :checked="(answers[q.id]||[]).includes(opt)"
                     @change="toggleMultiAnswer(q.id, opt, $event)" />
              <span class="letter">{{ opt }}</span>
              <span class="opt-content">
                <span class="opt-text" v-if="parseOption(q, opt).text" v-html="renderHTML(parseOption(q, opt).text)"></span>
                <img
                  v-if="parseOption(q, opt).img"
                  :src="resolveImg(parseOption(q, opt).img)"
                  :alt="`option ${opt} image`"
                  class="opt-img"
                  @click="openLightbox(resolveImg(parseOption(q, opt).img))"
                />
              </span>
            </label>
          </div>
          <div v-else class="options grid-2">
            <label v-for="opt in availableOptions(q)" :key="opt" class="opt" :class="{ selected: answers[q.id]===opt }">
              <input class="radio" type="radio" :name="`q_${q.id}`" :value="opt" v-model="answers[q.id]" @change="markAnswered(q.id)" />
              <span class="letter">{{ opt }}</span>
              <span class="opt-content">
                <span class="opt-text" v-if="parseOption(q, opt).text" v-html="renderHTML(parseOption(q, opt).text)"></span>
                <img
                  v-if="parseOption(q, opt).img"
                  :src="resolveImg(parseOption(q, opt).img)"
                  :alt="`option ${opt} image`"
                  class="opt-img"
                  @click="openLightbox(resolveImg(parseOption(q, opt).img))"
                />
              </span>
            </label>
          </div>
          </div>
        </div>
        <div class="nav-row">
          <button class="btn secondary" :disabled="currentIndex===0" @click="prev">‹ Sebelumnya</button>
          <button class="btn warn" @click="toggleFlag(currentQuestionId)">
            {{ isFlagged(currentQuestionId) ? 'Batalkan Ragu-ragu' : 'Ragu-ragu' }}
          </button>
          <button class="btn" :disabled="currentIndex===questions.length-1" @click="next">Selanjutnya ›</button>
        </div>

        <button class="btn" style="margin-top:12px;" @click="openConfirm">Submit</button>
      </div>
      <div class="right">
        <div class="progress-wrap">
          <div class="grid compact">
            <button
              v-for="(q, idx) in questions"
              :key="q.id"
              class="cell"
              :class="[statusClass(q.id), (q.question_type||'mcq')]"
              @click="go(idx)"
            >
              {{ idx+1 }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="lightboxUrl" class="lightbox" @click="closeLightbox">
      <img :src="lightboxUrl" alt="preview" class="lightbox-img" />
    </div>

    <!-- Submit confirmation modal -->
    <div v-if="showConfirm" class="modal-overlay" @click.self="closeConfirm">
      <div class="modal">
        <div class="modal-head">Submit Answers?</div>
        <div class="modal-body">
          <p>Are you sure you want to submit? This action cannot be undone.</p>
          <p><strong>Progress:</strong> {{ answeredCount }} / {{ totalCount }} answered</p>
        </div>
        <div class="modal-actions">
          <button class="btn secondary" @click="closeConfirm">Cancel</button>
          <button class="btn" @click="confirmSubmit" :disabled="isSubmitting">Yes, Submit</button>
        </div>
      </div>
    </div>

    <!-- Re-login required modal -->
    <div v-if="showAuthModal" class="modal-overlay" @click.self="closeAuthModal">
      <div class="modal">
        <div class="modal-head">Session Expired</div>
        <div class="modal-body">
          <p>Your session has expired or is invalid. Please login again to submit your answers.</p>
        </div>
        <div class="modal-actions">
          <button class="btn secondary" @click="closeAuthModal">Cancel</button>
          <button class="btn" @click="goLogin">Login to Continue</button>
        </div>
      </div>
    </div>

    <!-- Violation reached modal -->
    <div v-if="endedByViolation" class="modal-overlay">
      <div class="modal">
        <div class="modal-head">Exam Stopped</div>
        <div class="modal-body">
          <p>Focus rules were violated {{ violations }} times. Your exam will be submitted automatically.</p>
          <p v-if="submitError" style="margin-top:10px;color:#b91c1c;">{{ submitError }}</p>
        </div>
        <div class="modal-actions">
          <button v-if="isSubmitting" class="btn" disabled>Submitting…</button>
          <button v-else class="btn" @click="retrySubmitNow">Retry now</button>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { onMounted, onUnmounted, ref, computed, watch, nextTick } from 'vue'
import api from '../api/client'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'
import { renderMathHTML } from '../utils/math'
import renderMathInElement from 'katex/contrib/auto-render/auto-render'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const categoryId = Number(route.params.categoryId)
const setId = route.query.setId ? Number(route.query.setId) : null

const loaded = ref(false)
const examSessionId = ref(null)
const totalQuestions = ref(0)
const questions = ref([])
const readingsMap = ref({})
const answers = ref({})
const collapsedReading = ref({})

// helpers for rendering reading passages
function readingById(id){
  if (!id) return null
  return readingsMap.value[id] || null
}
function toggleReading(id){
  if (!id) return
  collapsedReading.value[id] = !collapsedReading.value[id]
}

onUnmounted(() => {
  removeGuards()
})
const minutes = ref(0)
const seconds = ref(0)
const timeLimitInitial = ref(60)
let timer = null
const lightboxUrl = ref('')
const currentIndex = ref(0)
const flagged = ref({})
const currentQuestionId = computed(() => questions.value[currentIndex.value]?.id)
const answeredCount = computed(() => Object.values(answers.value).filter(Boolean).length)
const totalCount = computed(() => questions.value.length || totalQuestions.value)
const setTitle = ref('')

// UI state used by template (must be defined early)
const isSubmitting = ref(false)
const showConfirm = ref(false)
const showAuthModal = ref(false)
const submitError = ref('')
const pendingSubmitCache = ref(null)

// --- Anti-cheat state ---
const violations = ref(0)
const VIOLATION_LIMIT = 3
const inViolation = computed(()=> violations.value > 0)
const endedByViolation = ref(false)
let unsubs = []
let fullscreenRequested = false
let guardTick = null
let wasFullscreen = false
let lastViolationTs = 0

function maybeViolate(reason){
  const now = Date.now()
  // Debounce multiple events firing at once
  if (now - lastViolationTs > 1200){
    addViolation(reason)
    lastViolationTs = now
  }
}
function addViolation(reason){
  if (endedByViolation.value) return
  violations.value = Math.min(VIOLATION_LIMIT, violations.value + 1)
  try { console.warn('Violation:', reason, violations.value, '/', VIOLATION_LIMIT) } catch {}
  if (violations.value >= VIOLATION_LIMIT){
    endForViolation()
  }
}

async function endForViolation(){
  if (endedByViolation.value) return
  endedByViolation.value = true
  removeGuards()
  try { if (document.fullscreenElement) await document.exitFullscreen() } catch {}
  // Auto-submit with current answers immediately (guarded)
  if (!isSubmitting.value) {
    await submit()
  }
}

async function requestFullscreen(){
  const el = document.documentElement
  if (!document.fullscreenElement && el?.requestFullscreen){
    fullscreenRequested = true
    try { await el.requestFullscreen() } catch {}
  }
}

function ensureFullscreen(){
  if (!document.fullscreenElement){
    requestFullscreen()
  }
}

function onFullscreenChange(){
  if (!document.fullscreenElement && fullscreenRequested){
    maybeViolate('exit-fullscreen')
    // attempt to re-enter
    requestFullscreen()
  }
}

function onVisibility(){
  if (document.hidden){ maybeViolate('tab-hidden') }
}

function onBlur(){ maybeViolate('window-blur') }
function blockContextMenu(e){ e.preventDefault() }
function blockClipboard(e){ e.preventDefault() }
function onKeydown(e){
  const k = e.key.toLowerCase()
  const meta = e.ctrlKey || e.metaKey
  // Block common shortcuts: copy/print/save/find/devtools
  if (meta && ['c','p','s','f'].includes(k)) { e.preventDefault(); addViolation('shortcut-'+k) }
  // F12
  if (k === 'f12'){ e.preventDefault(); addViolation('f12') }
}

function onBeforeUnload(e){
  e.preventDefault()
  e.returnValue = ''
}

function parseRich(val){
  // Accept plain text or JSON string: { text: string, img: string }
  try {
    if (typeof val === 'string' && val.trim().startsWith('{')){
      const obj = JSON.parse(val)
      return { text: obj.text || '', img: obj.img || '' }
    }
  } catch {}
  return { text: val || '', img: '' }
}

function parseOption(q, opt){
  const raw = q[`option_${opt.toLowerCase()}`]
  return parseRich(raw)
}

function availableOptions(q){
  const opts = ['A','B','C','D','E']
  return opts.filter(letter => {
    const o = parseOption(q, letter)
    return (o.text && String(o.text).trim()) || (o.img && String(o.img).trim())
  })
}

function resolveImg(src){
  if (!src) return ''
  // If already absolute, return as is
  if (/^https?:\/\//i.test(src)) return src
  // If starts with /uploads/, prefix backend
  if (src.startsWith('/uploads/')) return `${window.location.origin.replace('5173', '8000')}${src}`
  return src
}

// Very small sanitizer for rendering rich HTML from our editor
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
  })(div)
  // After sanitizing, render math using KaTeX for $...$ and $$...$$ within text nodes
  return renderMathHTML(div.innerHTML)
}

function renderMathDOM(rootEl){
  try{
    const root = rootEl || document.getElementById(`qcard-${currentIndex.value}`) || document.querySelector('.left') || document.body
    renderMathInElement(root, {
      delimiters: [
        { left: '$$', right: '$$', display: true },
        { left: '$', right: '$', display: false },
      ],
      throwOnError: false,
      ignoredClasses: ['katex'],
      ignoredTags: ['script','style','textarea']
    })
  } catch (e){
    try { console.warn('katex auto-render error', e) } catch {}
  }
}

function openLightbox(url){ lightboxUrl.value = url }
function closeLightbox(){ lightboxUrl.value = '' }

function prev(){
  if (currentIndex.value > 0){
    currentIndex.value--
    ensureFullscreen()
    nextTick(() => requestAnimationFrame(() => renderMathDOM()))
  }
}
function next(){
  if (currentIndex.value < questions.value.length-1){
    currentIndex.value++
    ensureFullscreen()
    nextTick(() => requestAnimationFrame(() => renderMathDOM()))
  }
}
function go(i){
  currentIndex.value = i
  ensureFullscreen()
  nextTick(() => requestAnimationFrame(() => renderMathDOM()))
}
function toggleFlag(qid){
  flagged.value[qid] = !flagged.value[qid]
}
function isFlagged(qid){ return !!flagged.value[qid] }
function markAnswered(qid){ /* trigger UI update via answers binding */ }
function toggleMultiAnswer(qid, letter, ev){
  const cur = Array.isArray(answers.value[qid]) ? answers.value[qid].slice() : []
  if (ev.target.checked){
    if (!cur.includes(letter)) cur.push(letter)
  } else {
    const i = cur.indexOf(letter)
    if (i !== -1) cur.splice(i,1)
  }
  answers.value[qid] = cur
  markAnswered(qid)
}
function statusClass(qid){
  if (isFlagged(qid)) return 'flagged'
  const val = answers.value[qid]
  if (typeof val === 'string'){
    if (val && val.trim() !== '') return 'answered'
  } else if (val){
    return 'answered'
  }
  return 'pending'
}

function statusText(qid){
  if (isFlagged(qid)) return 'Ragu-ragu'
  if (answers.value[qid]) return 'Terjawab'
  return 'Belum Dijawab'
}

onMounted(async () => {
  try {
    // Start exam session (backend handles time limit; if setId provided, start by set)
    const payload = { category_id: categoryId }
    if (setId) payload.question_set_id = setId
    const { data: session } = await api.post('/exams/start', payload)
    examSessionId.value = session.id
    totalQuestions.value = session.total_questions

    // Fetch questions for the set (if provided) or the whole category
    const params = setId ? { question_set_id: setId } : { category_id: categoryId }
    const { data: qs } = await api.get('/questions/', { params })
    questions.value = qs
    // Fetch readings for any referenced reading_id
    const ids = Array.from(new Set((qs || []).map(q => q.reading_id).filter(Boolean)))
    if (ids.length){
      await Promise.all(ids.map(async (id) => {
        try { const { data } = await api.get(`/readings/${id}`); readingsMap.value[id] = data } catch {}
      }))
    }
    await nextTick()
    renderMathDOM()

    // if viewing by set, fetch set title
    if (setId){
      try {
        const { data: set } = await api.get(`/sets/${setId}`)
        setTitle.value = set.title
      } catch {}
    }

    // timer
    let timeLimit = session.time_limit_minutes || 60
    timeLimitInitial.value = timeLimit
    minutes.value = timeLimit
    seconds.value = 0
    timer = setInterval(() => {
      if (seconds.value === 0){
        if (minutes.value === 0){
          clearInterval(timer)
          submit()
        } else {
          minutes.value -= 1
          seconds.value = 59
        }
      } else {
        seconds.value -= 1
      }
    }, 1000)

    loaded.value = true
    // Activate focus guard after content is ready
    setupGuards()
  } catch (e) {
    const status = e?.response?.status
    if (status === 401 || status === 403) {
      // not logged in
      router.push({ name: 'login' })
      return
    }
    console.error('Failed to start exam:', e)
  }
})

function setupGuards(){
  // require fullscreen to start
  requestFullscreen()
  document.addEventListener('fullscreenchange', onFullscreenChange)
  document.addEventListener('visibilitychange', onVisibility)
  window.addEventListener('blur', onBlur)
  window.addEventListener('beforeunload', onBeforeUnload)
  document.addEventListener('contextmenu', blockContextMenu)
  document.addEventListener('copy', blockClipboard)
  document.addEventListener('cut', blockClipboard)
  document.addEventListener('paste', blockClipboard)
  document.addEventListener('keydown', onKeydown, { capture: true })
  unsubs = [
    () => document.removeEventListener('fullscreenchange', onFullscreenChange),
    () => document.removeEventListener('visibilitychange', onVisibility),
    () => window.removeEventListener('blur', onBlur),
    () => window.removeEventListener('beforeunload', onBeforeUnload),
    () => document.removeEventListener('contextmenu', blockContextMenu),
    () => document.removeEventListener('copy', blockClipboard),
    () => document.removeEventListener('cut', blockClipboard),
    () => document.removeEventListener('paste', blockClipboard),
    () => document.removeEventListener('keydown', onKeydown, { capture: true }),
  ]
  // Polling fallback: if fullscreen exits without firing change (or initial request blocked), record once
  wasFullscreen = !!document.fullscreenElement
  guardTick = setInterval(() => {
    if (endedByViolation.value) return
    const isFull = !!document.fullscreenElement
    if (wasFullscreen && !isFull) {
      maybeViolate('lost-fullscreen')
    }
    // also catch hidden state if event missed
    if (document.hidden){ maybeViolate('hidden-poll') }
    wasFullscreen = isFull
  }, 1000)
}
function removeGuards(){
  try { unsubs.forEach(fn => { try{ fn() }catch{} }) } catch {}
  unsubs = []
  try { if (guardTick) { clearInterval(guardTick); guardTick = null } } catch {}
}
function openConfirm(){ showConfirm.value = true }
function closeConfirm(){ showConfirm.value = false }
function confirmSubmit(){ showConfirm.value = false; submit() }
function closeAuthModal(){ showAuthModal.value = false }
function goLogin(){
  try {
    // Save pending submit payload for one-time retry after login
    if (pendingSubmitCache.value) {
      sessionStorage.setItem('pending_submit', JSON.stringify(pendingSubmitCache.value))
    }
  } catch {}
  const next = encodeURIComponent(window.location.pathname + window.location.search)
  router.push({ name: 'login', query: { next } })
}
async function submit(){
  if (isSubmitting.value) return
  isSubmitting.value = true
  if (timer) clearInterval(timer)
  // Compute elapsed time (initial - remaining)
  const remaining = minutes.value + (seconds.value / 60)
  let elapsed = (timeLimitInitial.value - remaining)
  if (elapsed < 0) elapsed = 0
  if (elapsed > timeLimitInitial.value) elapsed = timeLimitInitial.value
  const qTypeMap = Object.fromEntries(questions.value.map(q => [q.id, q.question_type || 'mcq']))
  const payload = {
    exam_session_id: examSessionId.value,
    answers: Object.keys(answers.value).map(qid => {
      const id = Number(qid)
      const t = qTypeMap[id] || 'mcq'
      const val = answers.value[qid]
      let selected
      if (t === 'multi'){
        selected = Array.isArray(val) ? val.map(x => String(x).toUpperCase()).sort().join(',') : ''
      } else if (typeof val === 'string'){
        selected = val
      } else {
        selected = ''
      }
      return { question_id: id, selected_answer: selected }
    }),
    time_taken_minutes: Number(elapsed.toFixed(2)),
  }
  try{
    // allow this call to handle auth errors itself
    const { data } = await api.post('/exams/submit', payload, { skipAuthRedirect: true })
    sessionStorage.removeItem('pending_submit')
    router.push({ name: 'result', params: { sessionId: data.exam_session_id } })
  } catch (e) {
    const status = e?.response?.status
    if (status === 401 || status === 403){
      // cache payload for retry after login
      pendingSubmitCache.value = payload
      try { sessionStorage.setItem('pending_submit', JSON.stringify(payload)) } catch {}
      showAuthModal.value = true
      return
    }
    console.error('Submit failed', e)
    submitError.value = e?.response?.data?.detail || e?.message || 'Submit failed. Please try again.'
  } finally {
    isSubmitting.value = false
  }
}

async function retrySubmitNow(){
  submitError.value = ''
  await submit()
}

// On return from login, if we have a cached submit and a valid token, retry once
onMounted(async () => {
  try {
    const cached = sessionStorage.getItem('pending_submit')
    if (cached && auth?.token){
      const parsed = JSON.parse(cached)
      // basic validation
      if (parsed && parsed.exam_session_id){
        try {
          const { data } = await api.post('/exams/submit', parsed, { skipAuthRedirect: true })
          sessionStorage.removeItem('pending_submit')
          router.push({ name: 'result', params: { sessionId: data.exam_session_id } })
          return
        } catch (e) {
          // if it still fails auth, show modal again
          const status = e?.response?.status
          if (status === 401 || status === 403){ showAuthModal.value = true }
        }
      }
    }
  } catch {}
})
</script>
<style scoped>
.exam-header{ display:flex; justify-content:space-between; align-items:center; }
.guard-bar{ margin:10px 0 6px; padding:8px 10px; border-radius:10px; background:#fff7ed; border:1px solid #fed7aa; color:#7c2d12; display:flex; align-items:center; gap:8px; font-size:14px; }
.guard-bar .dot{ width:8px; height:8px; border-radius:50%; display:inline-block; background:#f59e0b; }
.guard-bar .dot.ok{ background:#10b981; }
.guard-bar .dot.warn{ background:#f59e0b; }
.exam-body{ display:grid; grid-template-columns: 2fr 0.9fr; gap:16px; align-items:start; }
.left{ display:flex; flex-direction:column; gap:12px; }
.progress-wrap{ background:#f8fafc; border:1px solid #e2e8f0; border-radius:12px; padding:12px; }
.grid{ display:grid; gap:8px; }
.grid.compact{ grid-template-columns: repeat(5, 1fr); }
.cell{ padding:6px 0; border-radius:8px; border:1px solid #e2e8f0; background:#f1f5f9; cursor:pointer; font-weight:700; }
.cell.answered{ background:#dcfce7; border-color:#16a34a; color:#065f46; }
.cell.flagged{ background:#ffedd5; border-color:#f59e0b; color:#92400e; }
.cell.pending{ background:#f1f5f9; color:#475569; }
.cell.essay{ position:relative; }
.cell.essay::after{ content:'✎'; position:absolute; top:-6px; right:-6px; background:#fde68a; color:#92400e; border:1px solid #f59e0b; width:16px; height:16px; font-size:11px; line-height:14px; border-radius:50%; display:flex; align-items:center; justify-content:center; }
.cell.multi{ position:relative; }
.cell.multi::after{ content:'M'; position:absolute; top:-6px; right:-6px; background:#e0f2fe; color:#075985; border:1px solid #7dd3fc; width:16px; height:16px; font-size:11px; line-height:14px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:800; }
.question-card{ background:white; border:1px solid #e2e8f0; border-radius:14px; overflow:hidden; }
.reading-card{ margin:12px 12px 10px; background:#f8fafc; border:1px solid #e2e8f0; border-left:4px solid #6366f1; border-radius:12px; box-shadow: 0 6px 16px rgba(2,6,23,0.05); overflow:hidden; position: sticky; top: 0; z-index: 2; }
.reading-card.collapsed{ box-shadow:none; }
.reading-head{ display:flex; align-items:center; justify-content:space-between; gap:8px; padding:10px 12px; background:linear-gradient(90deg, rgba(99,102,241,0.12), rgba(99,102,241,0.06)); border-bottom:1px solid #e5e7eb; }
.reading-title{ font-weight:800; font-size:16px; color:#111827; }
.reading-body{ padding:12px 14px; color:#1f2937; line-height:1.9; letter-spacing:0.1px; background:white; }
.reading-body :deep(p){ margin: 0 0 10px; }
.reading-body :deep(h1),
.reading-body :deep(h2),
.reading-body :deep(h3){ margin: 8px 0 6px; line-height:1.3; }
.reading-body :deep(ul),
.reading-body :deep(ol){ padding-left: 22px; margin: 6px 0 10px; }
.reading-body :deep(img){ max-width: 100%; border-radius:8px; display:block; margin:8px auto; }
.reading-body :deep(blockquote){ border-left:3px solid #93c5fd; background:#f0f9ff; margin:8px 0; padding:8px 12px; border-radius:6px; color:#0c4a6e; }
.reading-body :deep(a){ color:#2563eb; text-decoration: underline; }
.reading-card .btn.tiny.secondary{ background:#ffffff; border:1px solid #c7d2fe; color:#3730a3; }
.reading-card .btn.tiny.secondary:hover{ background:#eef2ff; }
.reading-card + .q-top{ margin-top: 6px; }
.q-top{ display:flex; justify-content:space-between; align-items:center; padding:10px 12px; background: linear-gradient(90deg, #4f46e5, #6366f1); color:white; }
.q-top .pill.strong{ background:rgba(255,255,255,.2); color:#fff; border-radius:10px; padding:4px 10px; font-weight:800; }
.q-top .of{ margin-left:8px; opacity:.9; }
.q-top .status{ background:rgba(255,255,255,.2); color:#fff; border:1px solid rgba(255,255,255,.35); border-radius:999px; padding:4px 10px; font-weight:700; }
.q-top .status.answered{ background:#dcfce7; color:#065f46; border-color:#bbf7d0; }
.q-top .status.flagged{ background:#ffedd5; color:#92400e; border-color:#fed7aa; }
.q-top .type-pill{ background:#fde68a; color:#92400e; border:1px solid #f59e0b; border-radius:999px; padding:4px 10px; font-weight:800; margin-right:8px; }
.qtext{ padding:16px 16px 6px; font-weight:500; line-height:1.85; letter-spacing:0.1px; }
.q-divider{ height:1px; background:#e5e7eb; margin:8px 12px 6px; }
.answers-label{ padding:6px 16px 10px; font-weight:700; }
.qtext{ margin-top:8px; font-weight:400; line-height:1.85; letter-spacing:0.1px; }
.answers-label{ margin-top:16px; margin-bottom:10px; font-weight:700; }
.opt{ display:flex; gap:12px; align-items:flex-start; border:1px solid #e2e8f0; background:#fff; padding:14px 16px; border-radius:12px; transition: box-shadow .15s ease, border-color .15s ease, background .15s ease; }
.opt:hover{ box-shadow: 0 6px 18px rgba(2,6,23,0.06); border-color:#cbd5e1; }
.opt.selected{ border-color:#6366f1; background:#eef2ff; box-shadow: 0 8px 20px rgba(99,102,241,0.15); }
.radio{ margin:3px 2px 0 0; }
.letter{ display:inline-flex; width:28px; height:28px; border-radius:8px; background:#f1f5f9; align-items:center; justify-content:center; font-weight:800; color:#0f172a; flex: 0 0 28px; }
.opt-content{ display:flex; flex-direction:column; gap:12px; line-height:1.85; flex: 1; }
.opt-content > span:first-child{ display:block; white-space:normal; word-break:break-word; }
.options.grid-2{ display:grid; grid-template-columns: 1fr; row-gap:16px; }
.essay-input{ width:100%; min-height:140px; padding:12px 14px; border:1px solid #e2e8f0; border-radius:10px; font: inherit; line-height:1.7; }
.nav-row{ display:flex; justify-content:space-between; gap:8px; }
.btn.warn{ background:#f59e0b; color:white; border:none; }
.q-img { max-width: 100%; max-height: 240px; width: auto; height: auto; margin:10px auto 2px; display:block; border-radius:8px; cursor: zoom-in; object-fit: contain; }
.opt-img { max-width: 220px; max-height: 160px; width: auto; height: auto; border-radius:8px; cursor: zoom-in; object-fit: contain; }
.lightbox { position: fixed; inset: 0; background: rgba(0,0,0,0.75); display:flex; align-items:center; justify-content:center; z-index: 1000; }
.lightbox-img { max-width: 90vw; max-height: 90vh; border-radius: 10px; box-shadow: 0 8px 24px rgba(0,0,0,0.5); }
/* Center math formulas */
.qtext .katex-display,
.opt-content .katex-display{ margin-left:auto; margin-right:auto; text-align:center; }
.qtext .math-inline:only-child,
.opt-content .math-inline:only-child{ display:block; text-align:center; margin: 0 auto; }
.qtext .math-block,
.opt-content .math-block{ text-align:center; margin-left:auto; margin-right:auto; }
/* Confirm submit modal */
.modal-overlay{ position:fixed; inset:0; background: rgba(2,6,23,0.55); display:flex; align-items:center; justify-content:center; z-index: 1000; padding: 16px; }
.modal{ width:100%; max-width:480px; background:#fff; border:1px solid #e2e8f0; border-radius:14px; box-shadow: 0 20px 40px rgba(2,6,23,0.18); overflow:hidden; }
.modal-head{ font-weight:800; font-size:18px; padding:16px; border-bottom:1px solid #e2e8f0; color:#0f172a; }
.modal-body{ padding:16px; color:#334155; line-height:1.7; }
.modal-actions{ padding:12px 16px 16px; display:flex; gap:8px; justify-content:flex-end; }
@media (max-width: 900px){
  .exam-body{ grid-template-columns: 1fr; }
  .grid.compact{ grid-template-columns: repeat(5, 1fr); }
  .options.grid-2{ grid-template-columns: 1fr; }
}
</style>
