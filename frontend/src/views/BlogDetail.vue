<template>
  <article class="card" v-if="post">
    <h1 class="title">{{ post.title }}</h1>
    <div v-if="post.cover_url" class="cover"><img :src="resolveImg(post.cover_url)" :alt="post.title" /></div>
    <div class="meta">Published: {{ formatDate(post.published_at || post.created_at) }}</div>
    <div class="content" v-html="post.content_html"></div>
  </article>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '../api/client'

const route = useRoute()
const post = ref(null)

function resolveImg(src){
  if (!src) return ''
  const s = String(src)
  if (/^https?:\/\//i.test(s) || s.startsWith('data:image')) return s
  return s.startsWith('/') ? s : `/${s}`
}
function formatDate(s){ if(!s) return ''; return new Date(s).toLocaleDateString() }

onMounted(async () => {
  const slug = route.params.slug
  const { data } = await api.get(`/posts/${slug}`)
  post.value = data
})
</script>

<style scoped>
.title{ font-weight:800; font-size:26px; margin:0 0 8px; }
.cover img{ width:100%; height:auto; border-radius:8px; }
.meta{ color:#64748b; font-size:13px; margin:8px 0 16px; }
.content :deep(img){ max-width:100%; height:auto; }
.content :deep(h2){ margin-top:1.2em; }
</style>
