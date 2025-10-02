<template>
  <div class="card" v-if="set">
    <h2>{{ set.title }}</h2>
    <p class="desc">{{ set.description }}</p>
    <div class="meta">
      <div><strong>Kategori:</strong> {{ category?.name }}</div>
      <div><strong>Pertanyaan:</strong> {{ questionCount }} item</div>
      <div><strong>Durasi:</strong> {{ set.time_limit_minutes }} menit</div>
    </div>
    <button class="btn" style="margin-top:16px;" @click="start">Mulai Simulasi</button>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api/client'

const route = useRoute()
const router = useRouter()
const setId = Number(route.params.setId)

const set = ref(null)
const category = ref(null)
const questionCount = ref(0)

onMounted(async () => {
  const { data: s } = await api.get(`/sets/${setId}`)
  set.value = s
  const { data: cats } = await api.get('/categories/')
  category.value = cats.find(c => c.id === s.category_id)
  const { data: qs } = await api.get('/questions/', { params: { question_set_id: setId } })
  questionCount.value = qs.length
})

function start(){
  router.push({ name: 'exam', params: { categoryId: set.value.category_id }, query: { setId } })
}
</script>

<style scoped>
.desc{ color:#64748b; line-height:1.85; letter-spacing:0.1px; white-space: pre-line; margin-top:6px; }
.meta{ margin-top:12px; display:flex; flex-direction:column; gap:6px; line-height:1.7; }
</style>
