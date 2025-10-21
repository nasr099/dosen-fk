<template>
  <div class="banner" :style="{ height: bannerH }">
    <template v-if="promos.length">
      <div class="slides">
        <div v-for="(p,i) in promos" :key="p.id" class="slide" :class="{ active: i === index }" :style="bgStyle(p.image_url)">
          <div class="overlay">
            <div class="text">
              <div class="title">{{ p.title }}</div>
              <div class="desc">{{ p.description }}</div>
              <a v-if="p.link_url" class="cta" :href="p.link_url" target="_blank">Learn more →</a>
            </div>
          </div>
        </div>
      </div>
      <button class="nav prev" @click="prev">‹</button>
      <button class="nav next" @click="next">›</button>
      <div class="dots">
        <button v-for="(p,i) in promos" :key="p.id" :class="{ dot:true, active: i===index }" @click="go(i)" />
      </div>
    </template>
    <template v-else>
      <div class="fallback">
        <div class="overlay">
          <div class="text">
            <div class="title">Welcome</div>
            <div class="desc">Tambah promo untuk menampilkan banner.</div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
<script setup>
import { onMounted, ref, onBeforeUnmount, onBeforeMount, onUnmounted } from 'vue'
import api from '../api/client'
const promos = ref([])
const index = ref(0)
let timer = null
const bannerH = ref('420px')

function computeHeight(){ bannerH.value = window.innerWidth < 640 ? '180px' : (window.innerWidth >= 1280 ? '480px' : '420px') }

onMounted(async () => {
  const { data } = await api.get('/promos/')
  promos.value = data
  start()
  computeHeight()
  window.addEventListener('resize', computeHeight)
})

onBeforeUnmount(() => { stop(); window.removeEventListener('resize', computeHeight) })

function start(){ stop(); timer = setInterval(next, 5000) }
function stop(){ if (timer) clearInterval(timer) }
function next(){ index.value = (index.value + 1) % (promos.value.length || 1) }
function prev(){ index.value = (index.value - 1 + (promos.value.length || 1)) % (promos.value.length || 1) }
function go(i){ index.value = i; start() }
function bgStyle(url){
  if (!url) return { backgroundImage: 'none' }
  const s = String(url)
  let resolved = s
  // Resolve relative paths to backend origin (port 8000), like resolveImg in Home.vue
  if (!/^https?:\/\//i.test(s) && !s.startsWith('data:image')){
    const path = s.startsWith('/') ? s : `/${s}`
    if (path.startsWith('/uploads/')){
      resolved = `${window.location.origin.replace('5173','8000')}${path}`
    } else {
      resolved = path
    }
  }
  // Ensure special characters are safe in CSS url()
  const safe = encodeURI(resolved)
  return { backgroundImage: `url("${safe}")` }
}
</script>
<style scoped>
.banner { position:relative; border-radius:14px; overflow:hidden; height:420px; background:#0f172a; width:100%; max-width:100%; }
.slides { position:relative; width:100%; height:100%; }
.slide { position:absolute; inset:0; background-size:cover; background-position:center; opacity:0; transition: opacity .5s ease; }
.slide.active { opacity:1; }
.overlay { position:absolute; inset:0; background: linear-gradient(90deg, rgba(0,0,0,.55), rgba(0,0,0,.15) 60%, rgba(0,0,0,0)); display:flex; align-items:center; }
.text { color:white; padding:24px; max-width:60%; display:flex; flex-direction:column; gap:8px; }
.title { font-weight:800; font-size:34px; line-height:1.2; }
.desc { opacity:.95; }
.cta { color:#93c5fd; text-decoration:underline; font-weight:700; }
.fallback{ position:relative; width:100%; height:100%; background:#0f172a; }
.nav { position:absolute; top:50%; transform:translateY(-50%); background:rgba(0,0,0,.45); color:white; border:none; width:36px; height:36px; border-radius:999px; cursor:pointer; display:flex; align-items:center; justify-content:center; }
.nav.prev { left:10px; }
.nav.next { right:10px; }
.dots { position:absolute; bottom:10px; left:0; right:0; display:flex; justify-content:center; gap:6px; }
.dot { width:8px; height:8px; border-radius:999px; background:rgba(255,255,255,.5); border:none; cursor:pointer; }
.dot.active { background:#fff; }

@media (max-width: 640px){
  .banner { height: 180px; border-radius: 0; }
  .text { max-width: 85%; padding:20px; }
  .title { font-size:20px; line-height:1.25; }
}

@media (min-width: 1280px){
  .banner { height: 480px; }
}
</style>
