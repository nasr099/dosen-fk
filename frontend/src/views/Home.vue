<template>
  <!-- Top Banner -->
  <PromoCarousel />

  <!-- Payment How-To Section -->
  <div class="card pay-steps reveal">
    <h2 class="pay-title">Akses Konten Premium dalam 3 Langkah Mudah</h2>
    <div class="pay-row">
      <div class="pay-left">
        <template v-if="premiumImg">
          <img :src="premiumImg" alt="medical team" class="pay-hero" />
        </template>
        <template v-else>
          <!-- lightweight fallback illustration -->
          <svg class="pay-hero-svg" viewBox="0 0 640 360" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <rect width="100%" height="100%" rx="14" fill="#f0f7ff"/>
            <circle cx="120" cy="190" r="52" fill="#1f2937"/>
            <rect x="72" y="240" width="96" height="48" rx="18" fill="#ffffff" stroke="#c7d2fe"/>
            <circle cx="260" cy="190" r="52" fill="#1f2937"/>
            <rect x="212" y="240" width="96" height="48" rx="18" fill="#ffffff" stroke="#c7d2fe"/>
            <circle cx="400" cy="190" r="52" fill="#1f2937"/>
            <rect x="352" y="240" width="96" height="48" rx="18" fill="#ffffff" stroke="#c7d2fe"/>
            <circle cx="540" cy="190" r="52" fill="#1f2937"/>
            <rect x="492" y="240" width="96" height="48" rx="18" fill="#ffffff" stroke="#c7d2fe"/>
          </svg>
        </template>
      </div>
      <div class="pay-right">
        <div class="steps">
          <div
            class="step collapsible"
            :class="{ open: isOpen(1) }"
            @click="toggleStep(1)"
            role="button"
            tabindex="0"
            @keydown.enter.prevent="toggleStep(1)" @keydown.space.prevent="toggleStep(1)"
          >
            <div class="step-toggle header-btn" :aria-expanded="isOpen(1)">
              <div class="step-head">1. Hubungi Admin via WhatsApp</div>
            </div>
            <transition name="expand">
              <div class="step-desc-wrap" v-if="isOpen(1)">
                <div class="step-desc">Klik tombol di bawah dan sampaikan paket yang Anda inginkan.</div>
              </div>
            </transition>
          </div>
          <div
            class="step collapsible"
            :class="{ open: isOpen(2) }"
            @click="toggleStep(2)"
            role="button"
            tabindex="0"
            @keydown.enter.prevent="toggleStep(2)" @keydown.space.prevent="toggleStep(2)"
          >
            <div class="step-toggle header-btn" :aria-expanded="isOpen(2)">
              <div class="step-head">2. Lakukan Pembayaran</div>
            </div>
            <transition name="expand">
              <div class="step-desc-wrap" v-if="isOpen(2)">
                <div class="step-desc">Admin akan mengirimkan link pembayaran Resmi. Selesaikan pembayaran Anda melalui link tersebut.</div>
              </div>
            </transition>
          </div>
          <div
            class="step collapsible"
            :class="{ open: isOpen(3) }"
            @click="toggleStep(3)"
            role="button"
            tabindex="0"
            @keydown.enter.prevent="toggleStep(3)" @keydown.space.prevent="toggleStep(3)"
          >
            <div class="step-toggle header-btn" :aria-expanded="isOpen(3)">
              <div class="step-head">3. Aktivasi Akun</div>
            </div>
            <transition name="expand">
              <div class="step-desc-wrap" v-if="isOpen(3)">
                <div class="step-desc">Admin mengkonfirmasi pembayaran Anda. Akun Anda langsung diaktifkan! Akses konten premium sekarang.</div>
              </div>
            </transition>
          </div>
        </div>
        <div class="pay-cta">
          <a class="btn upgrade" :href="whatsLink" target="_blank" rel="noopener noreferrer">Upgrade Akun</a>
        </div>
      </div>
    </div>
  </div>

  <!-- Featured Tryouts (latest 3) -->
  <section class="card featured-tryouts reveal" v-if="tryoutsLatest.length">
    <div class="ft-head">
      <h2 class="ft-title-lg" style="margin:0;">Latest Tryouts</h2>
      <router-link to="/tryouts"><button class="see-all-btn">See all</button></router-link>
    </div>
    <div class="ft-grid">
      <div class="ft-card" v-for="t in tryoutsLatest" :key="t.id">
        <div class="ft-top">
          <span class="iconbubble">🩺</span>
          <span
            class="cat-badge"
            v-if="t.category"
            :style="{
              color: catColor(t.category),
              background: 'transparent',
              borderColor: catColor(t.category)
            }"
          >{{ t.category }}</span>
        </div>
        <div class="ft-title" :title="t.title">{{ t.title }}</div>
        <div class="ft-meta">
          <span>{{ (t.sets_count||0) }} sets</span>
          <span class="dot">•</span>
          <span>{{ (t.duration_minutes||0) }} mins</span>
        </div>
        <div class="ft-desc line" v-if="descPreview(t)">{{ descPreview(t) }}</div>
        <div class="ft-actions">
          <router-link :to="`/tryout/${t.id}`"><button class="cta">Kerjakan Sekarang</button></router-link>
        </div>
      </div>
    </div>
  </section>

  <!-- Head Categories (cards) -->
  <section class="card head-cards reveal" v-if="headCategories.length">
    <h2 style="margin:0 0 10px;">Categories</h2>
    <div class="grid heads-grid" style="gap:16px;">
      <router-link v-for="h in headCategories" :key="h.id" class="head-card" :to="`/categories?headId=${h.id}`">
        <div class="banner-box">
          <img v-if="h.banner_url || h.cover_url || h.image_url" class="banner" :src="resolveImg(h.banner_url || h.cover_url || h.image_url)" alt="banner" loading="lazy" />
        </div>
        <div class="head-title">{{ h.name }}</div>
        <div class="head-desc">{{ h.description || '—' }}</div>
      </router-link>
    </div>
  </section>
  <!-- Zoom Section -->
  <section class="zoom-section card reveal">
      <div class="zoom-head">
        <h2 style="margin:0;">Zoom Discussion</h2>
      </div>
      <div class="zoom-slider">
        <button class="nav prev" @click="prevZoom">‹</button>
        <div class="viewport">
          <div class="track" :style="{ transform: `translateX(-${zoomIndex * 100}%)` }">
            <div v-for="(page, pi) in zoomPages" :key="pi" class="slide">
              <div class="zgrid" :style="{ '--cols': zoomPerPage }">
                <template v-for="(c, i) in page" :key="i">
                  <div v-if="c.type==='item'" class="zoom-card" @click="$router.push(`/zoom/${c.data.id}`)">
                    <div class="thumb" v-if="c.data.image_url"><img :src="resolveImg(c.data.image_url)" alt="presenter" /></div>
                    <div class="inner">
                      <div class="row top"><span class="chip" :class="c.data.status==='Upcoming' ? 'up' : 'done'">{{ c.data.status }}</span><span class="date-badge">📅 {{ formatLocal(c.data.start_at) }}</span></div>
                      <div
                        class="cat-badge"
                        v-if="c.data.category_id"
                        :style="{
                          background: 'transparent',
                          color: bandColor(categoryName(c.data.category_id)),
                          borderColor: bandColor(categoryName(c.data.category_id))
                        }"
                      >
                        {{ categoryName(c.data.category_id) }}
                      </div>
                      <div class="title" :title="c.data.title">{{ c.data.title }}</div>
                      <div class="presenter">{{ c.data.presenter_name }}</div>
                      <div class="desc" v-if="c.data.description">{{ c.data.description }}</div>
                    </div>
                  </div>
                  <div v-else class="zoom-card see-more">
                    <div class="see-more-inner">
                      <div class="see-title">Lihat lebih banyak diskusi</div>
                      <router-link to="/zoom"><button class="see-all-btn orange">Lihat semua</button></router-link>
                    </div>
                  </div>
                </template>
              </div>
            </div>
          </div>
        </div>
        <button class="nav next" @click="nextZoom">›</button>
      </div>
      <div v-if="zoomCards.length===0" class="empty">Belum ada jadwal.</div>
    </section>
    <section class="card tests-section reveal">
      <div class="home-head">
        <h2 style="margin:0;">Pilihan Test Gratis Untukmu</h2>
        <div class="chips">
          <button v-for="c in headCategories" :key="c.id" class="pill outline" :class="{ active: selectedCategoryId === c.id }" :title="c.name" @click="selectCategory(c.id)"><span class="pill-label">{{ c.name }}</span></button>
        </div>
      </div>

      <div class="program-panel">
      <div class="search-sort">
        <input v-model="homeSearch" class="input search" type="text" placeholder="Cari set..." />
        <select v-model="homeSort" class="input">
          <option value="recent">Terbaru</option>
          <option value="oldest">Terdahulu</option>
          <option value="az">Judul (A-Z)</option>
          <option value="za">Judul (Z-A)</option>
        </select>
      </div>
      <div class="grid cols-4 grid-spacious" style="margin-top:6px;">
        <div v-for="item in homeDisplayed" :key="item.set.id" class="set-card">
          <span class="color-dot" :style="{ background: bandColor(item.category.name) }"></span>
          <span class="plan-badge" :class="(item.set.access_level||'free')==='paid' ? 'paid' : 'free'">
            {{ (item.set.access_level||'free')==='paid' ? 'Paid' : 'Free' }}
          </span>
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
      <div class="see-all-wrap">
        <router-link to="/categories"><button class="see-all-btn orange">Lihat semua</button></router-link>
      </div>
      </div>
    </section>
    <!-- FAQ Section -->
    <section id="faq" class="card reveal" style="margin-top:16px;">
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
    <section class="card reveal" style="margin-top:16px;">
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
</template>
<script setup>
import { onMounted, onUnmounted, ref, computed, nextTick } from 'vue'
import PromoCarousel from '../components/PromoCarousel.vue'
import api from '../api/client'
import { buildWaLink } from '../config/whatsapp'

const whatsLink = buildWaLink('Halo Admin, saya ingin upgrade akun premium.')
// Featured tryouts (latest 3)
const tryoutsLatest = ref([])
const premiumImg = ref('https://medexam-assets-prod.sgp1.cdn.digitaloceanspaces.com/uploads/Gemini_Generated_Image_p2452ep2452ep245.png')
// Steps are always expanded; keep stubs for existing template bindings
const open1 = ref(true)
const open2 = ref(true)
const open3 = ref(true)
function toggleStep(i){ /* no-op: always expanded */ }
function isOpen(i){ return true }
const categories = ref([])
const headCategories = computed(() => categories.value.filter(c => !c.parent_id))
const headHero = computed(() => {
  const h = headCategories.value[0]
  if (!h) return null
  // Try several likely fields for banner image; fallback to empty to use CSS gradient
  const banner = h.banner_url || h.cover_url || h.image_url || ''
  return { title: h.name, banner }
})
// Zoom slider state
const zoomItems = ref([])
const zoomIndex = ref(0)
const zoomPerPage = ref(4) // desktop default
const zoomCards = computed(() => {
  const first10 = (zoomItems.value || []).slice(0, 10)
  const cards = first10.map(z => ({ type: 'item', data: z }))
  return cards.concat([{ type: 'more' }])
})
const zoomPages = computed(() => {
  const per = Math.max(1, zoomPerPage.value)
  const out = []
  for (let i = 0; i < zoomCards.value.length; i += per){ out.push(zoomCards.value.slice(i, i + per)) }
  return out
})
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
  // default to first head category when available
  const firstHead = (cats || []).find(c => !c.parent_id)
  if (firstHead) selectedCategoryId.value = firstHead.id
  // fetch latest active tryouts (non-paginated list includes sets_count & duration_minutes)
  try {
    const { data: ts } = await api.get('/tryouts/', { params: { status: 'active' } })
    const sorted = [...(Array.isArray(ts) ? ts : [])].sort((a,b)=> String(b.created_at||'').localeCompare(String(a.created_at||'')))
    tryoutsLatest.value = sorted.slice(0,4)
  } catch {}
  // load zoom discussions
  try{
    const { data: zoom } = await api.get('/zoom-discussions/')
    // upcoming first (GMT+7 is handled by backend status), then latest
    zoomItems.value = zoom.sort((a,b)=>{
      if (a.status===b.status) return String(b.start_at).localeCompare(String(a.start_at))
      return a.status==='Upcoming' ? -1 : 1
    })
  } catch {}
  // load branding
  try { branding.value = JSON.parse(localStorage.getItem('category_branding')||'{}') } catch { branding.value = {} }
  // Read branding illustration (same key used on Auth page)
  // For each category, fetch exam-available set summaries once (faster) and use 'count'
  await Promise.all(cats.map(async (c) => {
    const { data: sums } = await api.get('/sets/summary', { params: { category_id: c.id, allow_in_exam: 1 } })
    const arr = Array.isArray(sums) ? sums : []
    setsByCategory.value[c.id] = arr
    for (const s of arr){ questionCount.value[s.id] = Number(s.count || 0) }
  }))
  rebuildGrid()
  // after async content lands, prepare reveals again
  nextTick(() => setupReveals())
})

function selectCategory(id){
  selectedCategoryId.value = id
  rebuildGrid()
}

// Shorten long category names on small screens with explicit '...'
function shortName(name){
  const s = String(name || '')
  try{
    if (window && window.innerWidth <= 640){
      const max = 18
      return s.length > max ? (s.slice(0, max-3) + '...') : s
    }
  }catch{}
  return s
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

// Zoom slider controls + time formatter (GMT+7)
function nextZoom(){ if (zoomPages.value.length===0) return; zoomIndex.value = Math.min(zoomIndex.value + 1, zoomPages.value.length - 1) }
function prevZoom(){ if (zoomPages.value.length===0) return; zoomIndex.value = Math.max(zoomIndex.value - 1, 0) }
function formatLocal(s){ try { return new Date(s).toLocaleString('id-ID', { timeZone: 'Asia/Jakarta', dateStyle: 'medium', timeStyle: 'short' }) } catch { return s } }

function updateZoomPerPage(){
  const w = window.innerWidth
  if (w < 900) zoomPerPage.value = 1
  else if (w < 1200) zoomPerPage.value = 2
  else if (w < 1500) zoomPerPage.value = 3
  else zoomPerPage.value = 4
  const maxIndex = Math.max(0, zoomPages.value.length - 1)
  if (zoomIndex.value > maxIndex) zoomIndex.value = maxIndex
}

function categoryName(id){
  const c = (categories.value || []).find(x => x.id === Number(id))
  return c ? c.name : ''
}

function rebuildGrid(){
  // Build from ALL categories (sets belong to sub categories), then filter by selected head if any
  let items = []
  categories.value.forEach(c => {
    (setsByCategory.value[c.id] || []).forEach(s => {
      items.push({ category: c, set: s })
    })
  })
  if (selectedCategoryId.value !== null){
    const headId = selectedCategoryId.value
    items = items.filter(it => it.category.parent_id === headId || it.category.id === headId)
  }
  gridItems.value = items
}

const homeDisplayed = computed(() => {
  // Only FREE sets, latest first, limit 20
  let arr = gridItems.value.filter(it => String(it.set.access_level || 'free') === 'free')
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
  return arr.slice(0, 20)
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

// For category badge on featured tryouts: use neutral slate for 'Uncategorized'
function catColor(name){
  const s = String(name || '').trim().toLowerCase()
  if (s === 'uncategorized' || s === 'uncategorised') return '#94a3b8' // slate-400
  return bandColor(name)
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
// IntersectionObserver for reveal-on-scroll
let revealIO = null
const revealedSet = new Set()
function setupReveals(){
  try{
    const els = Array.from(document.querySelectorAll('.reveal'))
    if (!revealIO){
      revealIO = new IntersectionObserver((entries, obs) => {
        for (const e of entries){
          if (e.isIntersecting){
            e.target.classList.add('in')
            revealedSet.add(e.target)
            obs.unobserve(e.target)
          }
        }
      }, { threshold: 0.12, rootMargin: '0px 0px -5% 0px' })
      window.__homeRevealIO = revealIO
    }
    els.forEach(el => {
      if (!el.classList.contains('prep')) el.classList.add('prep')
      if (!revealedSet.has(el)){
        const r = el.getBoundingClientRect()
        const inView = r.top < (window.innerHeight * 0.88) && r.bottom > 0
        if (inView){ el.classList.add('in'); revealedSet.add(el) }
        else revealIO.observe(el)
      }
    })
  }catch{}
}

onMounted(() => {
  updatePerPage();
  updateZoomPerPage();
  window.addEventListener('resize', updatePerPage);
  window.addEventListener('resize', updateZoomPerPage);
  startAuto();
  nextTick(() => {
    measureFaqHeights()
    const n = pageCount();
    if (testiIndex.value >= n) testiIndex.value = n - 1
    // Setup and observe existing reveals
    setupReveals()
  })
})
onUnmounted(() => {
  window.removeEventListener('resize', updatePerPage);
  window.removeEventListener('resize', updateZoomPerPage);
  stopAuto();
  try{ revealIO && revealIO.disconnect(); window.__homeRevealIO = null }catch{}
})

// helper: shorten and sanitize description for featured tryout card
function shorten(html, maxLen = 140){
  const div = document.createElement('div')
  div.innerHTML = String(html||'')
  ;[...div.querySelectorAll('script,style')].forEach(n=>n.remove())
  const text = div.textContent || div.innerText || ''
  const s = text.trim().replace(/\s+/g,' ')
  return s.length > maxLen ? s.slice(0,maxLen) + '…' : s
}

// render a short rich preview with a fade (keep only basic tags)
function renderPreview(html){
  const ALLOWED_TAGS = new Set(['P','B','I','U','S','STRONG','EM','UL','OL','LI','H1','H2','H3','H4','BLOCKQUOTE','A','IMG','CODE','PRE','SUB','SUP','HR','BR','DIV','SPAN'])
  const ALLOWED_ATTR = new Set(['href','src','alt','target','rel','style'])
  const div = document.createElement('div')
  div.innerHTML = String(html||'')
  ;[...div.querySelectorAll('script,style')].forEach(n=>n.remove())
  ;(function clean(node){
    ;[...node.children].forEach(ch => {
      if (!ALLOWED_TAGS.has(ch.tagName)) { ch.replaceWith(...ch.childNodes); return }
      ;[...ch.attributes].forEach(attr => { if (!ALLOWED_ATTR.has(attr.name) || attr.name.startsWith('on')) ch.removeAttribute(attr.name) })
      clean(ch)
    })
  })(div)
  const text = div.textContent || ''
  if (text.length > 260){
    return `<div class="fade-wrap">${div.innerHTML}</div>`
  }
  return div.innerHTML
}

// compute a one/two-line plain preview, avoid repeating title
function descPreview(t){
  try{
    const title = String(t?.title || '').trim()
    const raw = String(t?.description || '').trim()
    if (!raw) return ''
    const text = shorten(raw, 160)
    if (!text) return ''
    if (text.toLowerCase() === title.toLowerCase()) return ''
    if (text.length < 3) return ''
    return text
  } catch { return '' }
}
</script>

<style scoped>

/* Categories: horizontal cards aligned like CategoryHeads.vue */
.grid.heads-grid { display: grid; }

/* If you want a single column of wide, horizontal cards instead of 3 columns: */
.heads-grid { grid-template-columns: 1fr; }

/* Keep banner aspect and spacing identical */
.banner-box {
  width: 100%;
  aspect-ratio: 16/9;
  background: #f1f5f9;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}
.banner { width: 100%; height: 100%; object-fit: contain; display: block; }

/* Head categories cards (match CategoryHeads.vue) */
.head-cards { margin: 16px 0; }
.heads-grid { grid-template-columns: repeat(3, 1fr); }
@media (max-width: 900px){ .heads-grid{ grid-template-columns: repeat(2,1fr); } }
@media (max-width: 640px){ .heads-grid{ grid-template-columns: 1fr; } }
.head-card {
  cursor: pointer;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 12px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow: hidden;
  text-decoration: none;
  color: inherit;
}
.head-card:hover { box-shadow: 0 8px 22px rgba(0,0,0,0.08); }
.banner-box {
  width: 100%;
  aspect-ratio: 16/9;
  background: #f1f5f9;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}
.banner { width: 100%; height: 100%; object-fit: contain; display: block; }
.head-title { font-weight: 800; color: #0f172a; font-size: 18px; line-height: 1.25; }
.head-desc { color: #64748b; margin-top: 6px; font-size: 14px; }
@media (max-width: 900px) { .heads-grid { grid-template-columns: repeat(2,1fr); } }
@media (max-width: 640px) { .heads-grid { grid-template-columns: 1fr; } }


/* Override grid vertical margins for heads grid */
.heads-grid > * + *{ margin-top: 0 !important; }

/* Zoom section */
.zoom-section{ overflow:hidden; }
.zoom-slider{ position:relative; display:flex; align-items:center; gap:12px; padding:6px 0; }
.zoom-slider .viewport{ overflow:hidden; width:100%; }
.zoom-slider .track{ display:flex; transition: transform .35s ease; }
.zoom-slider .slide{ min-width:100%; padding:14px 8px; }
.zgrid{ display:grid; gap:12px; align-items:stretch; width:100%; grid-template-columns: repeat(var(--cols, 3), 1fr); }
.zoom-card{ background:#fff; border:1px solid #e2e8f0; border-radius:14px; overflow:hidden; box-shadow:0 2px 10px rgba(0,0,0,0.05); width:100%; }
.zoom-card .thumb{ width:100%; height: 120px; background:#f1f5f9; }
.zoom-card .thumb img{ width:100%; height:100%; object-fit:cover; display:block; }
@media (max-width: 900px){ .zoom-card .thumb{ height: 100px; } }
.zoom-card .inner{ padding:10px 12px; display:flex; flex-direction:column; gap:8px; }
.zoom-card .row.top{ display:flex; justify-content:space-between; align-items:center; gap:8px; }
.zoom-card .title{ font-weight:800; color:#0f172a; line-height:1.4; }
.zoom-card .presenter{ font-weight:700; color:#334155; font-size:14px; line-height:1.5; }
.zoom-card .desc{ color:#64748b; font-size:14px; line-height:1.6; overflow:hidden; display:-webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 3; }
.cat-badge{ font-size:12px; display:inline-block; padding:2px 8px; border-radius:999px; border:1px solid #e2e8f0; margin:2px 0 6px; align-self:flex-start; }
.zoom-card.see-more{ display:flex; align-items:center; justify-content:center; }
.see-more-inner{ padding:24px; text-align:center; display:flex; flex-direction:column; gap:10px; }
.see-title{ font-weight:800; color:#0f172a; }
.chip{ font-size:12px; padding:2px 8px; border-radius:999px; border:1px solid #e2e8f0; }
.chip.up{ background:#ecfeff; color:#155e75; border-color:#a5f3fc; }
.chip.done{ background:#f8fafc; color:#334155; }
.date-badge{ font-size:12px; color:#0f172a; background:#fff; border:1px solid #e2e8f0; border-radius:999px; padding:2px 8px; }

/* Header controls layout */

/* Entrance reveal animation (only hide after JS marks as .prep) */
.reveal.prep{ opacity:0; transform: translateY(20px); transition: opacity .9s ease, transform .9s ease; will-change: opacity, transform; }
.reveal.prep.in{ opacity:1; transform: translateY(0); }
.featured-tryouts.reveal.prep{ transform: translateY(28px); }
.featured-tryouts.reveal.prep.in{ transform: translateY(0); }
.zoom-section.reveal.prep{ transform: translateY(24px); }
.tests-section.reveal.prep{ transform: translateY(24px); }
.card.reveal.prep{ transition-delay: .05s; }
.card.reveal.prep.in{ transition-delay: 0s; }
.home-head{ display:flex; align-items:center; gap:12px; flex-wrap:wrap; }
.chips{ display:flex; gap:12px; flex-wrap:wrap; align-items:flex-end; border-bottom:1px solid #e5e7eb; padding-bottom:6px; }

/* Pay steps */
.pay-steps{ margin:18px 0; padding:16px 16px 14px; background:linear-gradient(180deg,#eaf6ff,#f5fbff); border:1px solid #cfe7ff; border-radius:16px; box-shadow: 0 14px 34px rgba(30,64,175,0.08), 0 2px 6px rgba(2,6,23,0.04); }
.pay-title{ margin:0 0 14px; text-align:center; font-weight:900; letter-spacing:.2px; color:#0f172a; }
.pay-title::after{ content:""; display:block; width:180px; height:6px; margin:10px auto 0; border-radius:999px; background:linear-gradient(90deg,#2563eb,#4f46e5); opacity:.25; }
.pay-row{ display:grid; grid-template-columns: 1.2fr 1fr; gap:16px; align-items:center; }
.pay-left{ display:flex; align-items:center; justify-content:center; background: transparent; }
.pay-hero{ width:100%; height:auto; display:block; border-radius:12px; }
.pay-hero-svg{ width:100%; height:auto; display:block; border-radius:12px; }
/* Vertical accordion style */
.steps{ display:grid; grid-template-columns: 1fr; gap:10px; align-items:stretch; }
.step{ position:relative; background: rgba(255,255,255,0.5); border:1px solid rgba(2,6,23,0.10); border-radius:16px; padding:16px 18px; display:flex; flex-direction:column; gap:8px; transition: box-shadow .2s ease, transform .2s ease, border-color .2s ease, background-color .2s ease; box-shadow: 0 6px 16px rgba(2,6,23,0.06); }
.step:hover{ box-shadow: 0 14px 28px rgba(2,6,23,0.12); border-color: rgba(2,6,23,0.18); transform: translateY(-1px); background: rgba(255,255,255,0.6); }
.illo{ display:none; }
.step-head{ font-weight:900; color:#0f172a; padding-right:28px; }
.step-desc{ color:#334155; line-height:1.7; font-size:14px; }
/* collapsible behavior */
.step.collapsible{ cursor:default; user-select:text; }
.step-toggle{ display:flex; align-items:center; justify-content:space-between; gap:8px; width:100%; background:transparent; border:0; padding:0; margin:0; text-align:left; cursor:pointer; }
.step-toggle:focus{ outline:2px solid #93c5fd; outline-offset:2px; border-radius:8px; }
.step-desc-wrap{ overflow:hidden; }
.expand-enter-active, .expand-leave-active{ transition: opacity .2s ease; }
.expand-enter-from, .expand-leave-to{ opacity: 0; }
.expand-enter-to, .expand-leave-from{ opacity: 1; }
/* right-edge arrow indicator at card edge */
.step.collapsible::after{ content: ''; }
.step.collapsible.open::after{ content: ''; }
.pay-cta{ display:flex; justify-content:center; margin-top:12px; }
.btn.upgrade{ background:linear-gradient(90deg,#f97316,#fb923c); color:#fff; border:1px solid #fb923c; padding:12px 18px; border-radius:999px; text-decoration:none; font-weight:900; box-shadow: 0 12px 22px rgba(249,115,22,.25); }
.btn.upgrade:hover{ filter:brightness(.97); }
@media (max-width: 900px){
  .pay-row{ grid-template-columns: 1fr; }
  .steps{ grid-template-columns: 1fr; }
  .illo{ height:96px; }
  .illo svg{ width:96px; height:96px; }
  .steps .step + .step::before{ display:none; }
}
.home-head .chips{ display:flex; gap:8px; flex-wrap:wrap; }
.home-head .search-sort{ margin-left:auto; display:flex; gap:8px; align-items:center; }
.see-all-btn{ background:white; color:#2563eb; border:1px solid #2563eb; padding:8px 12px; border-radius:999px; font-weight:700; cursor:pointer; }
.see-all-btn:hover{ background:#2563eb; color:white; }
.see-all-btn.orange{ background:#f97316; border-color:#f97316; color:white; }
.see-all-btn.orange:hover{ background:#ea580c; border-color:#ea580c; }
.see-all-wrap{ display:flex; justify-content:center; margin-top:10px; }
/* Featured Tryouts */
.featured-tryouts{ margin: 14px 0; background:linear-gradient(180deg,#f8fbff,#ffffff); border:1px solid #e5efff; border-radius:16px; padding:14px; box-shadow: 0 10px 28px rgba(37,99,235,0.06); }
.ft-head{ display:flex; align-items:center; justify-content:space-between; gap:12px; padding:0 4px; }
.ft-title-lg{ font-size:24px; line-height:1.25; font-weight:900; letter-spacing:.2px; }
.ft-grid{ display:grid; grid-template-columns: repeat(4, 1fr); gap:14px; margin-top:12px; }
@media (max-width: 1200px){ .ft-grid{ grid-template-columns: repeat(3,1fr); } }
@media (max-width: 900px){ .ft-grid{ grid-template-columns: repeat(2,1fr); } }
@media (max-width: 640px){ .ft-grid{ grid-template-columns: 1fr; } }
.ft-card{ background:#ffffff; border:1px solid #e2e8f0; border-radius:14px; padding:14px; display:flex; flex-direction:column; gap:10px; box-shadow:0 6px 18px rgba(2,6,23,0.06); transition: box-shadow .2s ease, transform .2s ease; }
.ft-card:hover{ box-shadow:0 16px 32px rgba(2,6,23,0.12); transform: translateY(-2px); }
.ft-top{ display:flex; align-items:center; justify-content:space-between; padding:10px 12px; margin:-14px -14px 10px -14px; background:#fff7ed; border-bottom:1px solid #fed7aa; border-top-left-radius:14px; border-top-right-radius:14px; }
.iconbubble{ width:34px; height:34px; display:inline-flex; align-items:center; justify-content:center; border-radius:10px; background:linear-gradient(135deg,#dbeafe,#bfdbfe); border:1px solid #bfdbfe; box-shadow: inset 0 1px 0 #ffffff; }
.cat-badge{ font-size:12px; padding:4px 10px; border-radius:999px; font-weight:800; background:#f1f5f9; color:#0f172a; border:1px solid #e2e8f0; }
.ft-title{ font-weight:900; color:#0f172a; line-height:1.25; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; letter-spacing:.2px; }
.ft-meta{ color:#475569; font-size:13px; display:flex; align-items:center; gap:10px; }
.ft-meta .badge{ background:#eef2ff; border:1px solid #c7d2fe; padding:3px 8px; border-radius:999px; font-weight:800; font-size:12px; color:#3730a3; }
.ft-meta .dot{ opacity:.5; }
.ft-desc{ color:#64748b; font-size:14px; line-height:1.7; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; overflow:hidden; }
.ft-desc.line{ color:#475569; font-size:14px; line-height:1.6; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
.ft-actions{ margin-top:auto; display:flex; justify-content:flex-end; }
.ft-actions.dual{ gap:8px; justify-content:space-between; }
.ft-actions .cta{ background:linear-gradient(90deg,#f97316,#fb923c); color:#fff; border:1px solid #fb923c; padding:9px 14px; border-radius:12px; font-weight:900; cursor:pointer; box-shadow: 0 12px 22px rgba(249,115,22,.25); }
.ft-actions .cta.ghost{ background:#fff; color:#f97316; border-color:#fb923c; box-shadow:none; }
.ft-actions .cta:hover{ filter:brightness(.97); }
/* rich preview fade */
.ft-desc.rich{ position:relative; max-height: 96px; overflow:hidden; }
.ft-desc.rich .fade-wrap{ position:relative; display:block; }
.ft-desc.rich::after{ content:""; position:absolute; left:0; right:0; bottom:0; height:40px; background: linear-gradient(180deg, rgba(255,255,255,0), #ffffff); }
@media (max-width: 640px){
  .home-head h2{ width:100%; }
  .home-head .search-sort{ order:3; width:100%; margin-left:0; }
  .home-head .search-sort .input.search{ width:100%; }
}

/* Page flow: stack sections vertically with consistent spacing */
.grid{ display:block; }
.grid:not(.cols-4) > * + *{ margin-top:16px; }
@media (min-width: 900px){ .grid:not(.cols-4) > * + *{ margin-top:24px; } }
.pill { display:inline-flex; align-items:center; height:40px; padding: 0 14px; border-radius: 10px 10px 0 0; border: 1.5px solid #2563eb; border-bottom: none; background:transparent; color:#2563eb; font-weight:800; line-height:1; transition: background .15s ease, color .15s ease, box-shadow .15s ease; position:relative; top:0; }
.pill.outline { background:transparent; color:#2563eb; border-color:#2563eb; border-bottom: none; }
.pill:hover{ background: rgba(37,99,235,0.06); }
.pill.active { background:#f6f9ff; color:#0f172a; border-color:#2563eb; border-bottom: none; box-shadow: 0 -1px 0 #f6f9ff, 0 1px 0 rgba(2,6,23,0.02); }
@media (max-width: 640px){
  .pill{ height:auto; padding:6px 10px; font-size:12px; top:0; }
  .pill.outline{ font-size:12px; }
}

/* Mobile: keep folder tabs look with horizontal scroll, prevent wrapping */
@media (max-width: 640px){
  .chips{ flex-wrap: nowrap; overflow-x: auto; gap:8px; padding-bottom:6px; -webkit-overflow-scrolling: touch; scroll-snap-type: x proximity; }
  .chips::-webkit-scrollbar{ display:none; }
  .pill{ scroll-snap-align: start; height:auto; padding:6px 10px; }
  .pill .pill-label{ display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; text-overflow:ellipsis; white-space:normal; max-width: 70vw; line-height:1.2; }
  .program-panel{ padding:10px; border-radius:10px; }
  .program-panel .search-sort{ justify-content:stretch; }
  .program-panel .search-sort .input.search{ flex:1; width:auto; max-width:none; }
  .program-panel .search-sort select.input{ width:auto; }
  /* ensure the instance inside .home-head also no-wrap */
  .home-head .chips{ flex-wrap: nowrap !important; overflow-x:auto; gap:8px; }
}

/* Folder content panel under tabs */
.program-panel{
  background:#f6f9ff;
  border:1px solid #e5e7eb;
  border-radius: 10px;
  margin-top:-1px; /* tuck under tab bottom border */
  padding:12px;
}

/* Search/sort alignment inside panel */
.program-panel .search-sort{ display:flex; gap:8px; justify-content:flex-end; align-items:center; margin-bottom:8px; }
.program-panel .search-sort .input.search{ width: 220px; max-width: 60vw; }
.program-panel .search-sort select.input{ width: 140px; }

.set-card { position:relative; background:white; border-radius:14px; box-shadow: 0 4px 10px rgba(2,6,23,0.06), 0 1px 2px rgba(2,6,23,0.04); border:1px solid #e5e7eb; overflow:hidden; display:flex; flex-direction:column; transition: box-shadow .2s ease, transform .2s ease; height:100%; min-height: 230px; margin-bottom: 4px; }
.set-card:hover{ box-shadow: 0 10px 24px rgba(2,6,23,0.10), 0 2px 6px rgba(2,6,23,0.06); }
.color-dot{ position:absolute; right:12px; top:12px; width:10px; height:10px; border-radius:999px; box-shadow: 0 0 0 3px rgba(0,0,0,0.04); }
.plan-badge{ position:absolute; right:12px; top:12px; font-size:12px; font-weight:800; padding:4px 8px; border-radius:999px; border:1px solid #e2e8f0; background:#f8fafc; color:#0f172a; }
.plan-badge.paid{ background:#fef3c7; color:#92400e; border-color:#fde68a; }
.plan-badge.free{ background:#ecfeff; color:#155e75; border-color:#a5f3fc; }
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
.tests-section{ overflow:hidden; margin-top:16px; }
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
/* Equalize head card heights */
.heads-grid{ align-items:stretch; }
.head-card{ height:100%; }

</style>
/* Fix: ensure heads grid is horizontal despite global .grid rule */
.grid.heads-grid { display: grid; }
