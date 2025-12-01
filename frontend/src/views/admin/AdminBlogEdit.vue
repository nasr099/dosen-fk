<template>
  <AdminLayout>
    <template #title>{{ isNew ? 'New Post' : 'Edit Post' }}</template>
    <div class="card">
    <h2 style="margin-top:0">{{ isNew ? 'New Post' : 'Edit Post' }}</h2>
    <div class="form-grid">
      <div class="row full"><label>Title</label><input v-model="form.title" class="input" /></div>
      <div class="row"><label>Slug</label><input v-model="form.slug" class="input" placeholder="my-post-slug" /></div>
      <div class="row"><label>Published</label><input type="checkbox" v-model="form.is_published" /></div>
      <div class="row full"><label>Excerpt</label><input v-model="form.excerpt" class="input" /></div>
      <div class="row full">
        <label>Cover</label>
        <CdnUploader v-model="form.cover_url" />
      </div>
      <div class="row full">
        <label>Content</label>
        <RichTextEditor v-model="form.content_html" placeholder="Write your article..." />
      </div>
    </div>

    <div style="display:flex; gap:8px; margin-top:16px;">
      <button class="btn" :disabled="!canSave" @click="save">Save</button>
      <router-link class="btn secondary" to="/admin/blog">Back</router-link>
    </div>
  </div>
  </AdminLayout>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue'
import AdminLayout from '../../components/admin/AdminLayout.vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../../api/client'
import RichTextEditor from '../../components/RichTextEditor.vue'
import CdnUploader from '../../components/CdnUploader.vue'

const route = useRoute()
const router = useRouter()
const isNew = route.params.postId ? false : (route.params.isNew ?? true)

const form = ref({ title:'', slug:'', excerpt:'', content_html:'', cover_url:'', is_published:false, published_at:null })

function resolveImg(src){
  if (!src) return ''
  const s = String(src)
  if (/^https?:\/\//i.test(s) || s.startsWith('data:image')) return s
  const path = s.startsWith('/') ? s : `/${s}`
  if (path.startsWith('/uploads/')) return `${window.location.origin.replace('5173','8000')}${path}`
  return path
}

onMounted(async () => {
  if (!isNew){
    const id = route.params.postId
    // fetch by id via admin list then filter; for simplicity, get list with published_only=false
    const { data } = await api.get('/posts/', { params: { published_only: false, page_size: 100 } })
    const found = data.find(x => String(x.id) === String(id))
    if (found) form.value = { ...found }
  }
})

const canSave = computed(() => !!form.value.title && !!form.value.slug && !!form.value.content_html)

// cover is now handled by <CdnUploader v-model="form.cover_url" />

async function save(){
  const payload = { ...form.value }
  if (isNew){
    const { data } = await api.post('/posts/', payload)
    router.push('/admin/blog')
  } else {
    const id = route.params.postId
    await api.put(`/posts/${id}`, payload)
    router.push('/admin/blog')
  }
}
</script>

<style scoped>
.form-grid { display:grid; grid-template-columns: repeat(2, 1fr); gap:12px; }
.form-grid .row{ display:flex; flex-direction:column; gap:6px; }
.form-grid .row.full{ grid-column: 1 / -1; }
</style>
