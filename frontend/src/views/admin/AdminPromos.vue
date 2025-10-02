<template>
  <div class="card">
    <h2>Promo Banners</h2>
    <form @submit.prevent="add">
      <input v-model="form.title" class="input" placeholder="Title" required />
      <input v-model="form.description" class="input" placeholder="Description" />
      <div class="image-row">
        <input v-model="form.image_url" class="input" placeholder="Image URL" />
        <label class="btn secondary" style="white-space:nowrap;">
          Upload
          <input type="file" accept="image/*" style="display:none;" @change="onBannerFileChange" />
        </label>
      </div>
      <img v-if="form.image_url" :src="form.image_url" alt="preview" style="max-width:280px; border-radius:8px; margin:6px 0;" />
      <input v-model="form.link_url" class="input" placeholder="Link URL" />
      <input v-model.number="form.display_order" class="input" placeholder="Display Order" />
      <label><input type="checkbox" v-model="form.is_active" /> Active</label>
      <button class="btn" style="margin-top:8px;">Add Promo</button>
    </form>

    <ul>
      <li v-for="p in promos" :key="p.id" style="display:flex; gap:8px; align-items:center; padding:8px 0;">
        <span style="flex:1;">{{ p.title }} - {{ p.description }}</span>
        <button class="btn secondary" @click="remove(p.id)">Delete</button>
      </li>
    </ul>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import api from '../../api/client'
const promos = ref([])
const form = ref({ title:'', description:'', image_url:'', link_url:'', display_order:0, is_active:true })

async function load(){
  const { data } = await api.get('/promos/')
  promos.value = data
}

onMounted(load)

async function add(){
  await api.post('/promos/', form.value)
  form.value = { title:'', description:'', image_url:'', link_url:'', display_order:0, is_active:true }
  await load()
}

async function remove(id){
  await api.delete(`/promos/${id}`)
  await load()
}

async function onBannerFileChange(evt){
  const file = evt.target.files && evt.target.files[0]
  if (!file) return
  const fd = new FormData()
  fd.append('file', file)
  const { data } = await api.post('/files/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
  form.value.image_url = data.url
}
</script>

<style scoped>
.image-row { display:flex; gap:8px; align-items:center; }
</style>
