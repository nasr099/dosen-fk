<template>
  <div class="card">
    <h2>Questions</h2>

    <div class="filters">
      <select v-model="selectedCategoryId" class="input" @change="onCategoryChange">
        <option :value="null">All Categories</option>
        <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>
      <select v-model="selectedSetId" class="input" :disabled="!selectedCategoryId" @change="loadQuestions">
        <option :value="null">All Sets</option>
        <option v-for="s in sets" :key="s.id" :value="s.id">{{ s.title }}</option>
      </select>
    </div>
    <div class="builder">
      <div class="form-grid">
        <div class="row">
          <label>Category</label>
          <select v-model="builder.category_id" class="input" required @change="loadBuilderSets">
            <option value="" disabled>Select category</option>
            <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </div>
        <div class="row full"><label>Set Title</label><input v-model="builder.title" class="input" placeholder="e.g., Latihan Anatomi 2025 #3" /></div>
        <div class="row full"><label>Description</label><input v-model="builder.description" class="input" placeholder="Optional" /></div>
        <div class="row"><label>Time (minutes)</label><input v-model.number="builder.time_limit_minutes" type="number" min="1" class="input" /></div>
      </div>

      <div class="q-list">
        <div v-for="(q,i) in builder.questions" :key="i" class="q-item">
          <div class="q-head">
            <div class="q-index">Q{{ i+1 }}</div>
            <button class="btn secondary" @click="removeBuilderQuestion(i)">Remove</button>
          </div>
          <label style="font-weight:600; margin-bottom:4px; display:block;">Question text</label>
          <RichTextEditor v-model="q.question_text" placeholder="Write the question here..." />
          <div class="image-row">
            <input v-model="q.question_img" class="input" placeholder="Question image URL (optional)" />
            <label class="btn secondary" style="white-space:nowrap;">
              Upload
              <input type="file" accept="image/*" style="display:none;" @change="e => onFileChange(i, 'question_img', e)" />
            </label>
          </div>
          <div class="opt-grid">
            <div style="display:flex; flex-direction:column; gap:6px;">
              <input v-model="q.option_a" class="input" placeholder="Option A" />
              <div class="image-row">
                <input v-model="q.option_a_img" class="input" placeholder="Option A image URL (optional)" />
                <label class="btn secondary" style="white-space:nowrap;">
                  Upload
                  <input type="file" accept="image/*" style="display:none;" @change="e => onFileChange(i, 'option_a_img', e)" />
                </label>
              </div>
            </div>
            <div style="display:flex; flex-direction:column; gap:6px;">
              <input v-model="q.option_b" class="input" placeholder="Option B" />
              <div class="image-row">
                <input v-model="q.option_b_img" class="input" placeholder="Option B image URL (optional)" />
                <label class="btn secondary" style="white-space:nowrap;">
                  Upload
                  <input type="file" accept="image/*" style="display:none;" @change="e => onFileChange(i, 'option_b_img', e)" />
                </label>
              </div>
            </div>
            <div style="display:flex; flex-direction:column; gap:6px;">
              <input v-model="q.option_c" class="input" placeholder="Option C" />
              <div class="image-row">
                <input v-model="q.option_c_img" class="input" placeholder="Option C image URL (optional)" />
                <label class="btn secondary" style="white-space:nowrap;">
                  Upload
                  <input type="file" accept="image/*" style="display:none;" @change="e => onFileChange(i, 'option_c_img', e)" />
                </label>
              </div>
            </div>
            <div style="display:flex; flex-direction:column; gap:6px;">
              <input v-model="q.option_d" class="input" placeholder="Option D" />
              <div class="image-row">
                <input v-model="q.option_d_img" class="input" placeholder="Option D image URL (optional)" />
                <label class="btn secondary" style="white-space:nowrap;">
                  Upload
                  <input type="file" accept="image/*" style="display:none;" @change="e => onFileChange(i, 'option_d_img', e)" />
                </label>
              </div>
            </div>
            <div style="display:flex; flex-direction:column; gap:6px;">
              <input v-model="q.option_e" class="input" placeholder="Option E" />
              <div class="image-row">
                <input v-model="q.option_e_img" class="input" placeholder="Option E image URL (optional)" />
                <label class="btn secondary" style="white-space:nowrap;">
                  Upload
                  <input type="file" accept="image/*" style="display:none;" @change="e => onFileChange(i, 'option_e_img', e)" />
                </label>
              </div>
            </div>
            <input v-model="q.correct_answer" class="input" maxlength="1" placeholder="Correct (A-E)" />
          </div>
          <label style="font-weight:600; margin-bottom:4px; display:block;">Explanation (optional)</label>
          <RichTextEditor v-model="q.explanation" placeholder="Add explanation..." />
        </div>
      </div>

      <div class="builder-actions">
        <button class="btn secondary" @click="addBuilderQuestion">+ Add question</button>
        <button class="btn" :disabled="!canSaveSet" @click="saveSetWithQuestions">Save set</button>
      </div>
    </div>
    <div class="sets-wrap">
      <h3>Sets Overview</h3>
      <div class="grid cols-3">
        <div v-for="s in filteredSetsOverview" :key="s.id" class="q-card">
          <div class="q-title">{{ s.title }}</div>
          <div class="q-meta">Category: {{ categoryName(s.category_id) }}</div>
          <div class="q-meta">Questions: {{ s.count }}</div>
          <div class="q-meta">Time: {{ s.time_limit_minutes }} min</div>
          <div style="margin-top:8px; display:flex; gap:8px;">
            <router-link class="btn" :to="{ path: `/admin/sets/${s.id}` }">Edit</router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { onMounted, ref, computed } from 'vue'
import api from '../../api/client'
import RichTextEditor from '../../components/RichTextEditor.vue'
const categories = ref([])
const sets = ref([])
const selectedCategoryId = ref(null)
const selectedSetId = ref(null)
const setsOverview = ref([])
// Set Builder state
const builder = ref({ category_id:'', title:'', description:'', time_limit_minutes:105, questions: [] })

async function load(){
  const { data: cats } = await api.get('/categories/')
  categories.value = cats
  await refreshSetsOverview()
}

onMounted(load)

async function refreshSetsOverview(){
  // flatten all sets and count questions per set
  const allSets = []
  for (const c of categories.value){
    const { data: sets } = await api.get('/sets/', { params: { category_id: c.id } })
    for (const s of sets){
      const { data: qs } = await api.get('/questions/', { params: { question_set_id: s.id } })
      allSets.push({ ...s, count: qs.length })
    }
  }
  setsOverview.value = allSets
}

function categoryName(id){
  const c = categories.value.find(x => x.id === id)
  return c ? c.name : id
}

// Filters logic: load sets for selected category and filter overview
async function onCategoryChange(){
  sets.value = []
  selectedSetId.value = null
  if (selectedCategoryId.value){
    const { data } = await api.get('/sets/', { params: { category_id: selectedCategoryId.value } })
    sets.value = data
  }
}

async function loadQuestions(){
  // no-op; filtering happens in computed below
}

const filteredSetsOverview = computed(() => {
  let arr = setsOverview.value
  if (selectedCategoryId.value){
    arr = arr.filter(s => s.category_id === selectedCategoryId.value)
  }
  if (selectedSetId.value){
    arr = arr.filter(s => s.id === selectedSetId.value)
  }
  return arr
})

// Builder helpers
function addBuilderQuestion(){
  builder.value.questions.push({
    question_text:'', question_img:'',
    option_a:'', option_a_img:'',
    option_b:'', option_b_img:'',
    option_c:'', option_c_img:'',
    option_d:'', option_d_img:'',
    option_e:'', option_e_img:'',
    correct_answer:'', explanation:'', is_featured:false, difficulty_level:'medium'
  })
}
function removeBuilderQuestion(i){ builder.value.questions.splice(i,1) }
const canSaveSet = computed(() => {
  const b = builder.value
  if (!b.category_id || !b.title || b.questions.length === 0) return false
  // allow either text or image for question/options
  return b.questions.every(q => (
    ((q.question_text && q.question_text.trim()) || (q.question_img && q.question_img.trim())) &&
    ((q.option_a && q.option_a.trim()) || (q.option_a_img && q.option_a_img.trim())) &&
    ((q.option_b && q.option_b.trim()) || (q.option_b_img && q.option_b_img.trim())) &&
    ((q.option_c && q.option_c.trim()) || (q.option_c_img && q.option_c_img.trim())) &&
    ((q.option_d && q.option_d.trim()) || (q.option_d_img && q.option_d_img.trim())) &&
    ((q.option_e && q.option_e.trim()) || (q.option_e_img && q.option_e_img.trim())) &&
    q.correct_answer
  ))
})
async function saveSetWithQuestions(){
  const payload = {
    category_id: Number(builder.value.category_id),
    title: builder.value.title,
    description: builder.value.description,
    time_limit_minutes: builder.value.time_limit_minutes,
    is_active: true,
    questions: builder.value.questions.map(q => ({
      question_text: toRich(q.question_text, q.question_img),
      option_a: toRich(q.option_a, q.option_a_img),
      option_b: toRich(q.option_b, q.option_b_img),
      option_c: toRich(q.option_c, q.option_c_img),
      option_d: toRich(q.option_d, q.option_d_img),
      option_e: toRich(q.option_e, q.option_e_img),
      correct_answer: q.correct_answer,
      explanation: q.explanation,
      is_featured: q.is_featured,
      difficulty_level: q.difficulty_level,
    }))
  }
  await api.post('/sets/with-questions', payload)
  builder.value = { category_id:'', title:'', description:'', time_limit_minutes:105, questions: [] }
  await refreshSetsOverview()
}
async function loadBuilderSets(){
  if (!builder.value.category_id) return
  await api.get('/sets/', { params: { category_id: builder.value.category_id } })
}

function toRich(text, img){
  const t = (text || '').trim()
  const i = (img || '').trim()
  if (!i){ return t }
  return JSON.stringify({ text: t, img: i })
}

async function onFileChange(index, field, evt){
  const file = evt.target.files && evt.target.files[0]
  if (!file) return
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post('/files/upload', form, { headers: { 'Content-Type': 'multipart/form-data' } })
  builder.value.questions[index][field] = data.url
}
</script>

<style scoped>
.filters { display:flex; gap:12px; margin-bottom:12px; }
.tabs { display:flex; gap:8px; margin-bottom:12px; }
.tab { padding:8px 12px; border-radius:8px; border:1px solid #e2e8f0; background:white; cursor:pointer; }
.tab.active { background:#2563eb; color:white; border-color:#2563eb; }
.form-grid { display:grid; grid-template-columns: repeat(2, 1fr); gap:12px; }
.form-grid .row { display:flex; flex-direction:column; gap:6px; }
.form-grid .row.full { grid-column: 1 / -1; }
.q-card { background:white; border-radius:12px; padding:12px; box-shadow:0 2px 10px rgba(0,0,0,0.06); }
.q-title { font-weight:700; margin-bottom:6px; }
.q-meta { color:#475569; font-size:14px; }
.builder { border-top:1px solid #e2e8f0; padding-top:12px; margin-bottom:12px; }
.q-list { display:flex; flex-direction:column; gap:12px; margin-top:12px; }
.q-item { background:#f8fafc; padding:12px; border-radius:10px; border:1px solid #e2e8f0; }
.q-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }
.q-index { font-weight:700; }
.opt-grid { display:grid; grid-template-columns:repeat(3, 1fr); gap:8px; margin:8px 0; }
.builder-actions { display:flex; gap:8px; }
.sets-wrap { margin-top:24px; }
.image-row { display:flex; gap:8px; align-items:center; }
</style>
