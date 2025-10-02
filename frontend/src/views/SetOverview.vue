<template>
  <div class="card" v-if="set" style="position:relative;">
    <div class="status-badge" :class="{ taken: lastMeta?.taken }">
      <span class="dot"></span>
      <div class="lines">
        <div class="state">{{ lastMeta?.taken ? 'Taken' : 'Not taken' }}</div>
        <div v-if="lastMeta?.taken" class="meta">Last score: {{ Math.round(lastMeta.score) }}% · {{ formatDate(lastMeta.time) }}</div>
      </div>
    </div>
    <h2>{{ set.title }}</h2>
    <p class="desc">{{ set.description }}</p>
    <div class="meta">
      <div><strong>Kategori:</strong> {{ category?.name }}</div>
      <div><strong>Pertanyaan:</strong> {{ questionCount }} item</div>
      <div><strong>Durasi:</strong> {{ set.time_limit_minutes }} menit</div>
    </div>
    <button class="btn" style="margin-top:16px;" @click="start">Mulai Simulasi</button>
  </div>
</template>
<script setup>
import { onMounted, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api/client'

const route = useRoute()
const router = useRouter()
const setId = Number(route.params.setId)

const set = ref(null)
const category = ref(null)
const history = ref([])
const questionCount = ref(0)

onMounted(async () => {
  const { data: s } = await api.get(`/sets/${setId}`)
  set.value = s
  const { data: cats } = await api.get('/categories/')
  category.value = cats.find(c => c.id === s.category_id)
  const { data: qs } = await api.get('/questions/', { params: { question_set_id: setId } })
  questionCount.value = qs.length

  // fetch exam history for this set
  try{
    const { data: hist } = await api.get('/exams/history')
    history.value = Array.isArray(hist) ? hist : []
  } catch {}
})

function start(){
  router.push({ name: 'exam', params: { categoryId: set.value.category_id }, query: { setId } })
}

// compute last attempt meta (taken flag, score, time)
const pickFirst = (obj, keys) => {
  for (const k of keys){
    const v = obj?.[k]
    if (v !== undefined && v !== null && String(v).trim?.() !== '') return v
  }
  return null
}
const lastMeta = computed(() => {
  const sid = setId
  const items = (history.value || []).filter(h => Number(pickFirst(h, ['question_set_id','set_id','questionSetId','setId'])) === sid)

  if (items.length === 0) return { taken: false }

  // Latest completed attempt (by completed_at)
  const completed = items
    .filter(h => !!pickFirst(h, ['is_completed','isCompleted']))
    .map(h => ({
      src: h,
      t: Date.parse(pickFirst(h, ['completed_at','updated_at'])) || 0,
    }))
    .sort((a,b) => b.t - a.t)

  const latestCompleted = completed[0]?.src

  // Latest attempt time for display if needed
  const latestAny = items
    .map(h => ({ src: h, t: Date.parse(pickFirst(h, ['completed_at','started_at','updated_at','created_at','createdAt'])) || 0 }))
    .sort((a,b) => b.t - a.t)[0]?.src

  if (latestCompleted){
    // Prefer percentage; else compute from correct/total
    const perc = Number(pickFirst(latestCompleted, ['score_percentage','score','scorePercentage']))
    let score = Number.isFinite(perc) ? perc : null
    if (score === null){
      const correct = Number(pickFirst(latestCompleted, ['correct_answers','correctAnswers']))
      const total = Number(pickFirst(latestCompleted, ['total_questions','totalQuestions']))
      if (Number.isFinite(correct) && Number.isFinite(total) && total > 0){
        score = (correct / total) * 100
      }
    }
    const timeRaw = pickFirst(latestCompleted, ['completed_at','updated_at'])
    return { taken: true, score: score !== null ? score : 0, time: timeRaw }
  }

  // No completed attempt yet
  return { taken: false, time: pickFirst(latestAny, ['started_at','created_at','createdAt']) }
})

function formatDate(val){
  if (!val) return ''
  const d = new Date(val)
  if (isNaN(d.getTime())) return String(val)
  return d.toLocaleDateString(undefined, { year:'numeric', month:'short', day:'2-digit' })
}
</script>

<style scoped>
.desc{ color:#64748b; line-height:1.85; letter-spacing:0.1px; white-space: pre-line; margin-top:6px; }
.meta{ margin-top:12px; display:flex; flex-direction:column; gap:6px; line-height:1.7; }
/* top-right status badge */
.status-badge{ position:absolute; top:12px; right:12px; display:flex; align-items:center; gap:8px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:999px; padding:6px 10px; color:#64748b; }
.status-badge .dot{ width:10px; height:10px; border-radius:999px; background:#cbd5e1; display:inline-block; }
.status-badge.taken{ color:#065f46; background:#ecfdf5; border-color:#a7f3d0; }
.status-badge.taken .dot{ background:#16a34a; }
.status-badge .lines{ display:flex; flex-direction:column; line-height:1.1; }
.status-badge .state{ font-weight:700; }
.status-badge .meta{ margin:0; font-size:12px; line-height:1.2; color:#475569; }
</style>
