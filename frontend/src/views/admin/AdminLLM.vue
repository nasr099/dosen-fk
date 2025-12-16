<template>
  <AdminLayout>
    <template #title>Question Generator</template>
    <div class="card" style="padding:12px;">
      <h3 style="margin:0 0 8px;">Generate Questions with (produces .xlsx)</h3>
      <p class="muted">Upload a PDF file. The generator will learn from it and return an Excel matching the import template.</p>

      <form class="form-grid" @submit.prevent="generate">
        <div class="field">
          <label class="label">PDF File</label>
          <input type="file" accept="application/pdf,.pdf" @change="onDocChange" />
        </div>
        <div class="field">
          <label class="label">Total Questions</label>
          <input class="input" type="number" min="1" max="200" v-model.number="count" />
        </div>
        <div class="field span-2">
          <label class="label">Topic (optional)</label>
          <input class="input" v-model="topic" placeholder="e.g. Algebra, Anatomy, History" />
        </div>
        <div class="field">
          <label class="label">Difficulty</label>
          <select class="input" v-model="difficulty">
            <option value="easy">easy</option>
            <option value="medium">medium</option>
            <option value="hard">hard</option>
            <option value="mixed">mixed</option>
          </select>
        </div>
        <div class="field">
          <label class="label">Questions per chunk</label>
          <input class="input" type="number" min="1" max="50" v-model.number="perChunk" />
        </div>
        <div class="field">
          <label class="label">Max pages (PDF)</label>
          <input class="input" type="number" min="1" max="1000" v-model.number="maxPages" />
        </div>
        <div class="actions">
          <button type="submit" class="btn" :disabled="!doc || loading">{{ loading ? 'Generating…' : 'Generate Excel' }}</button>
        </div>
      </form>
      <div v-if="error" class="issues" style="margin-top:8px;">{{ error }}</div>
      <div class="hint" style="margin-top:12px;">
        <strong>Note:</strong> Generator creates only MCQ and MULTI types. Excel headers: type, question_text, question_img, option_a_text, option_a_img, ... option_e_text, option_e_img, correct_answer, explanation, reading_id, reading_title, reading_content.
      </div>
    </div>
  </AdminLayout>
  <div v-if="loading" class="overlay">
    <div class="modal">
      <div class="spinner"></div>
      <div class="msg">Generating questions… This may take a moment for large PDFs.</div>
    </div>
  </div>
</template>
<script setup>
import { ref } from 'vue'
import AdminLayout from '../../components/admin/AdminLayout.vue'
import api from '../../api/client'

const doc = ref(null)
const count = ref(20)
const topic = ref('')
const difficulty = ref('mixed')
const loading = ref(false)
const error = ref('')
const perChunk = ref(10)
const maxPages = ref(30)

function onDocChange(e){ doc.value = e.target.files?.[0] || null }

async function generate(){
  if (!doc.value) return
  loading.value = true
  error.value = ''
  try{
    const fd = new FormData(); fd.append('file', doc.value)
    const params = new URLSearchParams({
      question_count: String(count.value||20),
      topic: topic.value||'',
      difficulty: difficulty.value||'mixed',
      questions_per_chunk: String(perChunk.value||10),
      max_pages: String(maxPages.value||30)
    })
    const { data } = await api.post(`/llm/generate-xlsx?${params.toString()}`, fd, { responseType: 'blob' })
    const blob = new Blob([data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = 'llm_generated_questions.xlsx'
    document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url)
  }catch(e){
    // When using responseType:'blob', FastAPI error responses may come back as a Blob.
    // Decode it so we can show the real error detail.
    try{
      const r = e?.response
      const d = r?.data
      if (d instanceof Blob){
        const txt = await d.text()
        try{
          const j = JSON.parse(txt)
          error.value = j?.detail || txt || 'Failed to generate Excel'
        } catch {
          error.value = txt || 'Failed to generate Excel'
        }
      } else {
        error.value = r?.data?.detail || e.message || 'Failed to generate Excel'
      }
    } catch {
      error.value = e?.response?.data?.detail || e.message || 'Failed to generate Excel'
    }
  }finally{ loading.value = false }
}
</script>
<style scoped>
.overlay{ position:fixed; inset:0; background:rgba(15,23,42,0.45); display:flex; align-items:center; justify-content:center; z-index:9999; }
.modal{ background:#fff; border-radius:10px; padding:20px 24px; min-width:280px; box-shadow:0 10px 30px rgba(0,0,0,0.2); display:flex; align-items:center; gap:14px; }
.spinner{ width:22px; height:22px; border:3px solid #e2e8f0; border-top-color:#2563eb; border-radius:50%; animation:spin 1s linear infinite; }
.msg{ color:#0f172a; font-weight:600; }
@keyframes spin{ from{ transform:rotate(0) } to{ transform:rotate(360deg) } }
.form-grid{ display:grid; grid-template-columns: repeat(2, minmax(220px, 1fr)); gap:12px; align-items:end; }
.field{ display:flex; flex-direction:column; gap:6px; }
.field.span-2{ grid-column: span 2; }
.label{ font-weight:700; color:#0f172a; font-size:13px; }
.actions{ grid-column: span 2; display:flex; justify-content:flex-end; }
.issues{ color:#b91c1c; }
.muted{ color:#64748b }
</style>
