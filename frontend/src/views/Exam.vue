<template>
  <div class="card" v-if="loaded">
    <div class="exam-header">
      <h2>{{ setTitle || 'Exam' }}</h2>
      <div class="time"><strong>Time Left:</strong> {{ minutes }}:{{ seconds.toString().padStart(2,'0') }}</div>
    </div>
    <div class="guard-bar">
      <span class="dot" :class="{ ok: !inViolation, warn: inViolation }"></span>
      <strong>Focus mode:</strong>
      Keep the exam in fullscreen and this tab active. Violations {{ violations }} / {{ VIOLATION_LIMIT }}.
    </div>
    <div class="exam-body">
      <div class="left">
        <div v-for="(q, idx) in questions" :key="q.id" v-show="idx === currentIndex" class="question-card">
          <img
            v-if="parseRich(q.question_text).img"
            :src="resolveImg(parseRich(q.question_text).img)"
            alt="question image"
            class="q-img"
            @click="openLightbox(resolveImg(parseRich(q.question_text).img))"
          />
          <div class="qtext">
            <span class="qnum">Q{{ idx+1 }}.</span>
            <span v-if="parseRich(q.question_text).text" v-html="renderHTML(parseRich(q.question_text).text)"></span>
          </div>
          <div class="answers-label">Jawaban</div>
          <div class="options grid-2">
            <label v-for="opt in ['A','B','C','D','E']" :key="opt" class="opt">
              <input type="radio" :name="`q_${q.id}`" :value="opt" v-model="answers[q.id]" @change="markAnswered(q.id)" />
              <span class="opt-content">
                <span v-if="parseOption(q, opt).text" v-html="renderHTML(parseOption(q, opt).text)"></span>
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
              :class="statusClass(q.id)"
              @click="go(idx)"
            >{{ idx+1 }}</button>
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
import { onMounted, onUnmounted, ref, computed, watch } from 'vue'
import api from '../api/client'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const categoryId = Number(route.params.categoryId)
const setId = route.query.setId ? Number(route.query.setId) : null

const loaded = ref(false)
const examSessionId = ref(null)
const totalQuestions = ref(0)
const questions = ref([])
const answers = ref({})
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
  return div.innerHTML
}

function openLightbox(url){ lightboxUrl.value = url }
function closeLightbox(){ lightboxUrl.value = '' }

function prev(){ if (currentIndex.value > 0){ currentIndex.value--; ensureFullscreen() } }
function next(){ if (currentIndex.value < questions.value.length-1){ currentIndex.value++; ensureFullscreen() } }
function go(i){ currentIndex.value = i; ensureFullscreen() }
function toggleFlag(qid){
  flagged.value[qid] = !flagged.value[qid]
}
function isFlagged(qid){ return !!flagged.value[qid] }
function markAnswered(qid){ /* trigger UI update via answers binding */ }
function statusClass(qid){
  if (isFlagged(qid)) return 'flagged'
  if (answers.value[qid]) return 'answered'
  return 'pending'
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
  const payload = {
    exam_session_id: examSessionId.value,
    answers: Object.keys(answers.value).map(qid => ({ question_id: Number(qid), selected_answer: answers.value[qid] })),
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
.question-card{ background:white; border:1px solid #e2e8f0; border-radius:12px; padding:12px; }
.qtext{ margin-top:8px; font-weight:400; line-height:1.85; letter-spacing:0.1px; }
.answers-label{ margin-top:16px; margin-bottom:10px; font-weight:700; }
.opt{ display:flex; gap:8px; align-items:flex-start; }
.opt{ padding:8px 10px; border-radius:10px; }
.opt-content{ display:flex; flex-direction:column; gap:10px; line-height:1.75; }
.opt-content > span:first-child{ display:block; }
.options.grid-2{ display:grid; grid-template-columns: 1fr 1fr; column-gap:24px; row-gap:16px; }
.nav-row{ display:flex; justify-content:space-between; gap:8px; }
.btn.warn{ background:#f59e0b; color:white; border:none; }
.q-img { max-width: 100%; max-height: 240px; width: auto; height: auto; margin:10px auto 2px; display:block; border-radius:8px; cursor: zoom-in; object-fit: contain; }
.opt-img { max-width: 220px; max-height: 160px; width: auto; height: auto; border-radius:8px; cursor: zoom-in; object-fit: contain; }
.lightbox { position: fixed; inset: 0; background: rgba(0,0,0,0.75); display:flex; align-items:center; justify-content:center; z-index: 1000; }
.lightbox-img { max-width: 90vw; max-height: 90vh; border-radius: 10px; box-shadow: 0 8px 24px rgba(0,0,0,0.5); }
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
