<template>
  <div class="card">
    <h2>Questions</h2>

    
    <div class="builder">
      <div class="tabs" style="margin-bottom:10px;">
        <button class="tab" :class="{ active: mode==='manual' }" @click="mode='manual'">Build Manually</button>
        <button class="tab" :class="{ active: mode==='import' }" @click="mode='import'">Import from Excel</button>
      </div>
      <div class="form-grid">
        <div class="row">
          <label>Category</label>
          <select v-model="builder.category_id" class="input" required @change="loadBuilderSets">
            <option value="" disabled>Select category</option>
            <option v-for="c in subCategories" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </div>
        <div class="row full"><label>Set Title</label><input v-model="builder.title" class="input" placeholder="e.g., Latihan Anatomi 2025 #3" /></div>
        <div class="row full"><label>Description</label><input v-model="builder.description" class="input" placeholder="Optional" /></div>
        <div class="row"><label>Time (minutes)</label><input v-model.number="builder.time_limit_minutes" type="number" min="1" class="input" /></div>
      </div>
      <div v-if="mode==='manual'" class="q-list">
        <div v-for="(q,i) in builder.questions" :key="i" class="q-item">
          <div class="q-head">
            <div class="q-index">Q{{ i+1 }}</div>
            <button class="btn secondary" @click="removeBuilderQuestion(i)">Remove</button>
          </div>
          <div class="row" style="margin-bottom:6px;">
            <label style="font-weight:600;">Type</label>
            <select v-model="q.type" class="input" style="max-width:220px;">
              <option value="mcq">Multiple Choice (single)</option>
              <option value="multi">Multiple Answers</option>
              <option value="essay">Essay</option>
            </select>
          </div>
          <label style="font-weight:600; margin-bottom:4px; display:block;">Question text</label>
          <RichTextEditor v-model="q.question_text" placeholder="Write the question here..." />
          <CdnUploader v-model="q.question_img" />
          <div v-if="q.type==='mcq' || q.type==='multi'" class="opt-grid">
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
                <option v-for="(opt, oi) in q.options" :key="`c-${oi}`" :value="oi">Correct: {{ letter(oi) }}</option>
              </select>
            </template>
            <template v-else>
              <span class="muted">Select one or more correct answers above</span>
            </template>
          </div>
          <div v-else class="muted" style="margin:6px 0 0;">Essay question. No predefined options. Answers will be graded manually.</div>
          <label style="font-weight:600; margin-bottom:4px; display:block;">Explanation (optional)</label>
          <RichTextEditor v-model="q.explanation" placeholder="Add explanation..." />
        </div>
      </div>

      <div v-if="mode==='manual'" class="builder-actions">
        <button class="btn secondary" @click="addBuilderQuestion('mcq')">+ Add MCQ</button>
        <button class="btn secondary" @click="addBuilderQuestion('multi')">+ Add Multiple</button>
        <button class="btn secondary" @click="addBuilderQuestion('essay')">+ Add Essay</button>
        <button class="btn" :disabled="builderIssues.length>0" @click="onSaveClicked">Save set</button>
      </div>
      <!-- Import from Excel when creating a new set -->
      <div v-if="mode==='import'" class="import-card">
        <h3>Import Questions from Excel (.xlsx)</h3>
        <p class="muted">Fill Category, Title and Time first. Upload a file with headers: <code>type, question_text, question_img, option_a_text, option_a_img, ... option_e_text, option_e_img, correct_answer, explanation</code>.</p>
        <div class="import-row">
          <input ref="fileInput" type="file" accept=".xlsx" @change="onFileChangeNew" />
          <button type="button" class="btn" :disabled="!xlsxFileNew || importingNew" @click="doImportNew">{{ importingNew ? 'Importing…' : 'Import' }}</button>
          <button type="button" class="btn secondary" :disabled="!xlsxFileNew || importingNew" @click="doPreviewNew">Preview</button>
          <button type="button" class="btn secondary" @click="downloadTemplateNew">Download template</button>
        </div>
        <div v-if="importErrorNew" class="issues" style="margin-top:8px;">
          {{ importErrorNew }}
        </div>
        <div v-if="previewOpenNew" class="preview-panel">
          <div class="preview-head">
            <strong>Preview parsed rows</strong>
            <button class="btn tiny" @click="previewOpenNew=false">Close</button>
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
                <tr v-for="(r,i) in previewRowsNew" :key="i">
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
      <div v-if="mode==='manual' && builderIssues.length>0" class="issues">
        <div class="issue-title">Fix before saving:</div>
        <ul>
          <li v-for="(msg, i) in builderIssues" :key="i">{{ msg }}</li>
        </ul>
      </div>
    </div>
    <div class="sets-wrap">
      <h3>Sets Overview</h3>
      <div class="sets-toolbar">
        <input class="input" v-model="overviewSearch" placeholder="Search by title or category…" />
        <select class="input" v-model="overviewCategoryId">
          <option :value="null">All Categories</option>
          <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
        <select class="input" v-model="overviewSort">
          <option value="newest">Sort: New → Old</option>
          <option value="oldest">Sort: Old → New</option>
          <option value="title_asc">Sort: Title A→Z</option>
          <option value="title_desc">Sort: Title Z→A</option>
          <option value="count_desc">Sort: Questions ↓</option>
          <option value="count_asc">Sort: Questions ↑</option>
        </select>
      </div>
      <table class="sets-table">
        <thead>
          <tr>
            <th>Title</th>
            <th>Category</th>
            <th style="width:100px;">Questions</th>
            <th style="width:220px;">Types</th>
            <th style="width:100px;">Time (min)</th>
            <th style="width:120px;">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in displayedSets" :key="s.id">
            <td><strong>{{ s.title }}</strong></td>
            <td>{{ categoryName(s.category_id) }}</td>
            <td>{{ s.count }}</td>
            <td>
              <span class="tag">MCQ {{ s.mcq_count || 0 }}</span>
              <span class="tag">Multi {{ s.multi_count || 0 }}</span>
              <span class="tag">Essay {{ s.essay_count || 0 }}</span>
            </td>
            <td>{{ s.time_limit_minutes }}</td>
            <td>
              <router-link class="btn tiny" :to="{ path: `/admin/sets/${s.id}` }">Edit</router-link>
              <button class="btn tiny secondary" style="margin-left:6px;" @click="removeSetOverview(s.id)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
<script setup>
import { onMounted, ref, computed } from 'vue'
import api from '../../api/client'
import RichTextEditor from '../../components/RichTextEditor.vue'
import CdnUploader from '../../components/CdnUploader.vue'
import { useRouter } from 'vue-router'
const categories = ref([])
const subCategories = computed(() => (categories.value || []).filter(c => !!c.parent_id))
const mode = ref('import') // 'manual' | 'import'
const sets = ref([])
const selectedCategoryId = ref(null)
const selectedSetId = ref(null)
const selectedType = ref('all') // all | mcq | multi | essay
const setsOverview = ref([])
// Sets Overview search/sort
const overviewSearch = ref('')
const overviewSort = ref('newest')
const overviewCategoryId = ref(null)
// Set Builder state
const builder = ref({ category_id:'', title:'', description:'', time_limit_minutes:105, questions: [] })
// Import (new set) state
const xlsxFileNew = ref(null)
const importingNew = ref(false)
const previewOpenNew = ref(false)
const previewRowsNew = ref([])
const createdSetId = ref(null) // draft set created for preview/import
const templateUrl = `${window.location.origin.replace('5173','8000')}/api/v1/sets/import-template.xlsx`
const importErrorNew = ref('')
const router = useRouter()

async function load(){
  const { data: cats } = await api.get('/categories/')
  categories.value = cats
  await refreshSetsOverview()
}

onMounted(load)
async function downloadTemplateNew(){
  try {
    const { data } = await api.get('/sets/import-template.xlsx', { responseType: 'blob' })
    const blob = new Blob([data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'import-template.xlsx'
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  } catch (e) {
    // Fallback to unauthenticated fetch then open in new tab
    try{
      const res = await fetch(templateUrl)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'import-template.xlsx'
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    }catch{
      window.open(templateUrl, '_blank', 'noopener')
    }
  }
}

async function refreshSetsOverview(){
  // flatten all sets and count questions per set
  const allSets = []
  for (const c of categories.value){
    const { data: sets } = await api.get('/sets/', { params: { category_id: c.id } })
    for (const s of sets){
      const { data: qs } = await api.get('/questions/', { params: { question_set_id: s.id } })
      let mcq = 0, multi = 0, essay = 0
      for (const q of qs){
        const t = (q.question_type) ? String(q.question_type) : guessTypeFromOptions(q)
        if (t === 'essay') essay++
        else if (t === 'multi') multi++
        else mcq++
      }
      allSets.push({ ...s, count: qs.length, mcq_count: mcq, multi_count: multi, essay_count: essay })
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
  // Prefer toolbar category filter; fallback to global filter
  const catId = overviewCategoryId.value != null ? overviewCategoryId.value : selectedCategoryId.value
  if (catId){ arr = arr.filter(s => s.category_id === catId) }
  if (selectedSetId.value){
    arr = arr.filter(s => s.id === selectedSetId.value)
  }
  if (selectedType.value === 'mcq'){
    arr = arr.filter(s => (s.mcq_count || 0) > 0)
  } else if (selectedType.value === 'multi'){
    arr = arr.filter(s => (s.multi_count || 0) > 0)
  } else if (selectedType.value === 'essay'){
    arr = arr.filter(s => (s.essay_count || 0) > 0)
  }
  // text search (title/category)
  const q = (overviewSearch.value || '').toLowerCase().trim()
  if (q){
    arr = arr.filter(s => String(s.title||'').toLowerCase().includes(q) || String(categoryName(s.category_id)||'').toLowerCase().includes(q))
  }
  // sorting
  const sort = overviewSort.value
  const keyDate = (s) => {
    const t = s.created_at ? new Date(s.created_at).getTime() : 0
    const id = (typeof s.id === 'number') ? s.id : parseInt(String(s.id||'0'),10) || 0
    return t || id
  }
  const by = {
    newest: (a,b) => keyDate(b) - keyDate(a),
    oldest: (a,b) => keyDate(a) - keyDate(b),
    title_asc:  (a,b) => String(a.title||'').localeCompare(String(b.title||'')),
    title_desc: (a,b) => String(b.title||'').localeCompare(String(a.title||'')),
    count_asc:  (a,b) => (a.count||0) - (b.count||0),
    count_desc: (a,b) => (b.count||0) - (a.count||0),
  }[sort] || ((a,b)=>0)
  return [...arr].sort(by)
})

const displayedSets = computed(() => filteredSetsOverview.value)

async function removeSetOverview(id){
  try {
    // optional confirm to avoid accidental deletes
    if (window.confirm('Delete this set permanently?')){
      await api.delete(`/sets/${id}`)
      await refreshSetsOverview()
    }
  } catch (e) {
    console.error(e)
    alert(e?.response?.data?.detail || e.message || 'Delete failed')
  }
}
// Builder helpers
function addBuilderQuestion(type='mcq'){
  if (type === 'essay'){
    builder.value.questions.push({
      type:'essay',
      question_text:'', question_img:'',
      options:[], correct_idx:null,
      explanation:'', is_featured:false, difficulty_level:'medium'
    })
  } else if (type === 'multi'){
    builder.value.questions.push({
      type:'multi',
      question_text:'', question_img:'',
      options:[ { text:'', img:'' }, { text:'', img:'' }, { text:'', img:'' } ],
      correct_idxs: [],
      explanation:'', is_featured:false, difficulty_level:'medium'
    })
  } else {
    builder.value.questions.push({
      type:'mcq',
      question_text:'', question_img:'',
      options:[ { text:'', img:'' }, { text:'', img:'' }, { text:'', img:'' } ],
      correct_idx: 0,
      explanation:'', is_featured:false, difficulty_level:'medium'
    })
  }
}
function toggleMultiCorrect(q, idx, ev){
  const set = new Set(q.correct_idxs || [])
  if (ev.target.checked) set.add(idx); else set.delete(idx)
  q.correct_idxs = Array.from(set).sort((a,b)=>a-b)
}
function removeBuilderQuestion(i){ builder.value.questions.splice(i,1) }
function addOption(q){ if (q.options.length < 5) q.options.push({ text:'', img:'' }) }
function removeOption(q, idx){ if (q.options.length > 1){ q.options.splice(idx,1); if (q.correct_idx >= q.options.length) q.correct_idx = Math.max(0, q.options.length-1) } }
function letter(i){ return String.fromCharCode('A'.charCodeAt(0) + i) }
const canSaveSet = computed(() => {
  const b = builder.value
  if (!b.category_id || !b.title || b.questions.length === 0) return false
  // allow either text or image for question/options
  return b.questions.every(q => {
    const hasStem = ((q.question_text && q.question_text.trim()) || (q.question_img && q.question_img.trim()))
    if (!hasStem) return false
    if ((q.type||'mcq') === 'essay'){
      return true
    }
    if (!Array.isArray(q.options) || q.options.length < 1 || q.options.length > 5) return false
    const allOptsOk = q.options.every(op => (op.text && op.text.trim()) || (op.img && op.img.trim()))
    if (!allOptsOk) return false
    if (q.type==='mcq'){
      if (q.correct_idx == null || q.correct_idx < 0 || q.correct_idx >= q.options.length) return false
    } else if (q.type==='multi'){
      if (!Array.isArray(q.correct_idxs) || q.correct_idxs.length < 1) return false
      if (q.correct_idxs.some(ci => ci<0 || ci>=q.options.length)) return false
    }
    return true
  })
})
const builderIssues = computed(() => {
  const issues = []
  const b = builder.value
  if (!b.category_id) issues.push('Select a category')
  if (!b.title) issues.push('Set title is required')
  if (b.questions.length === 0) issues.push('Add at least one question')
  b.questions.forEach((q, idx) => {
    const stemOk = ((q.question_text && q.question_text.trim()) || (q.question_img && q.question_img.trim()))
    if (!stemOk) issues.push(`Q${idx+1}: question text or image is required`)
    const type = q.type || 'mcq'
    if (type === 'mcq'){
      if (!Array.isArray(q.options) || q.options.length < 1 || q.options.length > 5){
        issues.push(`Q${idx+1}: number of options must be between 1 and 5`)
      } else {
        q.options.forEach((op, oi) => {
          if (!((op.text && op.text.trim()) || (op.img && op.img.trim()))){
            issues.push(`Q${idx+1} option ${letter(oi)}: text or image is required`)
          }
        })
      }
      if (q.correct_idx == null || q.correct_idx < 0 || q.correct_idx >= (q.options?.length||0)){
        issues.push(`Q${idx+1}: select a correct answer`)
      }
    } else if (type === 'multi'){
      if (!Array.isArray(q.options) || q.options.length < 1 || q.options.length > 5){
        issues.push(`Q${idx+1}: number of options must be between 1 and 5`)
      } else {
        q.options.forEach((op, oi) => {
          if (!((op.text && op.text.trim()) || (op.img && op.img.trim()))){
            issues.push(`Q${idx+1} option ${letter(oi)}: text or image is required`)
          }
        })
      }
      if (!Array.isArray(q.correct_idxs) || q.correct_idxs.length < 1){
        issues.push(`Q${idx+1}: select at least one correct answer`)
      }
    }
  })
  return issues
})
function onSaveClicked(){
  if (builderIssues.value.length>0) return
  saveSetWithQuestions()
}
async function saveSetWithQuestions(){
  const payload = {
    category_id: Number(builder.value.category_id),
    title: builder.value.title,
    description: builder.value.description,
    time_limit_minutes: builder.value.time_limit_minutes,
    is_active: true,
    questions: builder.value.questions.map(q => {
      const base = {
        question_text: toRich(q.question_text, q.question_img),
        explanation: q.explanation,
        is_featured: q.is_featured,
        difficulty_level: q.difficulty_level,
        question_type: q.type || 'mcq',
      }
      if ((q.type||'mcq') === 'essay'){
        return { ...base, option_a:'', option_b:'', option_c:'', option_d:'', option_e:'', correct_answer:'' }
      }
      const texts = (q.options || []).map(op => toRich(op.text, op.img))
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
    })
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

// Manual upload helper removed (replaced by CdnUploader)

function guessTypeFromOptions(q){
  const optTexts = [q.option_a, q.option_b, q.option_c, q.option_d, q.option_e]
  const anyOpt = optTexts.some(v => {
    const pr = (typeof v === 'string' && v.trim().startsWith('{')) ? JSON.parse(v || '{}') : v
    if (typeof pr === 'object' && pr){ return (pr.text && String(pr.text).trim()) || (pr.img && String(pr.img).trim()) }
    return String(v || '').trim() !== ''
  })
  // Without explicit type, we cannot detect multi reliably; default to 'mcq' if options exist
  return anyOpt ? 'mcq' : 'essay'
}

// ----- Import-from-Excel actions (Create New Set) -----
function onFileChangeNew(e){
  xlsxFileNew.value = e.target.files?.[0] || null
}

async function ensureDraftSet(){
  if (createdSetId.value) return createdSetId.value
  if (!builder.value.category_id){
    throw new Error('Please select a Category before preview/import')
  }
  const title = (builder.value.title && builder.value.title.trim()) ? builder.value.title.trim() : `Untitled ${new Date().toLocaleString()}`
  const payload = {
    category_id: Number(builder.value.category_id),
    title,
    description: builder.value.description || '',
    time_limit_minutes: builder.value.time_limit_minutes || 60,
    is_active: true,
    access_level: 'free',
  }
  const { data } = await api.post('/sets/', payload)
  createdSetId.value = data.id
  return createdSetId.value
}

async function doPreviewNew(){
  if (!xlsxFileNew.value) return
  try {
    importErrorNew.value = ''
    const setId = await ensureDraftSet()
    const fd = new FormData()
    fd.append('file', xlsxFileNew.value)
    const { data } = await api.post(`/sets/${setId}/import-xlsx/preview`, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    previewRowsNew.value = data.rows || []
    previewOpenNew.value = true
  } catch (e) {
    previewRowsNew.value = []
    previewOpenNew.value = true
    importErrorNew.value = e?.response?.data?.detail || e.message || 'Preview failed'
  }
}

async function doImportNew(){
  if (!xlsxFileNew.value) return
  importingNew.value = true
  try {
    importErrorNew.value = ''
    const setId = await ensureDraftSet()
    const fd = new FormData()
    fd.append('file', xlsxFileNew.value)
    await api.post(`/sets/${setId}/import-xlsx`, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    router.push({ path: `/admin/sets/${setId}` })
  } catch (e) {
    importErrorNew.value = e?.response?.data?.detail || e.message || 'Import failed'
  } finally {
    importingNew.value = false
  }
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
.opt-item { background:#fff; border:1px solid #e2e8f0; border-radius:10px; padding:8px; display:flex; flex-direction:column; gap:6px; }
.opt-head { display:flex; justify-content:space-between; align-items:center; }
.badge { display:inline-flex; width:22px; height:22px; border-radius:999px; align-items:center; justify-content:center; font-weight:700; background:#f1f5f9; color:#0f172a; }
.opt-actions { display:flex; gap:8px; align-items:center; margin-bottom:8px; }
.btn.tiny { padding:4px 8px; font-size:12px; }
.builder-actions { display:flex; gap:8px; }
.issues{ margin-top:8px; padding:8px; border:1px solid #fee2e2; background:#fef2f2; border-radius:8px; color:#7f1d1d; }
.issues .issue-title{ font-weight:700; margin-bottom:4px; }
.sets-wrap { margin-top:24px; }
.sets-toolbar{ display:flex; gap:8px; align-items:center; margin:8px 0; }
.sets-table{ width:100%; border-collapse:separate; border-spacing:0; }
.sets-table thead th{ position:sticky; top:0; background:#fff; border-bottom:2px solid #e2e8f0; text-align:left; padding:8px 10px; }
.sets-table td{ border-bottom:1px solid #e2e8f0; padding:8px 10px; vertical-align:top; }
.tag{ display:inline-block; margin-right:8px; padding:2px 8px; background:#eef2ff; border-radius:999px; font-size:12px; color:#3730a3; }
.image-row { display:flex; gap:8px; align-items:center; }
</style>
