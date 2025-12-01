<template>
  <AdminLayout>
    <template #title>Promos</template>
    <div class="card">
    <h2 style="margin-top:0">Promo Banners</h2>
    <form @submit.prevent="add">
      <input v-model="form.title" class="input" placeholder="Title" required />
      <input v-model="form.description" class="input" placeholder="Description" />
      <CdnUploader v-model="form.image_url" />
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
  </AdminLayout>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import AdminLayout from '../../components/admin/AdminLayout.vue'
import api from '../../api/client'
import CdnUploader from '../../components/CdnUploader.vue'
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

// file upload handled by CdnUploader
</script>

<style scoped>
.image-row { display:flex; gap:8px; align-items:center; }
</style>
