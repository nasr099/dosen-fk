<template>
  <div class="card">
    <div class="head">
      <h2>Blog Posts</h2>
      <router-link to="/admin/blog/new"><button class="btn">+ New Post</button></router-link>
    </div>
    <table style="width:100%; border-collapse:collapse;">
      <thead>
        <tr>
          <th class="th">Title</th>
          <th class="th">Slug</th>
          <th class="th">Published</th>
          <th class="th">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="p in posts" :key="p.id">
          <td class="td">{{ p.title }}</td>
          <td class="td">{{ p.slug }}</td>
          <td class="td">{{ p.is_published ? 'Yes' : 'No' }}</td>
          <td class="td">
            <router-link :to="`/admin/blog/${p.id}`">Edit</router-link>
            <span> · </span>
            <a href="#" @click.prevent="del(p.id)">Delete</a>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import api from '../../api/client'

const posts = ref([])

async function load(){
  const { data } = await api.get('/posts/', { params: { published_only: false, page_size: 100 } })
  posts.value = data
}

async function del(id){
  if (!confirm('Delete this post?')) return
  await api.delete(`/posts/${id}`)
  await load()
}

onMounted(load)
</script>

<style scoped>
.head{ display:flex; align-items:center; justify-content:space-between; }
.th{ text-align:left; border-bottom:1px solid #e2e8f0; padding:8px; }
.td{ padding:8px; border-bottom:1px solid #eef2f7; }
</style>
