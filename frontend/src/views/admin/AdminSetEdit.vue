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
        <div class="row">
          <label>Access Level</label>
          <select v-model="form.access_level" class="input">
            <option value="free">Free</option>
            <option value="paid">Paid</option>
          </select>
        </div>
      </div>

      <h3 style="margin-top:16px;">Questions</h3>
      <div class="q-list">
        <div v-for="(q,i) in form.questions" :key="i" class="q-item">
          <div class="q-head">
            <div class="q-index">Q{{ i+1 }}</div>
            <button class="btn secondary" @click="removeQuestion(i)">Remove</button>
          </div>
          <div class="row" style="margin-bottom:6px;">
            <label style="font-weight:600;">Type</label>
            <select v-model="q.type" class="input" style="max-width:220px;">
              <option value="mcq">Multiple Choice (single)</option>
              <option value="multi">Multiple Answers</option>
              <option value="essay">Essay</option>
            </select>
          </div>
          <div class="q-rich">
            <label>Question text</label>
            <RichTextEditor v-model="q._text" placeholder="Write the question here..." />
            <CdnUploader v-model="q._img" />
          </div>
          <div v-if="q.type==='mcq' || q.type==='multi'" class="opt-grid2">
            <div v-for="(opt, oi) in q.options" :key="oi" class="opt-item">
              <div class="opt-head">
                <span class="badge">{{ letter(oi) }}</span>
                <button v-if="q.options.length > 1" class="btn tiny secondary" @click="removeOption(q, oi)">Remove</button>
              </div>
              <input v-model="opt.text" class="input" :placeholder="`Option ${letter(oi)}`" />
              <CdnUploader v-model="opt.img" />
              <label v-if="q.type==='multi'" style="display:flex; align-items:center; gap:6px; font-size:13px; color:#334155;">
                <input type="checkbox" :checked="(q.correct_idxs||[]).includes(oi)" @change="toggleMultiCorrect(q, oi, $event)"/>
                Mark as correct
              </label>
            </div>
          </div>
          <div v-if="q.type==='mcq' || q.type==='multi'" class="opt-actions">
            <button class="btn secondary" :disabled="q.options.length >= 5" @click="addOption(q)">+ Add answer</button>
            <template v-if="q.type==='mcq'">
              <select v-model.number="q.correct_idx" class="input" style="max-width:180px;">
                <option v-for="(_, oi) in q.options" :key="`c-${oi}`" :value="oi">Correct: {{ letter(oi) }}</option>
              </select>
            </template>
            <template v-else>
              <span class="muted">Select one or more correct answers above</span>
            </template>
          </div>
          <div v-else class="muted" style="margin:6px 0 0;">Essay question. No predefined options. Answers will be graded manually.</div>
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

      <div class="import-card">
        <h3>Import Questions from Excel (.xlsx)</h3>
        <p class="muted">Upload a file with headers: <code>type, question_text, question_img, option_a_text, option_a_img, ... option_e_text, option_e_img, correct_answer, explanation</code>. Types: <code>mcq</code> | <code>multi</code> | <code>essay</code>.</p>
        <div class="import-row">
          <input ref="fileInput" type="file" accept=".xlsx" @change="onFileChange" />
          <button class="btn" :disabled="!xlsxFile || importing" @click="doImport">{{ importing ? 'Importing…' : 'Import' }}</button>
          <button class="btn secondary" :disabled="!xlsxFile || importing" @click="doPreview">Preview</button>
          <a class="btn secondary" :href="templateUrl" target="_blank" rel="noopener">Download template</a>
        </div>
        <div v-if="importResult" class="import-result">
          <div><strong>Created:</strong> {{ importResult.created }}</div>
          <div v-if="(importResult.errors||[]).length"><strong>Errors:</strong>
            <ul>
              <li v-for="(e,i) in importResult.errors" :key="i">{{ e }}</li>
            </ul>
          </div>
        </div>
        <div v-if="previewOpen" class="preview-panel">
          <div class="preview-head">
            <strong>Preview parsed rows</strong>
            <button class="btn tiny" @click="previewOpen=false">Close</button>
          </div>
          <div class="preview-body">
            <table class="preview-table">
              <thead>
                <tr>
                  <th>Row</th>
                  <th>Type</th>
                  <th>Q Text</th>
                  <th>Q Img</th>
                  <th>A Img</th>
                  <th>B Img</th>
                  <th>C Img</th>
                  <th>D Img</th>
                  <th>E Img</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(r,i) in previewRows" :key="i">
                  <td>{{ r.row }}</td>
                  <td>{{ r.type }}</td>
                  <td>{{ r.question_text }}</td>
                  <td><a v-if="r.question_img" :href="r.question_img" target="_blank">open</a></td>
                  <td><a v-if="r.option_a_img" :href="r.option_a_img" target="_blank">open</a></td>
                  <td><a v-if="r.option_b_img" :href="r.option_b_img" target="_blank">open</a></td>
                  <td><a v-if="r.option_c_img" :href="r.option_c_img" target="_blank">open</a></td>
                  <td><a v-if="r.option_d_img" :href="r.option_d_img" target="_blank">open</a></td>
                  <td><a v-if="r.option_e_img" :href="r.option_e_img" target="_blank">open</a></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../../api/client'
import RichTextEditor from '../../components/RichTextEditor.vue'
import CdnUploader from '../../components/CdnUploader.vue'

const route = useRoute()
const router = useRouter()
const setId = Number(route.params.setId)

const loading = ref(true)
const setData = ref({})
const categories = ref([])
const form = ref({ title:'', description:'', time_limit_minutes:60, is_active:true, questions:[] })
const xlsxFile = ref(null)
const importing = ref(false)
const importResult = ref(null)
const templateUrl = `${window.location.origin.replace('5173','8000')}/api/v1/sets/import-template.xlsx`
const previewOpen = ref(false)
const previewRows = ref([])

function categoryName(id){
  const c = categories.value.find(x => x.id === id)
  return c ? c.name : id
}

async function doPreview(){
  if (!xlsxFile.value) return
  try{
    const fd = new FormData()
    fd.append('file', xlsxFile.value)
    const { data } = await api.post(`/sets/${setId}/import-xlsx/preview`, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    previewRows.value = data.rows || []
    previewOpen.value = true
  }catch(e){
    previewRows.value = []
    previewOpen.value = true
  }
}

function onFileChange(e){
  importResult.value = null
  xlsxFile.value = e.target.files?.[0] || null
}
async function doImport(){
  if (!xlsxFile.value) return
  importing.value = true
  try{
    const fd = new FormData()
    fd.append('file', xlsxFile.value)
    const { data } = await api.post(`/sets/${setId}/import-xlsx`, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    importResult.value = data
    // reload questions list
    const { data: qs } = await api.get('/questions/', { params: { question_set_id: setId } })
    form.value.questions = qs.map(q => {
      const pr = parseRich(q.question_text)
      const type = q.question_type || 'mcq'
      if (type === 'essay'){
        return ({ type:'essay', _text: pr.text, _img: pr.img, options:[], correct_idx:null, explanation: q.explanation || '', is_featured: q.is_featured || false, difficulty_level: q.difficulty_level || 'medium' })
      }
      const arr = [parseRich(q.option_a), parseRich(q.option_b), parseRich(q.option_c), parseRich(q.option_d), parseRich(q.option_e)]
      const options = arr.map(x => ({ text: x.text || '', img: x.img || '' })).filter(x => (x.text && x.text.trim()) || (x.img && x.img.trim()))
      if (type === 'multi'){
        const letters = String(q.correct_answer||'').split(',').map(s => s.trim().toUpperCase()).filter(Boolean)
        const correct_idxs = letters.map(l => ['A','B','C','D','E'].indexOf(l)).filter(i => i>=0)
        return ({ type:'multi', _text: pr.text, _img: pr.img, options: options.length ? options : [{ text:'', img:'' }], correct_idxs, explanation: q.explanation || '', is_featured: q.is_featured || false, difficulty_level: q.difficulty_level || 'medium' })
      } else {
        const correctLetter = String(q.correct_answer || 'A').toUpperCase()
        const idx = ['A','B','C','D','E'].indexOf(correctLetter)
        const correct_idx = Math.min(Math.max(0, idx), Math.max(0, options.length - 1))
        return ({ type:'mcq', _text: pr.text, _img: pr.img, options: options.length ? options : [{ text:'', img:'' }], correct_idx, explanation: q.explanation || '', is_featured: q.is_featured || false, difficulty_level: q.difficulty_level || 'medium' })
      }
    })
  } catch(e){
    importResult.value = { created: 0, errors: [ e?.response?.data?.detail || e.message || 'Import failed' ] }
  } finally {
    importing.value = false
  }
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
    access_level: setInfo.access_level || 'free',
    questions: qs.map(q => {
      const pr = parseRich(q.question_text)
      const type = q.question_type || 'mcq'
      if (type === 'essay'){
        return ({
          type:'essay',
          _text: pr.text,
          _img: pr.img,
          options:[], correct_idx:null,
          explanation: q.explanation || '',
          is_featured: q.is_featured || false,
          difficulty_level: q.difficulty_level || 'medium',
        })
      }
      const arr = [parseRich(q.option_a), parseRich(q.option_b), parseRich(q.option_c), parseRich(q.option_d), parseRich(q.option_e)]
      const options = arr
        .map(x => ({ text: x.text || '', img: x.img || '' }))
        .filter(x => (x.text && x.text.trim()) || (x.img && x.img.trim()))
      if ((q.question_type||'mcq') === 'multi'){
        const letters = String(q.correct_answer||'').split(',').map(s => s.trim().toUpperCase()).filter(Boolean)
        const correct_idxs = letters.map(l => ['A','B','C','D','E'].indexOf(l)).filter(i => i>=0)
        return ({
          type:'multi',
          _text: pr.text,
          _img: pr.img,
          options: options.length ? options : [{ text:'', img:'' }],
          correct_idxs,
          explanation: q.explanation || '',
          is_featured: q.is_featured || false,
          difficulty_level: q.difficulty_level || 'medium',
        })
      } else {
        const correctLetter = String(q.correct_answer || 'A').toUpperCase()
        const idx = ['A','B','C','D','E'].indexOf(correctLetter)
        const correct_idx = Math.min(Math.max(0, idx), Math.max(0, options.length - 1))
        return ({
          type:'mcq',
          _text: pr.text,
          _img: pr.img,
          options: options.length ? options : [{ text:'', img:'' }],
          correct_idx,
          explanation: q.explanation || '',
          is_featured: q.is_featured || false,
          difficulty_level: q.difficulty_level || 'medium',
        })
      }
    })
  }
  loading.value = false
})

const canSave = computed(() => {
  const f = form.value
  if (!f.title || !f.time_limit_minutes) return false
  if (!Array.isArray(f.questions) || f.questions.length === 0) return false
  return f.questions.every(q => {
    const hasStem = String(q._text || '').trim() !== '' || String(q._img || '').trim() !== ''
    if (!hasStem) return false
    if ((q.type||'mcq') === 'essay') return true
    if (!Array.isArray(q.options) || q.options.length < 1 || q.options.length > 5) return false
    const allOptsOk = q.options.every(op => (op.text && op.text.trim()) || (op.img && op.img.trim()))
    if (!allOptsOk) return false
    if (q.type==='multi'){
      return Array.isArray(q.correct_idxs) && q.correct_idxs.length>0 && q.correct_idxs.every(i => i>=0 && i<q.options.length)
    }
    return typeof q.correct_idx === 'number' && q.correct_idx >= 0 && q.correct_idx < q.options.length
  })
})

function addQuestion(){
  form.value.questions.push({ type:'mcq', _text:'', _img:'', options:[{ text:'', img:'' }, { text:'', img:'' }, { text:'', img:'' }], correct_idx: 0, explanation:'', is_featured:false, difficulty_level:'medium' })
}
function toggleMultiCorrect(q, idx, ev){
  const set = new Set(q.correct_idxs || [])
  if (ev.target.checked) set.add(idx); else set.delete(idx)
  q.correct_idxs = Array.from(set).sort((a,b)=>a-b)
}
function removeQuestion(i){ form.value.questions.splice(i,1) }
function letter(i){ return String.fromCharCode('A'.charCodeAt(0) + i) }
function addOption(q){ if (q.options.length < 5) q.options.push({ text:'', img:'' }) }
function removeOption(q, idx){ if (q.options.length > 1){ q.options.splice(idx,1); if (q.correct_idx >= q.options.length) q.correct_idx = Math.max(0, q.options.length-1) } }

async function save(){
  const payload = {
    title: form.value.title,
    description: form.value.description,
    time_limit_minutes: form.value.time_limit_minutes,
    is_active: form.value.is_active,
    access_level: form.value.access_level || 'free',
    questions: form.value.questions.map(q => {
      const base = {
        question_text: composeRich(q._text, q._img),
        explanation: q.explanation,
        is_featured: q.is_featured,
        difficulty_level: q.difficulty_level,
        question_type: q.type || 'mcq',
      }
      if ((q.type||'mcq') === 'essay'){
        return { ...base, option_a:'', option_b:'', option_c:'', option_d:'', option_e:'', correct_answer:'' }
      }
      const texts = (q.options || []).map(op => composeRich(op.text, op.img))
      const pad = (i) => texts[i] || ''
      if ((q.type||'mcq') === 'multi'){
        const letters = (q.correct_idxs||[]).map(letter).sort()
        return { ...base,
          option_a: pad(0), option_b: pad(1), option_c: pad(2), option_d: pad(3), option_e: pad(4),
          correct_answer: letters.join(','),
        }
      } else {
        const correct_letter = letter(q.correct_idx || 0)
        return { ...base,
          option_a: pad(0), option_b: pad(1), option_c: pad(2), option_d: pad(3), option_e: pad(4),
          correct_answer: correct_letter,
        }
      }
    }),
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
// Old manual upload helpers removed in favor of CdnUploader
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
  /* Dynamic options layout (match AdminQuestions.vue) */
  .opt-grid2 { display:grid; grid-template-columns: repeat(3, 1fr); gap:8px; margin:8px 0; }
  .opt-item { background:#fff; border:1px solid #e2e8f0; border-radius:10px; padding:8px; display:flex; flex-direction:column; gap:6px; }
  .opt-head { display:flex; justify-content:space-between; align-items:center; }
  .badge { display:inline-flex; width:22px; height:22px; border-radius:999px; align-items:center; justify-content:center; font-weight:700; background:#f1f5f9; color:#0f172a; }
  .opt-actions { display:flex; gap:8px; align-items:center; margin-bottom:8px; }
  .btn.tiny { padding:4px 8px; font-size:12px; }
.builder-actions { display:flex; gap:8px; }
  /* Rich question area */
  .q-rich{ display:flex; flex-direction:column; gap:8px; }
  @media (max-width: 900px){ .opt-grid2{ grid-template-columns: 1fr; } }

  /* Import */
  .import-card{ margin-top:18px; padding:12px; border:1px solid #e2e8f0; border-radius:10px; background:#fff; }
  .import-row{ display:flex; gap:8px; align-items:center; margin-top:8px; }
  .import-result{ margin-top:8px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:8px; }
  .preview-panel{ margin-top:10px; border:1px solid #e2e8f0; border-radius:10px; background:#fff; }
  .preview-head{ display:flex; justify-content:space-between; align-items:center; padding:8px 10px; border-bottom:1px solid #e2e8f0; }
  .preview-body{ padding:8px 10px; overflow:auto; max-height:300px; }
  .preview-table{ width:100%; border-collapse:collapse; font-size:13px; }
  .preview-table th, .preview-table td{ border:1px solid #e5e7eb; padding:4px 6px; white-space:nowrap; }
</style>
