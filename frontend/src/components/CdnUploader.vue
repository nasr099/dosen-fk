<template>
  <div class="uploader">
    <input ref="fileInput" type="file" accept="image/*" @change="onChoose" hidden />
    <div class="row">
      <input class="url" type="text" :value="modelValue" @input="onInput" placeholder="Paste image URL or upload..." />
      <button type="button" class="btn" @click="pick">Upload to CDN</button>
    </div>
    <div v-if="previewUrl" class="preview">
      <img :src="previewUrl" alt="preview" />
    </div>
  </div>
</template>
<script setup>
import { ref, watch, onMounted } from 'vue'
import { presignUpload } from '../api/files'

const props = defineProps({
  modelValue: { type: String, default: '' }
})
const emit = defineEmits(['update:modelValue'])

const fileInput = ref(null)
const previewUrl = ref('')

function pick(){ fileInput.value?.click() }

function resolve(src){
  if (!src) return ''
  const s = String(src)
  if (/^https?:\/\//i.test(s) || s.startsWith('data:image')) return s
  const path = s.startsWith('/') ? s : `/${s}`
  if (path.startsWith('/uploads/')) return `${window.location.origin.replace('5173','8000')}${path}`
  return s
}

function onInput(e){
  const v = e.target.value
  emit('update:modelValue', v)
  previewUrl.value = resolve(v)
}

async function onChoose(e){
  const file = e.target.files?.[0]
  if (!file) return
  try {
    // 1) request presigned PUT
    const { upload_url, public_url } = await presignUpload(file.name, file.type)
    // 2) upload directly to Spaces
    await fetch(upload_url, {
      method: 'PUT',
      headers: {
        'Content-Type': file.type,
        'x-amz-acl': 'public-read',
        'Cache-Control': 'public, max-age=31536000, immutable',
      },
      body: file,
    })
    // 3) set URL to form
    emit('update:modelValue', public_url)
    previewUrl.value = public_url
  } catch (err) {
    console.error('Upload failed', err)
    alert('Upload failed. Please try again.')
  } finally {
    e.target.value = ''
  }
}

// Keep preview in sync for imported values or programmatic changes
watch(() => props.modelValue, (v) => {
  previewUrl.value = resolve(v)
}, { immediate: true })
</script>
<style scoped>
.uploader .row{ display:flex; gap:8px; }
.uploader .url{ flex:1; padding:8px 10px; border:1px solid #cbd5e1; border-radius:8px; }
.btn{ padding:8px 12px; border-radius:8px; background:#2563eb; color:#fff; border:0; cursor:pointer; }
.preview{ margin-top:8px; }
.preview img{ max-height:120px; border:1px solid #e2e8f0; border-radius:8px; }
</style>
