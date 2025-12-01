<template>
  <AdminLayout>
    <template #title>Question Scanner</template>
    <div class="card" style="padding:12px;">
      <h3 style="margin:0 0 8px;">Scan Questions from PDF (produces .xlsx)</h3>
      <p class="muted">Upload a PDF that already contains MCQ/MULTI questions. The scanner will extract the same questions and answers as text and return an Excel matching the import template. Images/tables are ignored.</p>

      <form class="form-grid" @submit.prevent="scan">
        <div class="field">
          <label class="label">PDF File</label>
          <input type="file" accept="application/pdf,.pdf" @change="onDocChange" />
        </div>
        <div class="field">
          <label class="label">Questions per chunk</label>
          <input class="input" type="number" min="1" max="100" v-model.number="perChunk" />
        </div>
        <div class="field">
          <label class="label">Max pages (PDF)</label>
          <input class="input" type="number" min="1" max="2000" v-model.number="maxPages" />
        </div>
        <div class="field">
          <label class="label">Max questions</label>
          <input class="input" type="number" min="1" max="2000" v-model.number="maxQuestions" />
        </div>
        <div class="field">
          <label class="label">Use LLM fallback</label>
          <label class="checkbox-row"><input type="checkbox" v-model="useLLM" /> <span>Enable LLM to fill gaps if deterministic parser misses anything</span></label>
        </div>
        <div class="field">
          <label class="label">LaTeX math</label>
          <label class="checkbox-row"><input type="checkbox" v-model="latexify" /> <span>Convert detected math to LaTeX ($, $$)</span></label>
        </div>
        <div class="actions">
          <button type="submit" class="btn" :disabled="!doc || loading">{{ loading ? 'Scanning…' : 'Generate Excel' }}</button>
        </div>
      </form>
      <div v-if="error" class="issues" style="margin-top:8px;">{{ error }}</div>
      <div class="hint" style="margin-top:12px;">
        <strong>Note:</strong> Scanner extracts only MCQ and MULTI currently. Images/tables are skipped. Output columns follow the import template.
      </div>
    </div>
  </AdminLayout>
  <div v-if="loading" class="overlay">
    <div class="modal">
      <div class="spinner"></div>
      <div class="msg">Scanning PDF… This may take a while for large documents.</div>
    </div>
  </div>
</template>
<script setup>
import { ref } from 'vue'
import AdminLayout from '../../components/admin/AdminLayout.vue'
import api from '../../api/client'

const doc = ref(null)
const loading = ref(false)
const error = ref('')
const perChunk = ref(20)
const maxPages = ref(100)
const maxQuestions = ref(500)
const useLLM = ref(false)
const latexify = ref(true)

function onDocChange(e){ doc.value = e.target.files?.[0] || null }

async function scan(){
  if (!doc.value) return
  loading.value = true
  error.value = ''
  try{
    const fd = new FormData(); fd.append('file', doc.value)
    const params = new URLSearchParams({
      questions_per_chunk: String(perChunk.value||20),
      max_pages: String(maxPages.value||100),
      max_questions: String(maxQuestions.value||500),
      use_llm: String(!!useLLM.value),
      latexify: String(!!latexify.value),
    })
    const { data } = await api.post(`/llm/scan-xlsx?${params.toString()}`, fd, { responseType: 'blob' })
    const blob = new Blob([data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = 'scanned_questions.xlsx'
    document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url)
  }catch(e){
    error.value = e?.response?.data?.detail || e.message || 'Failed to scan PDF'
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
.checkbox-row{ display:flex; align-items:center; gap:8px; font-size:13px; color:#0f172a; }
.label{ font-weight:700; color:#0f172a; font-size:13px; }
.actions{ grid-column: span 2; display:flex; justify-content:flex-end; }
.issues{ color:#b91c1c; }
.muted{ color:#64748b }
</style>
