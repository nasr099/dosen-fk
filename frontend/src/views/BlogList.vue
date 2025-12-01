<template>
  <div class="card">
    <div class="blog-head">
      <h2>Blog</h2>
      <div class="controls">
        <input v-model="q" class="input" placeholder="Search posts..." @input="fetchPosts" />
      </div>
    </div>
    <div class="grid cols-3" style="margin-top:12px;">
      <article v-for="p in posts" :key="p.id" class="post-card">
        <router-link :to="{ name:'blog-detail', params:{ slug: p.slug } }" class="cover" v-if="p.cover_url">
          <img :src="resolveImg(p.cover_url)" :alt="p.title" />
        </router-link>
        <div class="pc-body">
          <router-link :to="{ name:'blog-detail', params:{ slug: p.slug } }" class="pc-title">{{ p.title }}</router-link>
          <div class="pc-excerpt">{{ makeSnippet(p) }}</div>
          <router-link :to="{ name:'blog-detail', params:{ slug: p.slug } }" class="pc-read">Read more →</router-link>
        </div>
      </article>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api/client'

const posts = ref([])
const q = ref('')

function resolveImg(src){
  if (!src) return ''
  const s = String(src)
  if (/^https?:\/\//i.test(s) || s.startsWith('data:image')) return s
  const path = s.startsWith('/') ? s : `/${s}`
  if (path.startsWith('/uploads/')) return `${window.location.origin.replace('5173','8000')}${path}`
  return path
}

async function fetchPosts(){
  const { data } = await api.get('/posts/', { params: { q: q.value, page: 1, page_size: 12, published_only: true } })
  posts.value = data
}

onMounted(fetchPosts)

function stripHtml(html){
  const tmp = document.createElement('div')
  tmp.innerHTML = html || ''
  return (tmp.textContent || tmp.innerText || '').replace(/\s+/g, ' ').trim()
}
function truncate(s, n){ if(!s) return ''; return s.length > n ? s.slice(0, n-1) + '…' : s }
function makeSnippet(p){
  const base = (p.excerpt && p.excerpt.trim()) ? p.excerpt : stripHtml(p.content_html)
  return truncate(base, 140)
}
</script>

<style scoped>
.blog-head{ display:flex; align-items:center; gap:12px; }
.blog-head .controls{ margin-left:auto; }
.post-card{ background:#fff; border:1px solid #e2e8f0; border-radius:12px; overflow:hidden; display:flex; flex-direction:column; }
.post-card .cover img{ width:100%; height:180px; object-fit:cover; display:block; }
.pc-body{ padding:12px; display:flex; flex-direction:column; gap:8px; }
.pc-title{ font-weight:800; color:#0f172a; text-decoration:none; }
.pc-excerpt{ color:#475569; font-size:14px; min-height: 40px; }
.pc-read{ text-decoration:none; color:#2563eb; font-weight:600; }
@media (max-width: 900px){ .grid.cols-3{ grid-template-columns: repeat(2,1fr); } }
@media (max-width: 600px){ .grid.cols-3{ grid-template-columns: 1fr; } }
</style>
