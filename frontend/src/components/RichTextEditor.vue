<template>
  <div class="rte">
    <div class="rte-toolbar">
      <button type="button" @click="cmd('undo')" title="Undo">↶</button>
      <button type="button" @click="cmd('redo')" title="Redo">↷</button>
      <span class="sep"></span>
      <button type="button" @click="cmd('bold')" title="Bold"><b>B</b></button>
      <button type="button" @click="cmd('italic')" title="Italic"><i>I</i></button>
      <button type="button" @click="cmd('underline')" title="Underline"><u>U</u></button>
      <button type="button" @click="cmd('strikeThrough')" title="Strikethrough"><s>S</s></button>
      <button type="button" @click="sup" title="Superscript">x⁺</button>
      <button type="button" @click="sub" title="Subscript">x₋</button>
      <span class="sep"></span>
      <select class="head" @change="e=>wrap(e.target.value)">
        <option value="p">P</option>
        <option value="h1">H1</option>
        <option value="h2">H2</option>
        <option value="h3" selected>H3</option>
        <option value="h4">H4</option>
      </select>
      <button type="button" @click="wrap('blockquote')" title="Quote">❝ ❞</button>
      <span class="sep"></span>
      <button type="button" @click="cmd('justifyLeft')" title="Align left">⟸</button>
      <button type="button" @click="cmd('justifyCenter')" title="Align center">≡</button>
      <button type="button" @click="cmd('justifyRight')" title="Align right">⟹</button>
      <span class="sep"></span>
      <button type="button" @click="cmd('insertUnorderedList')" title="Bulleted list">• List</button>
      <button type="button" @click="cmd('insertOrderedList')" title="Numbered list">1. List</button>
      <span class="sep"></span>
      <button type="button" @click="inlineCode" title="Inline code">{ }</button>
      <button type="button" @click="blockCode" title="Code block">&lt;/&gt;</button>
      <button type="button" @click="insertInlineMath" title="Inline math">∑x</button>
      <button type="button" @click="insertBlockMath" title="Block math">∑</button>
      <div class="math-helper">
        <button type="button" @click="toggleMathMenu" title="Math helper">𝑓(x) ▾</button>
        <div v-if="showMath" class="math-menu" @mousedown.prevent>
          <div class="group">
            <div class="head">Inline</div>
            <div class="grid">
              <button type="button" @click="ins('$a^2+b^2=c^2$')">a^2+b^2=c^2</button>
              <button type="button" @click="ins('$\\frac{a}{b}$')">fraction</button>
              <button type="button" @click="ins('$\\sqrt{x}$')">sqrt</button>
              <button type="button" @click="ins('$\\alpha,\\beta,\\theta$')">α β θ</button>
              <button type="button" @click="ins('$\\pi$')">π</button>
              <button type="button" @click="ins('$\\leq, \\geq, \\approx$')">≤ ≥ ≈</button>
              <button type="button" @click="ins('$x_1, x_2$')">subscript</button>
              <button type="button" @click="ins('$a\\cdot b$')">· (cdot)</button>
            </div>
          </div>
          <div class="group">
            <div class="head">Block</div>
            <div class="grid">
              <button type="button" @click="insBlock('\\int_0^1 x^2 \\, dx')">integral</button>
              <button type="button" @click="insBlock('\\sum_{i=1}^n i')">summation</button>
              <button type="button" @click="insBlock('\\frac{a+b}{c+d}')">fraction</button>
              <button type="button" @click="insBlock('\\begin{bmatrix}1 & 2\\\\3 & 4\\end{bmatrix}')">matrix</button>
            </div>
          </div>
          <div class="tips">Tips: Use $...$ for inline, $$...$$ for block. Use \\ for commands, ^ for superscript, _ for subscript.</div>
        </div>
      </div>
      <button type="button" @click="insertHr" title="Horizontal rule">―</button>
      <span class="sep"></span>
      <button type="button" @click="makeLink" title="Link">🔗</button>
      <button type="button" @click="insertImageUrl" title="Insert image by URL">🖼️</button>
      <label class="btn small" v-if="uploadEnabled">Upload<input type="file" accept="image/*" @change="onUpload" style="display:none" /></label>
      <span class="sep"></span>
      <button type="button" @click="clearFormat" title="Clear formatting">Tx</button>
    </div>
    <div class="rte-editor" ref="ed" contenteditable="true" :placeholder="placeholder" @input="onInput" @paste="onPaste"></div>
  </div>
  
</template>
<script setup>
import { ref, watch, onMounted } from 'vue'
import api from '../api/client'
const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: '' },
  uploadEnabled: { type: Boolean, default: true },
  uploadEndpoint: { type: String, default: '/files/upload' }
})
const emit = defineEmits(['update:modelValue'])
const ed = ref(null)
const showMath = ref(false)

const ALLOWED_TAGS = new Set(['P','B','I','U','S','STRONG','EM','UL','OL','LI','H1','H2','H3','H4','BLOCKQUOTE','A','IMG','CODE','PRE','SUB','SUP','HR','BR','DIV','SPAN'])
const ALLOWED_ATTR = new Set(['href','src','alt','target','rel','style'])

function sanitize(html){
  const div = document.createElement('div')
  div.innerHTML = html || ''
  ;[...div.querySelectorAll('script,style')].forEach(n => n.remove())
  ;(function clean(node){
    [...node.children].forEach(ch => {
      if (!ALLOWED_TAGS.has(ch.tagName)) { ch.replaceWith(...ch.childNodes); return }
      [...ch.attributes].forEach(attr => { if (!ALLOWED_ATTR.has(attr.name) || attr.name.startsWith('on')) ch.removeAttribute(attr.name) })
      clean(ch)
    })
  })(div)
  return div.innerHTML
}

onMounted(() => {
  if (ed.value) ed.value.innerHTML = props.modelValue || ''
})
watch(() => props.modelValue, (v) => {
  if (!ed.value) return
  if (sanitize(ed.value.innerHTML) !== sanitize(v || '')) ed.value.innerHTML = v || ''
})

function onInput(){ emit('update:modelValue', sanitize(ed.value.innerHTML)) }
function onPaste(e){
  e.preventDefault()
  const text = (e.clipboardData || window.clipboardData).getData('text')
  document.execCommand('insertText', false, text)
}
function cmd(name){ document.execCommand(name, false, null); onInput() }
function clearFormat(){ document.execCommand('removeFormat', false, null); onInput() }
function wrap(tag){ document.execCommand('formatBlock', false, tag); onInput() }
function makeLink(){
  const url = prompt('Enter URL:')
  if (url) { document.execCommand('createLink', false, url); onInput() }
}
function inlineCode(){ document.execCommand('insertHTML', false, `<code>${getSelectionHtml()||'code'}</code>`); onInput() }
function blockCode(){ document.execCommand('insertHTML', false, `<pre><code>${getSelectionHtml()||''}</code></pre>`); onInput() }
function insertHr(){ document.execCommand('insertHorizontalRule', false, null); onInput() }
function sup(){ document.execCommand('superscript'); onInput() }
function sub(){ document.execCommand('subscript'); onInput() }
function insertInlineMath(){
  const sel = getSelectionHtml() || 'a^2+b^2=c^2'
  document.execCommand('insertHTML', false, `$${sel}$`)
  onInput()
}
function insertBlockMath(){
  const sel = getSelectionHtml() || '\\int_0^1 x^2 \\, dx'
  const html = `<pre>$$\n${sel}\n$$</pre>`
  document.execCommand('insertHTML', false, html)
  onInput()
}
function toggleMathMenu(){ showMath.value = !showMath.value }
function ins(snippet){ document.execCommand('insertHTML', false, snippet); onInput(); showMath.value=false }
function insBlock(snippet){ const html = `<pre>$$\n${snippet}\n$$</pre>`; document.execCommand('insertHTML', false, html); onInput(); showMath.value=false }
function insertImageUrl(){
  const url = prompt('Enter image URL:')
  if (url){ document.execCommand('insertImage', false, url); onInput() }
}
async function onUpload(e){
  const file = e.target.files && e.target.files[0]
  if (!file) return
  const fd = new FormData(); fd.append('file', file)
  const { data } = await api.post(props.uploadEndpoint, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
  const u = new URL(data.url)
  const src = u.pathname.startsWith('/uploads/') ? `${window.location.origin.replace('5173','8000')}${u.pathname}` : data.url
  document.execCommand('insertImage', false, src)
  onInput()
  e.target.value = ''
}

function getSelectionHtml(){
  let html = ''
  const sel = window.getSelection()
  if (sel && sel.rangeCount){
    const container = document.createElement('div')
    for (let i=0;i<sel.rangeCount;i++) container.appendChild(sel.getRangeAt(i).cloneContents())
    html = container.innerHTML
  }
  return html
}
</script>
<style scoped>
.rte{ border:1px solid #e2e8f0; border-radius:10px; overflow:hidden; background:white }
.rte-toolbar{ display:flex; gap:6px; align-items:center; padding:6px; background:#f8fafc; border-bottom:1px solid #e2e8f0; flex-wrap:wrap }
.rte-toolbar button, .rte-toolbar .btn.small{ border:1px solid #e2e8f0; background:white; border-radius:8px; padding:4px 8px; font-size:13px; cursor:pointer }
.rte-toolbar .head{ border:1px solid #e2e8f0; background:white; border-radius:8px; padding:4px 6px; font-size:13px }
.rte-toolbar .sep{ width:1px; height:20px; background:#e2e8f0; margin:0 4px }
.rte-editor{ min-height:120px; padding:8px 10px; outline:none; }
.rte-editor:empty:before{ content: attr(placeholder); color:#94a3b8 }
.rte-editor p{ margin: 6px 0 }
.rte-editor img{ max-width:100%; height:auto; border-radius:6px }
</style>
