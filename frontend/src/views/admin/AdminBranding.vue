<template>
  <AdminLayout>
    <template #title>Branding</template>
    <div class="card">
    <h2 style="margin-top:0">Auth Page Branding</h2>
    <p style="color:#475569;">Update images used in Login & Register pages.</p>

    <div class="row">
      <label>Logo URL</label>
      <div class="flex">
        <input v-model="logo" class="input" placeholder="https://... or /uploads/..." />
        <label class="btn secondary">
          Upload
          <input type="file" accept="image/*" style="display:none;" @change="upload('branding_logo', $event)" />
        </label>
      </div>
      <img v-if="logo" :src="logo" style="max-height:50px; margin-top:6px;" />
    </div>

    <div class="row">
      <label>Left Illustration URL</label>
      <div class="flex">
        <input v-model="left" class="input" placeholder="https://... or /uploads/..." />
        <label class="btn secondary">
          Upload
          <input type="file" accept="image/*" style="display:none;" @change="upload('branding_auth_left', $event)" />
        </label>
      </div>
      <img v-if="left" :src="left" style="max-width:280px; border-radius:8px; margin-top:6px;" />
    </div>

    <div class="row">
      <label>Right Illustration URL</label>
      <div class="flex">
        <input v-model="right" class="input" placeholder="https://... or /uploads/..." />
        <label class="btn secondary">
          Upload
          <input type="file" accept="image/*" style="display:none;" @change="upload('branding_auth_right', $event)" />
        </label>
      </div>
      <img v-if="right" :src="right" style="max-width:280px; border-radius:8px; margin-top:6px;" />
    </div>

    <div style="display:flex; gap:8px; margin-top:10px;">
      <button class="btn" @click="save">Save</button>
      <button class="btn secondary" @click="reset">Reset to defaults</button>
    </div>
  </div>
  </AdminLayout>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import AdminLayout from '../../components/admin/AdminLayout.vue'
import api from '../../api/client'

const logo = ref('')
const left = ref('')
const right = ref('')

onMounted(() => {
  logo.value = localStorage.getItem('branding_logo') || '/logo.svg'
  left.value = localStorage.getItem('branding_auth_left') || '/med-left.svg'
  right.value = localStorage.getItem('branding_auth_right') || '/med-right.svg'
})

function save(){
  localStorage.setItem('branding_logo', logo.value)
  localStorage.setItem('branding_auth_left', left.value)
  localStorage.setItem('branding_auth_right', right.value)
  alert('Branding saved. Refresh Login/Register to see changes.')
}

function reset(){
  localStorage.removeItem('branding_logo')
  localStorage.removeItem('branding_auth_left')
  localStorage.removeItem('branding_auth_right')
  logo.value = '/logo.svg'
  left.value = '/med-left.svg'
  right.value = '/med-right.svg'
}

async function upload(key, evt){
  const file = evt.target.files && evt.target.files[0]
  if (!file) return
  const fd = new FormData()
  fd.append('file', file)
  const { data } = await api.post('/files/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
  const url = data.url
  if (key === 'branding_logo') logo.value = url
  if (key === 'branding_auth_left') left.value = url
  if (key === 'branding_auth_right') right.value = url
}
</script>
<style scoped>
.row{ margin-top:12px; display:flex; flex-direction:column; gap:6px; }
.flex{ display:flex; gap:8px; align-items:center; }
</style>
