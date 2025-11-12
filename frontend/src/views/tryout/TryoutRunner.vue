<template>
  <div class="card" v-if="loaded">
    <div class="exam-header">
      <h2 v-if="phase==='running'">{{ setMeta?.title || 'Tryout' }}</h2>
      <h2 v-else>Next Set</h2>
      <div class="time" v-if="phase==='intermission'"><strong>Starts in:</strong> {{ interMin }}:{{ interSec }}</div>
      <div class="time" v-else-if="phase==='running'"><strong>Time Left:</strong> {{ runMin }}:{{ runSec }}</div>
    </div>
    <div v-if="phase==='running'" class="guard-bar">
      <span class="dot" :class="{ ok: !inViolation, warn: inViolation }"></span>
      Keep the exam in fullscreen and this tab active. Violations {{ violations }} / {{ VIOLATION_LIMIT }}.
    </div>

    <div v-if="phase==='intermission'" class="inter">
      <div class="ibox">
        <div class="ibody">
          <h2 class="set-title">{{ setMeta?.title || 'Next Set' }}</h2>
          <div v-if="setMeta?.intermission_text" class="desc" v-html="renderHTML(setMeta.intermission_text)"></div>
          <div v-else class="muted">Get ready. The next set will start automatically.</div>
        </div>
      </div>
    </div>

    <div v-else-if="phase==='running'" class="exam-body">
      <div class="left" v-if="questions.length">
        <div v-for="(q, i) in questions" :key="q.id">
          <div v-if="i === idx" class="question-card" :id="`qcard-${i}`">
            <div v-if="q.reading_id && readingById(q.reading_id)" class="reading-card" :class="{ collapsed: collapsedReading[q.reading_id] }">
              <div class="reading-head">
                <strong class="reading-title">{{ readingById(q.reading_id).title }}</strong>
                <button class="btn tiny secondary" @click="toggleReading(q.reading_id)">{{ collapsedReading[q.reading_id] ? 'Show' : 'Hide' }}</button>
              </div>
              <div class="reading-body" v-show="!collapsedReading[q.reading_id]" v-html="renderHTML(readingById(q.reading_id).content_html)"></div>
              <div class="q-divider" style="margin-top:8px;"></div>
            </div>
            <div class="q-top">
              <div class="q-top-left"><span class="pill strong">Soal {{ i+1 }}</span><span class="of">dari {{ questions.length }}</span></div>
              <div class="q-top-right">
                <span class="status" :class="statusClass(currentQuestionId)">{{ statusText(currentQuestionId) }}</span>
              </div>
            </div>
            <img v-if="stemImg(q)" :src="resolveImg(stemImg(q))" alt="question image" class="q-img" @click="openLightbox(resolveImg(stemImg(q)))" />
            <div class="qtext"><span v-html="renderHTML(stemText(q))"></span></div>
            <div class="q-divider"></div>
            <div class="answers-label">Jawaban</div>
            <template v-if="typeOf(q)==='essay'">
              <textarea class="essay-input" v-model="localAnswers[q.id]" @input="onEssayInput(q.id)" placeholder="Ketik jawaban Anda di sini..."></textarea>
            </template>
            <template v-else-if="typeOf(q)==='multi'">
              <div class="options grid-2">
                <label v-for="opt in optionLetters(q)" :key="opt" class="opt" :class="{ selected: (localAnswers[q.id]||[]).includes(opt) }">
                  <input class="radio" type="checkbox" :name="`q_${q.id}_${opt}`" :value="opt" :checked="(localAnswers[q.id]||[]).includes(opt)" @change="toggleMulti(q.id,opt,$event)" />
                  <span class="letter">{{ opt }}</span>
                  <span class="opt-content">
                    <span class="opt-text" v-if="optText(q,opt)" v-html="renderHTML(optText(q,opt))"></span>
                    <img v-if="optImg(q,opt)" :src="resolveImg(optImg(q,opt))" :alt="`option ${opt} image`" class="opt-img" @click="openLightbox(resolveImg(optImg(q,opt)))" />
                  </span>
                </label>
              </div>
            </template>
            <template v-else>
              <div class="options grid-2">
                <label v-for="opt in optionLetters(q)" :key="opt" class="opt" :class="{ selected: localAnswers[q.id]===opt }">
                  <input class="radio" type="radio" :name="`q_${q.id}`" :value="opt" :checked="localAnswers[q.id]===opt" @change="choose(q.id,opt)" />
                  <span class="letter">{{ opt }}</span>
                  <span class="opt-content">
                    <span class="opt-text" v-if="optText(q,opt)" v-html="renderHTML(optText(q,opt))"></span>
                    <img v-if="optImg(q,opt)" :src="resolveImg(optImg(q,opt))" :alt="`option ${opt} image`" class="opt-img" @click="openLightbox(resolveImg(optImg(q,opt)))" />
                  </span>
                </label>
              </div>
            </template>
          </div>
        </div>
        <div class="nav-row">
          <button class="btn secondary" :disabled="idx===0" @click="prev">‹ Sebelumnya</button>
          <button class="btn warn" @click="toggleFlag(currentQuestionId)">{{ isFlagged(currentQuestionId) ? 'Batalkan Ragu-ragu' : 'Ragu-ragu' }}</button>
          <button class="btn" :disabled="idx===questions.length-1" @click="next">Selanjutnya ›</button>
        </div>
        <button class="btn" style="margin-top:12px;" @click="openConfirm">Submit</button>
      </div>
      <div v-else>
        <div v-if="loadError" class="err">{{ loadError }}</div>
        <div v-else-if="questionsLoaded" class="muted">No questions in this set.</div>
        <div v-else class="muted">Loading questions…</div>
      </div>
      <div class="right" v-if="questions.length">
        <div class="progress-wrap">
          <div class="grid compact">
            <button
              v-for="(q, i) in questions"
              :key="q.id"
              class="cell"
              :class="[statusClass(q.id), (q.question_type||'mcq')]"
              @click="go(i)"
            >
              {{ i+1 }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="phase==='done'" class="muted">Tryout finished. Redirecting…</div>
    <!-- Device mismatch modal -->
    <div v-if="mismatch" class="modal-overlay">
      <div class="modal">
        <div class="modal-head">Session Locked to Another Device</div>
        <div class="modal-body">
          <p>{{ mismatchMsg || 'We detected this tryout is active on a different device. Please continue on the original device, or finish/close it there before resuming here.' }}</p>
        </div>
        <div class="modal-actions">
          <button class="btn secondary" @click="gotoHome">Back to Home</button>
          <button class="btn" @click="gotoLobby">Go to Lobby</button>
        </div>
      </div>
    </div>
    <!-- Submit confirmation modal (moved to top-level) -->
    <div v-if="showConfirm" class="modal-overlay" @click.self="closeConfirm">
      <div class="modal">
        <div class="modal-head">Finish this set?</div>
        <div class="modal-body">
          <p>Are you sure you want to submit answers for this set?</p>
          <p><strong>Progress:</strong> {{ answeredCount }} / {{ totalCount }} answered</p>
        </div>
        <div class="modal-actions">
          <button class="btn secondary" @click="closeConfirm">Cancel</button>
          <button class="btn" @click="confirmSubmit">Yes, Submit</button>
        </div>
      </div>
    </div>
    <div v-if="lightboxUrl" class="lightbox" @click="closeLightbox">
      <img :src="lightboxUrl" alt="preview" class="lightbox-img" />
    </div>
  </div>
</template>
<script setup>
import { onMounted, onUnmounted, ref, computed, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../../api/client'
import { renderMathHTML } from '../../utils/math'
import renderMathInElement from 'katex/contrib/auto-render/auto-render'

const route = useRoute()
const router = useRouter()
const sessionId = Number(route.params.sessionId)

const loaded = ref(false)
const phase = ref('intermission')
const tssId = ref(0)
const setMeta = ref(null)
const runEndAt = ref(null)
const interEndAt = ref(null)
const nowDrift = ref(0) // client-server drift in ms if needed later

// timers
let tInter = null
let tRun = null
const interMin = computed(()=> formatMM(interRemain.value).mm)
const interSec = computed(()=> formatMM(interRemain.value).ss)
const runMin = computed(()=> formatMM(runRemain.value).mm)
const runSec = computed(()=> formatMM(runRemain.value).ss)
const interRemain = ref(0)
const runRemain = ref(0)
const mismatch = ref(false)
const mismatchMsg = ref('')
const prefilledForTss = ref(0)

function parseISO(s){ return s ? new Date(s) : null }
function formatMM(totalSec){ const n=Math.max(0,Math.floor(totalSec)); const mm=String(Math.floor(n/60)).padStart(2,'0'); const ss=String(n%60).padStart(2,'0'); return {mm, ss} }

async function poll(){
  let data
  try{
    const res = await api.get(`/tryouts/sessions/${sessionId}/current`)
    data = res.data
  } catch (e) {
    const status = e?.response?.status
    if (status === 409){ handleDeviceMismatch(e); return }
    throw e
  }
  if (data.phase === 'done' || data.phase === 'finished'){
    router.push(`/tryout/result/${sessionId}`)
    return
  }
  phase.value = data.phase
  tssId.value = data.tss_id
  setMeta.value = data.set
  interEndAt.value = data.intermission_end_at
  runEndAt.value = data.run_end_at
  if (phase.value === 'intermission') startInterTimer()
  if (phase.value === 'running'){
    // Load questions only on first time or when set changed
    const curSetId = data.set?.question_set_id || null
    if (!questionsLoaded.value || loadedSetId.value !== curSetId){
      await ensureQuestions()
    }
    // Prefill answers once per active tss
    if (prefilledForTss.value !== data.tss_id){
      await prefillAnswers(data.tss_id)
      prefilledForTss.value = data.tss_id
    }
    startRunTimer()
  }
  loaded.value = true
}

function startInterTimer(){
  stopTimers()
  tInter = setInterval(async ()=>{
    const end = parseISO(interEndAt.value)
    const sec = Math.max(0, Math.ceil((end - Date.now())/1000))
    interRemain.value = sec
    if (sec <= 0){
      try{ await api.post(`/tryouts/set-sessions/${tssId.value}/begin-run`) }catch(e){ if(e?.response?.status===409){ handleDeviceMismatch(e); return } }
      await poll()
    }
  }, 1000)
}
function startRunTimer(){
  stopTimers()
  tRun = setInterval(async ()=>{
    const end = parseISO(runEndAt.value)
    let sec = 0
    if (end) {
      sec = Math.max(0, Math.ceil((end - Date.now())/1000))
    }
    runRemain.value = sec
    if (sec <= 0){ await finishNow() }
  }, 1000)
}
function stopTimers(){ try{ if (tInter) clearInterval(tInter) }catch{} tInter=null; try{ if (tRun) clearInterval(tRun) }catch{} tRun=null }

// questions
const questions = ref([])
const idx = ref(0)
const localAnswers = ref({})
const letters = ['A','B','C','D','E']
const loadError = ref('')
const questionsLoaded = ref(false)
const loadedSetId = ref(null)
const flagged = ref({})
const currentQuestionId = computed(() => questions.value[idx.value]?.id)
const answeredCount = computed(() => {
  const list = questions.value || []
  let n = 0
  for (const q of list){
    const v = localAnswers.value[q.id]
    if (Array.isArray(v)) { if (v.length) n++ }
    else if (typeof v === 'string') { if (v.trim()) n++ }
  }
  return n
})
const totalCount = computed(() => questions.value.length)
const showConfirm = ref(false)
const lightboxUrl = ref('')
const collapsedReading = ref({})
const readingsMap = ref({})

async function ensureQuestions(){
  if (!setMeta.value) return
  try{
    loadError.value = ''
    const { data: qs } = await api.get('/questions/', { params: { question_set_id: setMeta.value.question_set_id } })
    const setId = setMeta.value?.question_set_id || null
    const firstLoadForThisSet = loadedSetId.value !== setId
    // Only update the array if the IDs changed, to prevent VDOM rekey/patch churn
    const oldIds = (questions.value||[]).map(q=>q.id).join(',')
    const newIds = (qs||[]).map(q=>q.id).join(',')
    if (oldIds !== newIds){
      questions.value = qs
      if (firstLoadForThisSet){ idx.value = 0 }
    }
    questionsLoaded.value = true
    loadedSetId.value = setId
    // fetch reading passages for referenced questions
    const ids = Array.from(new Set((qs || []).map(q => q.reading_id).filter(Boolean)))
    if (ids.length){
      const map = {}
      await Promise.all(ids.map(async (id) => {
        try { const { data } = await api.get(`/readings/${id}`); map[id] = data } catch {}
      }))
      readingsMap.value = map
    } else {
      readingsMap.value = {}
    }
    await nextTick(); renderMathDOM()
  } catch (e) {
    const status = e?.response?.status
    const msg = e?.response?.data?.detail || e?.message || 'Failed to load questions'
    loadError.value = `Error ${status || ''} ${msg}`.trim()
    questionsLoaded.value = true
  }
}

async function prefillAnswers(activeTssId){
  if (!activeTssId) return
  try{
    const { data } = await api.get(`/tryouts/set-sessions/${activeTssId}/answers`)
    const map = {}
    const arr = Array.isArray(data?.answers) ? data.answers : []
    for (const row of arr){
      const qid = row?.question_id
      const sel = String(row?.selected_answer || '').trim()
      if (!qid) continue
      if (sel.includes(',')){
        // multi-answer stored as comma-separated
        map[qid] = sel.split(',').map(s=>s.trim()).filter(Boolean)
      } else {
        map[qid] = sel
      }
    }
    // merge without wiping current in-memory edits
    localAnswers.value = { ...map, ...localAnswers.value }
  }catch(e){
    const status = e?.response?.status
    if (status === 409){ handleDeviceMismatch(e); return }
  }
}

const currentQ = computed(()=> questions.value[idx.value] || {})
function typeOf(q){ return (q?.question_type)||'mcq' }
function safeParseJSON(maybeJson){
  try{
    if (typeof maybeJson === 'string' && maybeJson.trim().startsWith('{')){
      return JSON.parse(maybeJson)
    }
  }catch{}
  return null
}
function stemText(q){ const obj = safeParseJSON(q?.question_text); return (obj && obj.text) ? obj.text : (q?.question_text||'') }
function stemImg(q){ const obj = safeParseJSON(q?.question_text); return (obj && obj.img) ? obj.img : '' }
function optRaw(q, opt){ if (!opt || !q) return '';
  const key = `option_${String(opt).toLowerCase()}`
  return q[key]
}
function optText(q,opt){ const raw = optRaw(q,opt); const obj = safeParseJSON(raw); return (obj && obj.text) ? obj.text : (raw||'') }
function optImg(q,opt){ const raw = optRaw(q,opt); const obj = safeParseJSON(raw); return (obj && obj.img) ? obj.img : '' }
function hasOpt(q,opt){ if (!opt) return false; const t=optText(q,opt); const i=optImg(q,opt); return (t&&String(t).trim()) || (i&&String(i).trim()) }
function optionLetters(q){ return letters.filter(letter => hasOpt(q, letter)) }

function readingById(id){ if (!id) return null; return readingsMap.value[id] || null }
function toggleReading(id){ if (!id) return; collapsedReading.value[id] = !collapsedReading.value[id] }
function renderHTML(html){ return renderMathHTML(String(html||'')) }
function resolveImg(src){ if(!src) return ''; if(/^https?:\/\//i.test(src)||src.startsWith('data:image')) return src; const p = src.startsWith('/')?src:`/${src}`; return p.startsWith('/uploads/')? `${window.location.origin.replace('5173','8000')}${p}`: p }
function openLightbox(url){ lightboxUrl.value = url }
function closeLightbox(){ lightboxUrl.value = '' }
function renderMathDOM(){
  try{
    const root = document.getElementById(`qcard-${idx.value}`) || document.querySelector('.left') || document.body
    renderMathInElement(root, {
      delimiters: [
        { left: '$$', right: '$$', display: true },
        { left: '$', right: '$', display: false },
      ],
      throwOnError: false,
      ignoredClasses: ['katex'],
      ignoredTags: ['script','style','textarea']
    })
  } catch {}
}

async function choose(qid, L){
  localAnswers.value[qid] = L
  try { await api.post(`/tryouts/set-sessions/${tssId.value}/answer`, null, { params: { question_id: qid, selected_answer: L } }) } catch(e){ if(e?.response?.status===409){ handleDeviceMismatch(e); return } throw e }
}
async function toggleMulti(qid, L, ev){
  const cur = Array.isArray(localAnswers.value[qid]) ? localAnswers.value[qid].slice() : []
  if (ev.target.checked){ if(!cur.includes(L)) cur.push(L) } else { const i=cur.indexOf(L); if(i!==-1) cur.splice(i,1) }
  localAnswers.value[qid] = cur
  const payload = cur.slice().sort().join(',')
  try { await api.post(`/tryouts/set-sessions/${tssId.value}/answer`, null, { params: { question_id: qid, selected_answer: payload } }) } catch(e){ if(e?.response?.status===409){ handleDeviceMismatch(e); return } throw e }
}
async function onEssayInput(qid){
  const val = String(localAnswers.value[qid] || '')
  try { await api.post(`/tryouts/set-sessions/${tssId.value}/answer`, null, { params: { question_id: qid, essay_answer: val } }) } catch(e){ if(e?.response?.status===409){ handleDeviceMismatch(e); return } throw e }
}

async function finishNow(){
  try{
    await api.post(`/tryouts/set-sessions/${tssId.value}/finish`)
  }catch(e){ if(e?.response?.status===409){ handleDeviceMismatch(e); return } }
  // Do NOT navigate here. Let poll() decide: it will push to result only when phase === 'done'.
  await poll()
}

// UI helpers like Exam.vue
function ensureFullscreenOnAction(){
  // Try requesting fullscreen in direct reaction to a user gesture
  requestFullscreen()
}
function prev(){
  ensureFullscreenOnAction()
  if (idx.value>0){
    idx.value--
    nextTick(()=> requestAnimationFrame(()=> renderMathDOM()))
  }
}
function next(){
  ensureFullscreenOnAction()
  if (idx.value<questions.value.length-1){
    idx.value++
    nextTick(()=> requestAnimationFrame(()=> renderMathDOM()))
  }
}
function go(i){
  ensureFullscreenOnAction()
  idx.value = i
  nextTick(()=> requestAnimationFrame(()=> renderMathDOM()))
}
function toggleFlag(qid){ if (!qid) return; flagged.value[qid] = !flagged.value[qid] }
function isFlagged(qid){ return !!flagged.value[qid] }
function statusClass(qid){ if (isFlagged(qid)) return 'flagged'; const v = localAnswers.value[qid]; if (Array.isArray(v)) return v.length?'answered':'pending'; if (typeof v==='string') return v.trim()? 'answered':'pending'; return 'pending' }
function statusText(qid){ if (isFlagged(qid)) return 'Ragu-ragu'; return localAnswers.value[qid] ? 'Terjawab' : 'Belum Dijawab' }

function openConfirm(){ ensureFullscreenOnAction(); showConfirm.value = true }
function closeConfirm(){ showConfirm.value = false }
async function confirmSubmit(){ showConfirm.value = false; await finishNow() }

let poller = null
onMounted(async ()=>{
  await poll()
  poller = setInterval(poll, 2000)
})
onUnmounted(()=>{ if (poller) clearInterval(poller); stopTimers(); removeGuards() })

// -------- Security / Anti-cheat (ported from Exam.vue) --------
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
  if (now - lastViolationTs > 1200){
    addViolation(reason)
    lastViolationTs = now
  }
}
function addViolation(reason){
  if (endedByViolation.value || phase.value !== 'running') return
  violations.value = Math.min(VIOLATION_LIMIT, violations.value + 1)
  try { console.warn('Tryout violation:', reason, violations.value, '/', VIOLATION_LIMIT) } catch {}
  if (violations.value >= VIOLATION_LIMIT){
    endForViolation()
  }
}
async function endForViolation(){
  if (endedByViolation.value) return
  endedByViolation.value = true
  removeGuards()
  try { if (document.fullscreenElement) await document.exitFullscreen() } catch {}
  // Auto-finish the current set immediately
  await finishNow()
}

async function requestFullscreen(){
  const el = document.documentElement
  if (!document.fullscreenElement && el?.requestFullscreen){
    fullscreenRequested = true
    try { await el.requestFullscreen() } catch {}
  }
}
function ensureFullscreen(){ if (!document.fullscreenElement) requestFullscreen() }
function onFullscreenChange(){ if (!document.fullscreenElement && fullscreenRequested){ maybeViolate('exit-fullscreen'); requestFullscreen() } }
function onVisibility(){ if (document.hidden){ maybeViolate('tab-hidden') } }
function onBlur(){ maybeViolate('window-blur') }
function blockContextMenu(e){ e.preventDefault() }
function blockClipboard(e){ e.preventDefault() }
function onKeydown(e){
  const k = e.key.toLowerCase()
  const meta = e.ctrlKey || e.metaKey
  if (meta && ['c','p','s','f'].includes(k)) { e.preventDefault(); addViolation('shortcut-'+k) }
  if (k === 'f12'){ e.preventDefault(); addViolation('f12') }
}
function onBeforeUnload(e){ e.preventDefault(); e.returnValue = '' }

function setupGuards(){
  // Immediately request fullscreen when entering running phase
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
  wasFullscreen = !!document.fullscreenElement
  guardTick = setInterval(() => {
    if (endedByViolation.value || phase.value !== 'running') return
    const isFull = !!document.fullscreenElement
    if (wasFullscreen && !isFull) { maybeViolate('lost-fullscreen') }
    if (document.hidden){ maybeViolate('hidden-poll') }
    wasFullscreen = isFull
  }, 1000)
}
function removeGuards(){
  try { unsubs.forEach(fn => { try{ fn() }catch{} }) } catch {}
  unsubs = []
  try { if (guardTick) { clearInterval(guardTick); guardTick = null } } catch {}
}

// Whenever phase changes, attach/detach guards for running phase
watch(phase, (p, prev) => {
  if (p === 'running') setupGuards(); else removeGuards()
})

// Reload only when the set changes while running
watch(() => setMeta.value?.question_set_id, async (newId, oldId) => {
  if (phase.value === 'running' && newId && newId !== oldId){
    loadedSetId.value = null
    await ensureQuestions()
  }
})

function handleDeviceMismatch(e){
  mismatch.value = true
  mismatchMsg.value = (e?.response?.data?.detail) || 'This session is locked to another device.'
  stopTimers(); removeGuards()
}
function gotoHome(){ router.push('/') }
function gotoLobby(){ router.push(`/tryout/${setMeta.value?.tryout_id || ''}`) }
</script>
<style scoped>
.exam-header{ display:flex; justify-content:space-between; align-items:center; }
.guard-bar{ margin:10px 0 6px; padding:8px 10px; border-radius:10px; background:#fff7ed; border:1px solid #fed7aa; color:#7c2d12; display:flex; align-items:center; gap:8px; font-size:14px; }
.guard-bar .dot{ width:8px; height:8px; border-radius:50%; display:inline-block; background:#f59e0b; }
.guard-bar .dot.ok{ background:#10b981; }
.guard-bar .dot.warn{ background:#f59e0b; }
.inter{ display:flex; justify-content:center; }
.ibox{ width:100%; max-width:none; border:1px solid #e2e8f0; border-radius:12px; overflow:hidden; background:#fff; }
.ihead{ padding:10px 12px; font-weight:800; background:#f1f5f9; border-bottom:1px solid #e2e8f0; }
.ibody{ padding:12px; display:flex; flex-direction:column; gap:10px; }
.intertext{ background:#eef2ff; border:1px solid #e5e7eb; border-left:4px solid #6366f1; border-radius:10px; padding:10px 12px; color:#1f2937; line-height:1.85; }
.desc{ background:#f8fafc; border:1px solid #e5e7eb; border-radius:10px; padding:10px 12px; color:#1f2937; line-height:1.85; }
.intertext :deep(h1), .desc :deep(h1),
.intertext :deep(h2), .desc :deep(h2),
.intertext :deep(h3), .desc :deep(h3){ margin:6px 0 4px; line-height:1.3; }
.intertext :deep(p), .desc :deep(p){ margin:0 0 8px; }
.intertext :deep(ul), .desc :deep(ul),
.intertext :deep(ol), .desc :deep(ol){ margin:6px 0 8px; padding-left:20px; }
.intertext :deep(img), .desc :deep(img){ max-width:100%; border-radius:8px; display:block; margin:8px auto; }
.count{ font-size:28px; font-weight:900; margin-top:8px; }
.exam-body{ display:grid; grid-template-columns: 2fr 0.9fr; gap:16px; align-items:start; }
.left{ display:flex; flex-direction:column; gap:12px; }
.question-card{ background:#fff; border:1px solid #e2e8f0; border-radius:14px; overflow:hidden; }
.q-top{ display:flex; align-items:center; justify-content:space-between; padding:10px 12px; background: linear-gradient(90deg, #4f46e5, #6366f1); color:white; }
.q-top-left .pill.strong{ background:rgba(255,255,255,.2); color:#fff; border-radius:10px; padding:4px 10px; font-weight:800; }
.q-top-left .of{ margin-left:8px; opacity:.9; }
.q-top-right .status{ background:rgba(255,255,255,.2); color:#fff; border:1px solid rgba(255,255,255,.35); border-radius:999px; padding:4px 10px; font-weight:700; }
.q-top-right .status.answered{ background:#dcfce7; color:#065f46; border-color:#bbf7d0; }
.q-top-right .status.flagged{ background:#ffedd5; color:#92400e; border-color:#fed7aa; }
.qtext{ padding:16px 16px 6px; font-weight:500; line-height:1.85; letter-spacing:0.1px; }
.answers-label{ padding:6px 16px 10px; font-weight:700; }
.options.grid-2{ display:grid; grid-template-columns: 1fr; row-gap:16px; }
.opt{ display:flex; gap:12px; align-items:flex-start; border:1px solid #e2e8f0; background:#fff; padding:14px 16px; border-radius:12px; }
.opt.selected{ background:#eef2ff; border-color:#6366f1; box-shadow:0 0 0 3px rgba(99,102,241,0.18) inset; }
.radio{ margin:3px 2px 0 0; }
.letter{ display:inline-flex; width:28px; height:28px; border-radius:8px; background:#f1f5f9; align-items:center; justify-content:center; font-weight:800; color:#0f172a; flex: 0 0 28px; }
.opt-content{ display:flex; flex-direction:column; gap:12px; line-height:1.85; flex: 1; }
.q-img{ max-width:100%; max-height:240px; border-radius:8px; display:block; margin:6px auto; cursor: zoom-in; }
.opt-img{ max-width:220px; max-height:160px; border-radius:8px; cursor: zoom-in; }
.essay-input{ width:100%; min-height:140px; padding:12px 14px; border:1px solid #e2e8f0; border-radius:10px; font: inherit; line-height:1.7; }
.nav-row{ display:flex; gap:8px; justify-content:space-between; }
.btn.warn{ background:#f59e0b; color:#fff; }
.muted{ color:#64748b }
.reading-card{ margin:12px 12px 10px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:12px; box-shadow: 0 6px 16px rgba(2,6,23,0.05); overflow:hidden; position: sticky; top: 0; z-index: 2; }
.reading-card.collapsed{ box-shadow:none; }
.reading-head{ display:flex; align-items:center; justify-content:space-between; gap:8px; padding:10px 12px; background:linear-gradient(90deg, rgba(99,102,241,0.12), rgba(99,102,241,0.06)); border-bottom:1px solid #e5e7eb; }
.reading-title{ font-weight:800; font-size:16px; color:#111827; }
.reading-body{ padding:12px 14px; color:#1f2937; line-height:1.9; letter-spacing:0.1px; background:white; }
.q-divider{ height:1px; background:#e5e7eb; margin:8px 12px 6px; }
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

/* Modal */
.modal-overlay{ position:fixed; inset:0; background: rgba(2,6,23,0.55); display:flex; align-items:center; justify-content:center; z-index: 1000; padding: 16px; }
.modal{ width:100%; max-width:480px; background:#fff; border:1px solid #e2e8f0; border-radius:14px; box-shadow: 0 20px 40px rgba(2,6,23,0.18); overflow:hidden; }
.modal-head{ font-weight:800; font-size:18px; padding:16px; border-bottom:1px solid #e2e8f0; color:#0f172a; }
.modal-body{ padding:16px; color:#334155; line-height:1.7; }
.modal-actions{ padding:12px 16px 16px; display:flex; gap:8px; justify-content:flex-end; }

/* Lightbox */
.lightbox{ position:fixed; inset:0; background: rgba(2,6,23,0.8); display:flex; align-items:center; justify-content:center; z-index: 1200; }
.lightbox-img{ max-width:92vw; max-height:92vh; object-fit:contain; border-radius:10px; box-shadow: 0 10px 30px rgba(0,0,0,.4); }
</style>
