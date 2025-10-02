<template>
  <div class="card" v-if="loaded">
    <div class="exam-header">
      <h2>{{ setTitle || 'Exam' }}</h2>
      <div class="time"><strong>Time Left:</strong> {{ minutes }}:{{ seconds.toString().padStart(2,'0') }}</div>
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
          <div class="qtext">Q{{ idx+1 }}. {{ parseRich(q.question_text).text }}</div>
          <div class="answers-label">Jawaban</div>
          <div class="options grid-2">
            <label v-for="opt in ['A','B','C','D','E']" :key="opt" class="opt">
              <input type="radio" :name="`q_${q.id}`" :value="opt" v-model="answers[q.id]" @change="markAnswered(q.id)" />
              <span class="opt-content">
                <span>{{ parseOption(q, opt).text }}</span>
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
  </div>
</template>
<script setup>
import { onMounted, ref, computed } from 'vue'
import api from '../api/client'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
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

function openLightbox(url){ lightboxUrl.value = url }
function closeLightbox(){ lightboxUrl.value = '' }

function prev(){ if (currentIndex.value > 0) currentIndex.value-- }
function next(){ if (currentIndex.value < questions.value.length-1) currentIndex.value++ }
function go(i){ currentIndex.value = i }
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

const isSubmitting = ref(false)
const showConfirm = ref(false)
function openConfirm(){ showConfirm.value = true }
function closeConfirm(){ showConfirm.value = false }
function confirmSubmit(){ showConfirm.value = false; submit() }
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
    const { data } = await api.post('/exams/submit', payload)
    router.push({ name: 'result', params: { sessionId: data.exam_session_id } })
  } finally {
    isSubmitting.value = false
  }
}
</script>
<style scoped>
.exam-header{ display:flex; justify-content:space-between; align-items:center; }
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
