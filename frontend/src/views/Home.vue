<template>
  <div class="grid" style="gap:24px;">
    <PromoCarousel />
    <section class="card tests-section">
      <div class="home-head">
        <h2 style="margin:0;">Pilihan Test Untukmu</h2>
        <div class="chips">
          <button class="pill" :class="{ active: selectedCategoryId === null }" @click="selectCategory(null)">All Program</button>
          <button v-for="c in categories" :key="c.id" class="pill outline" :class="{ active: selectedCategoryId === c.id }" @click="selectCategory(c.id)">{{ c.name }}</button>
        </div>
        <div class="search-sort">
          <input v-model="homeSearch" class="input search" type="text" placeholder="Cari set..." />
          <select v-model="homeSort" class="input">
            <option value="recent">Terbaru</option>
            <option value="oldest">Terdahulu</option>
            <option value="az">Judul (A-Z)</option>
            <option value="za">Judul (Z-A)</option>
          </select>
        </div>
      </div>

      <div class="grid cols-4 grid-spacious" style="margin-top:18px;">
        <div v-for="item in homeDisplayed" :key="item.set.id" class="set-card">
          <span class="color-dot" :style="{ background: bandColor(item.category.name) }"></span>
          <div class="content flex-1">
            <div class="cat-line">
              <template v-if="brandFor(item.category.id).icon_url">
                <img :src="resolveImg(brandFor(item.category.id).icon_url)" alt="logo" class="badge-img" />
              </template>
              <template v-else>
                <span class="badge-icon" :style="{ background: 'rgba(15,23,42,0.08)' }">{{ brandFor(item.category.id).icon || '🔥' }}</span>
              </template>
              <span class="cat-name" :title="item.category.name">{{ item.category.name }}</span>
            </div>
            <div class="title truncate" :title="item.set.title">{{ item.set.title }}</div>
            <div class="meta">
              <div class="row"><span class="icon">📄</span> <span>Pertanyaan : {{ (questionCount[item.set.id] ?? 0) }} item</span></div>
              <div class="row"><span class="icon">⏱️</span> <span>Durasi: {{ item.set.time_limit_minutes }} Menit</span></div>
            </div>
            <router-link :to="{ name: 'set-overview', params: { setId: item.set.id } }">
              <button class="cta">Simulasi Test</button>
            </router-link>
          </div>
        </div>
      </div>
    </section>
    <!-- FAQ Section -->
    <section id="faq" class="card" style="margin-top:16px;">
      <div class="faq-wrap">
        <div class="faq-left">
          <div class="faq-title">Frequently Asked<br/>Questions</div>
          <div class="faq-sub">Masih bingung atau ragu? Hubungi kami di nomor <strong>+6285234727303</strong></div>
        </div>
        <div class="faq-right">
          <div v-for="(f, idx) in faqs" :key="idx" :class="['faq-item', { open: f.open }]" @click="toggleFaq(idx)">
            <div class="faq-head">
              <span class="faq-num">{{ (idx+1).toString().padStart(2,'0') }}</span>
              <span class="faq-q">{{ f.q }}</span>
              <span class="faq-icon">{{ f.open ? '▾' : '▸' }}</span>
            </div>
            <div class="faq-a" :style="{ maxHeight: faqHeights[idx] + 'px' }"><div class="faq-a-inner" :ref="el => setFaqInnerRef(idx, el)">{{ f.a }}</div></div>
          </div>
        </div>
      </div>
    </section>
    <!-- Testimonials (text-only slider) -->
    <section class="card" style="margin-top:16px;">
      <div class="testi-wrap">
        <div class="testi-head">
          <div class="testi-kicker">TESTIMONIAL</div>
          <div class="testi-title">Apa kata yang sudah bergabung</div>
          <div class="testi-sub">Banyak peserta puas dengan materi yang kami tawarkan</div>
        </div>
        <div class="testi-slider" @mouseenter="pauseAuto()" @mouseleave="resumeAuto()">
          <button class="nav prev" @click="prevTesti">‹</button>
          <div class="viewport">
            <div class="track" :style="{ transform: `translateX(-${testiIndex * 100}%)` }">
              <div v-for="(page, pi) in testiPages" :key="pi" class="slide">
                <div class="tgrid">
                  <div v-for="(t, i) in page" :key="i" class="tcard">
                    <div class="quote">“{{ t.text }}”</div>
                    <div class="author">{{ t.author }}</div>
                    <div class="meta">{{ t.meta }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <button class="nav next" @click="nextTesti">›</button>
        </div>
        <div class="dots">
          <button v-for="(p,i) in testiPages" :key="i" :class="['dot', { active: i===testiIndex }]" @click="goTesti(i)"></button>
        </div>
      </div>
    </section>
  </div>
</template>
<script setup>
import { onMounted, onUnmounted, ref, computed, nextTick } from 'vue'
import PromoCarousel from '../components/PromoCarousel.vue'
import api from '../api/client'

const categories = ref([])
// track measured heights for smooth slide
const faqInnerRefs = ref({})
const faqHeights = ref([])
const testimonials = ref([
  { text: 'Materinya jelas dan ringkas, sangat membantu persiapan.', author: 'dr. Anisa', meta: 'Member sejak 2022' },
  { text: 'Soal-soalnya up to date, mirip dengan ujian asli.', author: 'Rizky P.', meta: 'Calon Koas' },
  { text: 'Platformnya enak dipakai, progress terlihat jelas.', author: 'drg. Lintang', meta: 'Member sejak 2021' },
  { text: 'Pembahasan tiap soal membuat saya paham konsep.', author: 'Fadhil', meta: 'Mahasiswa Kedokteran' },
])
const testiIndex = ref(0)
let testiTimer = null
const testiPerPage = ref(3)
const testiPages = computed(() => {
  const out = []
  const size = Math.max(1, testiPerPage.value)
  for (let i = 0; i < testimonials.value.length; i += size){
    out.push(testimonials.value.slice(i, i + size))
  }
  return out
})
const setsByCategory = ref({})
const questionCount = ref({})
const selectedCategoryId = ref(null)
const gridItems = ref([])
const branding = ref({})
const homeSearch = ref('')
const homeSort = ref('recent')
const searchQuery = ref('')
const sortMode = ref('recent') // recent, oldest, az, za
const selectedCategoryIds = ref([])
const sidebarCategoryQuery = ref('')
const faqs = ref([
  { q: 'Apa itu MedExam?', a: 'MedExam adalah sebuah platform persiapan ujian online yang didedikasikan untuk membantu mahasiswa kedokteran, calon dokter, dan tenaga medis dalam mempersiapkan diri menghadapi berbagai ujian kompetensi. Kami menyediakan ribuan soal latihan berkualitas dan simulasi ujian yang realistis.', open:false },
  { q: 'Siapa saja yang cocok menggunakan platform ini?', a: 'Mahasiswa kedokteran, calon dokter, dan tenaga medis yang ingin mempersiapkan diri menghadapi berbagai ujian kompetensi.', open:false },
  { q: 'Apakah semua soal dan simulasi di MedExam gratis?', a: 'Kami berkomitmen untuk menyediakan akses latihan soal secara gratis untuk membantu sebanyak mungkin pengguna. Ke depannya, kami mungkin akan menyediakan paket premium dengan fitur eksklusif seperti analisis performa mendalam, materi pembelajaran interaktif, dan bank soal yang lebih ekstensif.', open:false },
  { q: 'Dari mana sumber soal-soal di MedExam?', a: 'Soal-soal kami disusun oleh tim ahli yang berpengalaman di bidangnya dan disesuaikan dengan blueprint serta kisi-kisi dari setiap ujian. Kami selalu berusaha memastikan soal yang disajikan relevan dan berkualitas.', open:false },
  { q: 'Apakah ada pembahasan setelah saya menyelesaikan tes?', a: 'Tentu. Setelah menyelesaikan satu sesi simulasi tes, Anda akan mendapatkan laporan hasil yang mencakup skor akhir serta pembahasan kunci jawaban untuk setiap soal. Ini akan membantu Anda memahami konsep dan belajar dari kesalahan.', open:false },
])

onMounted(async () => {
  const { data: cats } = await api.get('/categories/')
  categories.value = cats
  // load branding
  try { branding.value = JSON.parse(localStorage.getItem('category_branding')||'{}') } catch { branding.value = {} }
  // for each category, fetch sets and count questions per set
  await Promise.all(cats.map(async (c) => {
    const { data: sets } = await api.get('/sets/', { params: { category_id: c.id } })
    setsByCategory.value[c.id] = sets
    await Promise.all(sets.map(async (s) => {
      const { data: qs } = await api.get('/questions/', { params: { question_set_id: s.id } })
      questionCount.value[s.id] = qs.length
    }))
  }))
  rebuildGrid()
})

function selectCategory(id){
  selectedCategoryId.value = id
  rebuildGrid()
}

function brandFor(catId){
  return branding.value[String(catId)] || { icon: '', icon_url: '' }
}
function resolveImg(src){
  if (!src) return ''
  const s = String(src)
  if (/^https?:\/\//i.test(s) || s.startsWith('data:image')) return s
  const path = s.startsWith('/') ? s : `/${s}`
  if (path.startsWith('/uploads/')){
    return `${window.location.origin.replace('5173','8000')}${path}`
  }
  return path
}

function rebuildGrid(){
  const items = []
  const catList = selectedCategoryId.value === null
    ? categories.value
    : categories.value.filter(c => c.id === selectedCategoryId.value)
  catList.forEach(c => {
    (setsByCategory.value[c.id] || []).forEach(s => {
      items.push({ category: c, set: s })
    })
  })
  gridItems.value = items
}

const homeDisplayed = computed(() => {
  let arr = gridItems.value
  const q = homeSearch.value.toLowerCase().trim()
  if (q){ arr = arr.filter(it => String(it.set.title||'').toLowerCase().includes(q)) }
  const byTitleAsc = (a,b) => String(a.set.title||'').localeCompare(String(b.set.title||''))
  const byIdAsc = (a,b) => Number(a.set.id) - Number(b.set.id)
  switch (homeSort.value){
    case 'az': arr = [...arr].sort(byTitleAsc); break
    case 'za': arr = [...arr].sort((a,b)=>byTitleAsc(b,a)); break
    case 'oldest': arr = [...arr].sort(byIdAsc); break
    case 'recent': default: arr = [...arr].sort((a,b)=>byIdAsc(b,a)); break
  }
  return arr.slice(0, 12)
})

const displayedItems = computed(() => {
  const q = searchQuery.value.toLowerCase().trim()
  // base list
  let items = gridItems.value
  // sidebar multi-category filter (if any selected)
  if (selectedCategoryIds.value.length > 0){
    const setCat = new Set(selectedCategoryIds.value.map(Number))
    items = items.filter(it => setCat.has(it.category.id))
  }
  // quick chip filter (selectedCategoryId) still applies if set
  if (selectedCategoryId.value !== null){
    items = items.filter(it => it.category.id === selectedCategoryId.value)
  }
  // search
  if (q){
    items = items.filter(it => String(it.set.title||'').toLowerCase().includes(q))
  }
  // sort
  const byTitleAsc = (a,b) => String(a.set.title||'').localeCompare(String(b.set.title||''))
  const byIdAsc = (a,b) => Number(a.set.id) - Number(b.set.id)
  switch (sortMode.value){
    case 'az': items = [...items].sort(byTitleAsc); break
    case 'za': items = [...items].sort((a,b)=>byTitleAsc(b,a)); break
    case 'oldest': items = [...items].sort(byIdAsc); break
    case 'recent': default: items = [...items].sort((a,b)=>byIdAsc(b,a)); break
  }
  return items
})

const filteredSidebarCategories = computed(() => {
  const q = sidebarCategoryQuery.value.toLowerCase().trim()
  if (!q) return categories.value
  return categories.value.filter(c => String(c.name||'').toLowerCase().includes(q))
})

function bandColor(name){
  // Strong distinct colors for common categories
  const map = {
    'Anatomy': '#ef4444',       // red
    'Physiology': '#10b981',    // green
    'Pharmacology': '#8b5cf6',  // violet
    'Pathology': '#f59e0b',     // amber
    'Biochemistry': '#0ea5e9',  // sky
    'Microbiology': '#14b8a6',  // teal
    'Neurology': '#f43f5e',     // rose
    'Radiology': '#6366f1',     // indigo
    'Surgery': '#22c55e',       // emerald
    'Pediatrics': '#f97316',    // orange
    'Psychiatry': '#06b6d4',    // cyan
    'Obstetrics': '#a3e635',    // lime
  }
  if (map[name]) return map[name]
  // Fallback: deterministic palette with wide hue spacing
  const palette = ['#ef4444','#10b981','#8b5cf6','#f59e0b','#0ea5e9','#14b8a6','#f43f5e','#6366f1','#22c55e','#f97316']
  let hash = 0
  const s = String(name || '')
  for (let i = 0; i < s.length; i++) { hash = ((hash << 5) - hash) + s.charCodeAt(i); hash |= 0 }
  const idx = Math.abs(hash * 1315423911) % palette.length
  return palette[idx]
}

function luminance(hex){
  const c = hex.replace('#','')
  const r = parseInt(c.substring(0,2),16)/255
  const g = parseInt(c.substring(2,4),16)/255
  const b = parseInt(c.substring(4,6),16)/255
  const srgb = [r,g,b].map(v => v <= 0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4))
  return 0.2126*srgb[0] + 0.7152*srgb[1] + 0.0722*srgb[2]
}
function bandTextColor(name){
  const bg = bandColor(name)
  // Choose white for dark backgrounds and slate for light ones
  return luminance(bg) < 0.5 ? '#ffffff' : '#0f172a'
}
function badgeBg(name){
  return bandTextColor(name) === '#ffffff' ? 'rgba(255,255,255,0.24)' : 'rgba(15,23,42,0.12)'
}

function toggleFaq(i){
  faqs.value = faqs.value.map((f, idx) => ({ ...f, open: idx === i ? !f.open : false }))
  nextTick(() => measureFaqHeights())
}

function pageCount(){ return Math.max(1, testiPages.value.length) }
function nextTesti(){ const n = pageCount(); testiIndex.value = (testiIndex.value + 1) % n }
function prevTesti(){ const n = pageCount(); testiIndex.value = (testiIndex.value - 1 + n) % n }
function goTesti(i){ const n = pageCount(); testiIndex.value = Math.min(Math.max(0, i), n - 1) }
function startAuto(){
  stopAuto()
  if (pageCount() <= 1) return
  testiTimer = setInterval(() => nextTesti(), 4000)
}
function stopAuto(){ if (testiTimer) { clearInterval(testiTimer); testiTimer = null } }
function pauseAuto(){ stopAuto() }
function resumeAuto(){ startAuto() }

function updatePerPage(){
  testiPerPage.value = window.innerWidth < 900 ? 1 : 3
  // ensure current index is valid after per-page change
  const n = pageCount()
  if (testiIndex.value >= n) testiIndex.value = n - 1
}
function setFaqInnerRef(idx, el){ if (el) faqInnerRefs.value[idx] = el }
function measureFaqHeights(){
  faqHeights.value = faqs.value.map((f, idx) => {
    const el = faqInnerRefs.value[idx]
    if (!el) return 0
    return f.open ? el.scrollHeight + 12 : 0
  })
}
onMounted(() => {
  updatePerPage();
  window.addEventListener('resize', updatePerPage);
  startAuto();
  nextTick(() => {
    measureFaqHeights()
    const n = pageCount();
    if (testiIndex.value >= n) testiIndex.value = n - 1
  })
})
onUnmounted(() => { window.removeEventListener('resize', updatePerPage); stopAuto() })
</script>

<style scoped>
/* Header controls layout */
.home-head{ display:flex; align-items:center; gap:12px; flex-wrap:wrap; }
.home-head .chips{ display:flex; gap:8px; flex-wrap:wrap; }
.home-head .search-sort{ margin-left:auto; display:flex; gap:8px; align-items:center; }
@media (max-width: 640px){
  .home-head h2{ width:100%; }
  .home-head .search-sort{ order:3; width:100%; margin-left:0; }
  .home-head .search-sort .input.search{ width:100%; }
}

/* Page flow: stack sections vertically with consistent spacing */
.grid{ display:block; }
.grid:not(.cols-4) > * + *{ margin-top:16px; }
@media (min-width: 900px){ .grid:not(.cols-4) > * + *{ margin-top:24px; } }
.pill { padding: 8px 14px; border-radius: 999px; border: 1px solid #3b82f6; background:#3b82f6; color:white; font-weight:600; }
.pill.outline { background:white; color:#2563eb; border-color:#2563eb; }
.pill.active { background:#2563eb; color:white; }
@media (max-width: 640px){
  .pill{ padding:6px 10px; font-size:12px; }
  .pill.outline{ font-size:12px; }
}

.set-card { position:relative; background:white; border-radius:14px; box-shadow: 0 4px 10px rgba(2,6,23,0.06), 0 1px 2px rgba(2,6,23,0.04); border:1px solid #e5e7eb; overflow:hidden; display:flex; flex-direction:column; transition: box-shadow .2s ease, transform .2s ease; height:100%; min-height: 230px; margin-bottom: 4px; }
.set-card:hover{ box-shadow: 0 10px 24px rgba(2,6,23,0.10), 0 2px 6px rgba(2,6,23,0.06); }
.color-dot{ position:absolute; right:12px; top:12px; width:10px; height:10px; border-radius:999px; box-shadow: 0 0 0 3px rgba(0,0,0,0.04); }
.cat-line{ display:flex; align-items:center; gap:8px; min-width:0; margin-bottom:6px; color:#0f172a; font-weight:700; }
.cat-name{ display:block; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.badge-img { width:22px; height:22px; object-fit:contain; border-radius:6px; background: rgba(15,23,42,0.06); }
.set-card .content { padding:18px; display:flex; flex-direction:column; gap:12px; flex: 1; min-height: 180px; }
.set-card .title { font-weight:800; color:#0f172a; font-size:18px; line-height:1.35; overflow:hidden; display:-webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 2; word-break: break-word; }
.set-card .meta { color:#334155; display:flex; flex-direction:column; gap:6px; }
.set-card .row { display:flex; align-items:center; gap:8px; }
.set-card .icon { width:18px; text-align:center; }
.set-card .cta { width:100%; background:#2776d6; color:white; border:none; padding:10px 16px; border-radius:10px; font-weight:700; cursor:pointer; }
.set-card .content .cta{ margin-top:auto; }
.badge-icon { display:inline-flex; width:22px; height:22px; align-items:center; justify-content:center; background:rgba(15,23,42,0.06); border-radius:6px; }

/* Grid: 4 columns responsive */
.grid.cols-4{ display:grid; grid-template-columns: repeat(4, 1fr); gap:24px; align-items:stretch; }
.grid.cols-4 > *{ margin-top: 0 !important; }
.grid.grid-spacious{ padding: 4px 2px 12px; }
/* Ensure shadows don't spill outside the rounded section container */
.tests-section{ overflow:hidden; }
@media (max-width: 1200px){ .grid.cols-4{ grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 900px){ .grid.cols-4{ grid-template-columns: repeat(2, 1fr); } }
/* On small screens center cards and limit their width so they don't look like long rectangles */
@media (max-width: 640px){
  .grid.cols-4{ grid-template-columns: 1fr; }
  .grid-spacious .set-card{ margin-bottom:16px; }
  .set-card{ max-width: 100%; width:100%; margin: 0; border-radius:16px; box-shadow: 0 8px 28px rgba(2,6,23,0.08); }
  .color-dot{ right:10px; top:10px; }
  .set-card .content{ padding:14px; gap:10px; min-height: 0; }
  .set-card .title{ font-size:16px; }
  .set-card .meta{ gap:6px; }
  .set-card .cta{ padding:9px 12px; border-radius:8px; }
}

/* Vertical spacing inside cards */
.set-card .meta{ gap:8px; }

/* FAQ */
.faq-wrap{ display:grid; grid-template-columns: 1fr 2fr; gap:18px; align-items:center; }
.faq-left{ display:flex; flex-direction:column; gap:8px; }
.faq-title{ font-weight:800; font-size:26px; line-height:1.35; color:#0f172a; margin-bottom:6px; }
.faq-sub{ color:#475569; line-height:1.8; }
.faq-right{ display:flex; flex-direction:column; gap:12px; }
.faq-item{ border-bottom:1px solid #e2e8f0; padding:14px 0; cursor:pointer; }
.faq-head{ display:grid; grid-template-columns: 40px 1fr 20px; align-items:center; gap:10px; min-height:36px; }
.faq-num{ color:#2563eb; font-weight:800; }
.faq-q{ font-weight:700; color:#0f172a; line-height:1.45; }
.faq-icon{ color:#64748b; text-align:right; }
.faq-a{ color:#475569; padding-left:40px; overflow:hidden; transition:max-height .25s ease; max-height:0; }
.faq-item.open .faq-a{ max-height:400px; }
.faq-a-inner{ padding-top:10px; line-height:1.7; }
@media (max-width: 900px){ .faq-wrap{ grid-template-columns: 1fr; align-items:start; } .faq-a{ padding-left:0; } }

/* Testimonials */
.testi-wrap{ display:flex; flex-direction:column; gap:18px; }
.testi-head{ text-align:center; }
.testi-kicker{ color:#2563eb; letter-spacing:.12em; font-weight:800; font-size:12px; margin-bottom:4px; }
.testi-title{ font-weight:800; font-size:28px; color:#0f172a; line-height:1.3; }
.testi-sub{ color:#475569; margin-top:6px; line-height:1.9; }
.testi-slider{ position:relative; display:flex; align-items:center; gap:12px; padding:6px 0; }
.viewport{ overflow:hidden; width:100%; }
.track{ display:flex; transition: transform .4s ease; }
.slide{ min-width:100%; padding:22px 16px; display:flex; flex-direction:column; align-items:center; gap:12px; }
.tgrid{ display:grid; grid-template-columns: repeat(3, 1fr); gap:12px; width:100%; }
.tcard{ background:#ffffff; border:1px solid #e2e8f0; border-radius:12px; padding:20px; display:flex; flex-direction:column; align-items:center; text-align:center; gap:10px; }
.quote{ color:#0f172a; font-size:18px; text-align:center; max-width:760px; line-height:1.7; }
.author{ font-weight:800; color:#0f172a; }
.meta{ color:#64748b; font-size:14px; }
.nav{ border:1px solid #e2e8f0; background:white; border-radius:50%; width:36px; height:36px; display:flex; align-items:center; justify-content:center; cursor:pointer; }
.dots{ display:flex; gap:6px; justify-content:center; }
.dot{ width:8px; height:8px; border-radius:999px; background:#cbd5e1; border:none; cursor:pointer; }
.dot.active{ background:#2563eb; }
@media (max-width: 900px){ .tgrid{ grid-template-columns: 1fr; } }
</style>
