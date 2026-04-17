<template>
  <footer class="footer-wrap" :class="{ 'is-admin': isAdminRoute }">
    <div class="container footer">
      <div class="col brand">
        <div class="brand-row">
        </div>
        <p class="desc">{{ footer.tagline || 'Practice, learn, and ace your exams. Built for medical students and professionals.' }}</p>
        <ul class="contact">
          <li v-if="footer.address">📍 {{ footer.address }}</li>
          <li v-if="footer.phone">📞 {{ footer.phone }}</li>
          <li v-if="footer.email">✉️ {{ footer.email }}</li>
        </ul>
      </div>
      <div class="col">
        <div class="head">Program</div>
        <template v-if="footer.program && footer.program.length">
          <template v-for="(lnk, i) in footer.program" :key="'p'+i">
            <router-link v-if="isInternal(lnk.url)" :to="lnk.url">{{ lnk.label }}</router-link>
            <a v-else :href="lnk.url" rel="noopener">{{ lnk.label }}</a>
          </template>
        </template>
      </div>
      <div class="col" v-if="footer.product && footer.product.length">
        <div class="head">Product</div>
        <template v-for="(lnk, i) in footer.product" :key="'pd'+i">
          <router-link v-if="isInternal(lnk.url)" :to="lnk.url">{{ lnk.label }}</router-link>
          <a v-else :href="lnk.url" rel="noopener">{{ lnk.label }}</a>
        </template>
      </div>
      <div class="col">
        <div class="head">Support</div>
        <template v-if="footer.support && footer.support.length">
          <template v-for="(lnk, i) in footer.support" :key="'s'+i">
            <router-link v-if="isInternal(lnk.url)" :to="lnk.url">{{ lnk.label }}</router-link>
            <a v-else :href="lnk.url" rel="noopener">{{ lnk.label }}</a>
          </template>
        </template>
        <div class="social">
          <a v-for="(s, i) in footer.socials.filter(x => x.url && x.url !== '#')" :key="'soc'+i" :href="s.url" :aria-label="s.label">{{ s.icon || '🔗' }}</a>
        </div>
      </div>
    </div>
    <div class="foot-note">
      <div class="container note">
        <span>© {{ new Date().getFullYear() }} {{ footer.company || 'MedExam' }}. All rights reserved.</span>
        <span class="ver">{{ footer.version || 'v1.0.0' }}</span>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
const logoSrc = ref('/logo.svg')
const footer = ref({
  company: 'CBT-RU',
  tagline: 'Practice, learn, and ace your exams.',
  address: 'Wonoayu, Sidoarjo, Jawa Timur',
  phone: '+62 896-8131-5028',
  email: 'sekolahroudlotululum@gmail.com',
  version: '2026',
  // Only active links within the site
  program: [
    { label:'Categories', url:'/categories' },
    { label:'Zoom Discussions', url:'/zoom' },
  ],
  product: [],
  support: [
    { label:'FAQ', url:'/#faq' },
    { label:'Team', url:'/team' },
    { label:'Blog', url:'/blog' },
  ],
  socials: [ ],
})
onMounted(() => {
  const l = localStorage.getItem('branding_logo')
  if (l) logoSrc.value = l
  const saved = localStorage.getItem('footer_config')
  if (saved){
    try { footer.value = JSON.parse(saved) } catch {}
  }
})

function isInternal(url){
  return typeof url === 'string' && url.startsWith('/')
}

const route = useRoute()
const isAdminRoute = computed(() => route.path.startsWith('/admin'))
</script>

<style scoped>
.footer-wrap{ background:#fff; color: var(--text); margin-top: 24px; border-top: 1px solid var(--border); }
.footer-wrap.is-admin{ margin-top: 0; }
.footer-wrap.is-admin .footer{ padding-top: 16px; }
.footer-wrap .container{ margin: 0 auto 0 !important; }
.footer{ display:grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 24px; padding: 32px 16px 12px; }
.brand .brand-row{ display:flex; align-items:center; gap:10px; margin-bottom:8px; }
.logo{ height:28px; }
.title{ font-weight:800; letter-spacing:.2px; font-size:16px; color: var(--text); }
.desc{ margin: 8px 0 12px; color: var(--muted); max-width: 420px; font-size:14px; }
.contact{ list-style:none; padding:0; margin:0; color: var(--muted); font-size:14px; }
.contact li{ margin:4px 0; }

.col{ display:flex; flex-direction:column; gap:8px; }
.head{ font-weight:700; color: var(--text); margin-bottom:4px; font-size:14px; }
.col a{ color:#334155; text-decoration:none; font-size:13px; }
.col a:hover{ color:#111827; }

.social{ display:flex; gap:10px; margin-top:8px; }
.social a{ font-size:18px; color:#334155; }

.foot-note{ border-top: 1px solid var(--border); background: #f9fafb; }
.note{ display:flex; align-items:center; justify-content:space-between; padding: 10px 16px 6px; color:#64748b; font-size:12px; }
.ver{ opacity:.9; }

@media (max-width: 900px){
  .footer{ grid-template-columns: 1fr 1fr; }
}
@media (max-width: 600px){
  .footer{ grid-template-columns: 1fr; }
}
</style>
