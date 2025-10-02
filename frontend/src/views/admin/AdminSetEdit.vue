<template>
  <div class="card">
    <h2>Edit Test Set</h2>

    <div v-if="loading" class="muted">Loading...</div>
    <div v-else>
      <div class="form-grid">
        <div class="row">
          <label>Category</label>
          <input class="input" :value="categoryName(setData.category_id)" disabled />
        </div>
        <div class="row full"><label>Title</label><input v-model="form.title" class="input" /></div>
        <div class="row full"><label>Description</label><input v-model="form.description" class="input" /></div>
        <div class="row">
          <label>Time (minutes)</label>
          <input v-model.number="form.time_limit_minutes" type="number" min="1" class="input" />
        </div>
        <div class="row"><label><input type="checkbox" v-model="form.is_active" /> Active</label></div>
      </div>

      <h3 style="margin-top:16px;">Questions</h3>
      <div class="q-list">
        <div v-for="(q,i) in form.questions" :key="i" class="q-item">
          <div class="q-head">
            <div class="q-index">Q{{ i+1 }}</div>
            <button class="btn secondary" @click="removeQuestion(i)">Remove</button>
          </div>
          <div class="q-rich">
            <label>Question Text</label>
            <RichTextEditor v-model="q._text" placeholder="Write the question here..." />
            <div class="q-image-row">
              <div class="preview" v-if="q._img">
                <img :src="resolveImg(q._img)" alt="question" />
                <button class="btn secondary" type="button" @click="removeImage(i)">Remove Image</button>
              </div>
              <div class="upload">
                <label>Question Image</label>
                <input class="input" v-model="q._img" placeholder="/uploads/... or full URL" />
                <input type="file" @change="onUploadQuestion($event, i)" />
              </div>
            </div>
          </div>
          <div class="opt-grid">
            <input v-model="q._a_text" class="input" placeholder="Option A (text)" />
            <input v-model="q._b_text" class="input" placeholder="Option B (text)" />
            <input v-model="q._c_text" class="input" placeholder="Option C (text)" />
            <input v-model="q._d_text" class="input" placeholder="Option D (text)" />
            <input v-model="q._e_text" class="input" placeholder="Option E (text)" />
            <input v-model="q.correct_answer" class="input" maxlength="1" placeholder="Correct (A-E)" />
          </div>
          <div class="opt-images">
            <div class="opt-img-item" v-for="l in ['A','B','C','D','E']" :key="l">
              <div class="lbl">Image {{ l }}</div>
              <div class="opt-img-preview" v-if="optVal(q, l).img">
                <img :src="resolveImg(optVal(q, l).img)" alt="option" />
                <button class="btn secondary" type="button" @click="clearOptImg(q, l)">Remove</button>
              </div>
              <input class="input" v-model="optRef(q, l).imgRef.value" placeholder="/uploads/... or full URL" />
              <input type="file" @change="onUploadOption($event, q, l)" />
            </div>
          </div>
          <div class="q-rich">
            <label>Explanation (optional)</label>
            <RichTextEditor v-model="q.explanation" placeholder="Add explanation..." />
          </div>
        </div>
      </div>
      <div class="builder-actions">
        <button class="btn secondary" @click="addQuestion">+ Add question</button>
      </div>

      <div style="display:flex; gap:8px; margin-top:16px;">
        <button class="btn" :disabled="!canSave" @click="save">Save</button>
        <router-link class="btn secondary" to="/admin/questions">Back</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../../api/client'
import RichTextEditor from '../../components/RichTextEditor.vue'

const route = useRoute()
const router = useRouter()
const setId = Number(route.params.setId)

const loading = ref(true)
const setData = ref({})
const categories = ref([])
const form = ref({ title:'', description:'', time_limit_minutes:60, is_active:true, questions:[] })

function categoryName(id){
  const c = categories.value.find(x => x.id === id)
  return c ? c.name : id
}

onMounted(async () => {
  const [{ data: cats }, { data: setInfo }, { data: qs }] = await Promise.all([
    api.get('/categories/'),
    api.get(`/sets/${setId}`),
    api.get('/questions/', { params: { question_set_id: setId } })
  ])
  categories.value = cats
  setData.value = setInfo
  form.value = {
    title: setInfo.title,
    description: setInfo.description || '',
    time_limit_minutes: setInfo.time_limit_minutes || 60,
    is_active: setInfo.is_active !== false,
    questions: qs.map(q => {
      const pr = parseRich(q.question_text)
      const a = parseRich(q.option_a)
      const b = parseRich(q.option_b)
      const c = parseRich(q.option_c)
      const d = parseRich(q.option_d)
      const e = parseRich(q.option_e)
      return ({
        _text: pr.text,
        _img: pr.img,
        _a_text: a.text, _a_img: a.img,
        _b_text: b.text, _b_img: b.img,
        _c_text: c.text, _c_img: c.img,
        _d_text: d.text, _d_img: d.img,
        _e_text: e.text, _e_img: e.img,
        correct_answer: q.correct_answer,
        explanation: q.explanation || '',
        is_featured: q.is_featured || false,
        difficulty_level: q.difficulty_level || 'medium',
      })
    })
  }
  loading.value = false
})

const canSave = computed(() => {
  const f = form.value
  if (!f.title || !f.time_limit_minutes) return false
  if (!Array.isArray(f.questions) || f.questions.length === 0) return false
  const validAns = new Set(['A','B','C','D','E'])
  return f.questions.every(q =>
    String(q._text || '').trim() !== '' &&
    String(q._a_text || '').trim() !== '' &&
    String(q._b_text || '').trim() !== '' &&
    String(q._c_text || '').trim() !== '' &&
    String(q._d_text || '').trim() !== '' &&
    String(q._e_text || '').trim() !== '' &&
    validAns.has(String(q.correct_answer || '').toUpperCase())
  )
})

function addQuestion(){
  form.value.questions.push({ _text:'', _img:'', _a_text:'', _a_img:'', _b_text:'', _b_img:'', _c_text:'', _c_img:'', _d_text:'', _d_img:'', _e_text:'', _e_img:'', correct_answer:'', explanation:'', is_featured:false, difficulty_level:'medium' })
}
function removeQuestion(i){ form.value.questions.splice(i,1) }

async function save(){
  const payload = {
    title: form.value.title,
    description: form.value.description,
    time_limit_minutes: form.value.time_limit_minutes,
    is_active: form.value.is_active,
    questions: form.value.questions.map(q => ({
      question_text: composeRich(q._text, q._img),
      option_a: composeRich(q._a_text, q._a_img),
      option_b: composeRich(q._b_text, q._b_img),
      option_c: composeRich(q._c_text, q._c_img),
      option_d: composeRich(q._d_text, q._d_img),
      option_e: composeRich(q._e_text, q._e_img),
      correct_answer: q.correct_answer,
      explanation: q.explanation,
      is_featured: q.is_featured,
      difficulty_level: q.difficulty_level,
    })),
  }
  await api.put(`/sets/${setId}/with-questions`, payload)
  router.push('/admin/questions')
}

function parseRich(val){
  try{
    if (typeof val === 'string' && val.trim().startsWith('{')){
      const obj = JSON.parse(val)
      return { text: obj.text || '', img: obj.img || '' }
    }
  }catch{}
  return { text: val || '', img: '' }
}
function composeRich(text, img){
  const t = (text||'').trim()
  const i = (img||'').trim()
  if (!i) return t
  return JSON.stringify({ text: t, img: i })
}
function resolveImg(src){
  if (!src) return ''
  const s = String(src)
  if (/^https?:\/\//i.test(s) || s.startsWith('data:image')) return s
  const path = s.startsWith('/') ? s : `/${s}`
  if (path.startsWith('/uploads/')) return `${window.location.origin.replace('5173','8000')}${path}`
  return path
}
async function onUploadQuestion(ev, index){
  const file = ev.target.files?.[0]
  if (!file) return
  const fd = new FormData()
  fd.append('file', file)
  const { data } = await api.post('/files/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
  const url = data.url
  const u = new URL(url)
  form.value.questions[index]._img = `${u.pathname}`
}
function removeImage(index){ form.value.questions[index]._img = '' }

// Option helpers
function optVal(q, l){
  const key = `_${l.toLowerCase()}_img`
  return { img: q[key] }
}
function clearOptImg(q, l){ q[`_${l.toLowerCase()}_img`] = '' }
function optRef(q, l){
  const key = `_${l.toLowerCase()}_img`
  const obj = { value: q[key] }
  return { imgRef: {
    get value(){ return q[key] },
    set value(v){ q[key] = v }
  }}
}
async function onUploadOption(ev, q, l){
  const file = ev.target.files?.[0]
  if (!file) return
  const fd = new FormData()
  fd.append('file', file)
  const { data } = await api.post('/files/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
  const url = data.url
  const u = new URL(url)
  q[`_${l.toLowerCase()}_img`] = `${u.pathname}`
}
</script>

<style scoped>
.muted { color:#64748b; }
.form-grid { display:grid; grid-template-columns: repeat(2, 1fr); gap:12px; }
.form-grid .row { display:flex; flex-direction:column; gap:6px; }
.form-grid .row.full { grid-column: 1 / -1; }
.q-list { display:flex; flex-direction:column; gap:12px; margin-top:12px; }
.q-item { background:#f8fafc; padding:12px; border-radius:10px; border:1px solid #e2e8f0; }
.q-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }
.q-index { font-weight:700; }
.opt-grid { display:grid; grid-template-columns:repeat(3, 1fr); gap:8px; margin:8px 0; }
.builder-actions { display:flex; gap:8px; }
/* Rich question area */
.q-rich{ display:flex; flex-direction:column; gap:8px; }
.q-image-row{ display:grid; grid-template-columns: 1fr; gap:8px; }
.q-image-row .preview{ background:white; border:1px solid #e2e8f0; border-radius:8px; padding:8px; display:flex; flex-direction:column; gap:6px; align-items:flex-start; }
.q-image-row .preview img{ max-width:100%; width:auto; height:auto; max-height:320px; object-fit:contain; border-radius:6px; display:block; }
/* Option images */
.opt-images{ display:grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap:12px; margin:8px 0; }
.opt-img-item{ background:#fff; border:1px solid #e2e8f0; border-radius:8px; padding:8px; display:flex; flex-direction:column; gap:6px; min-width:0; }
.opt-img-item .lbl{ font-size:12px; font-weight:700; color:#475569; }
.opt-img-preview{ overflow:hidden; border-radius:6px; }
.opt-img-preview img{ max-width:100%; width:100%; height:auto; max-height:160px; object-fit:contain; display:block; }
.opt-img-item .input{ width:100%; min-width:0; }
@media (min-width: 1200px){ .opt-images{ grid-template-columns: repeat(5, 1fr); } }
@media (min-width: 1500px){ .opt-images{ grid-template-columns: repeat(6, 1fr); } }
@media (max-width: 900px){ .opt-images{ grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); } .q-image-row .preview img{ max-height:260px; } .opt-img-preview img{ max-height:140px; } }
</style>
