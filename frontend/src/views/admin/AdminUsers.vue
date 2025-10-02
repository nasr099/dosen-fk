<template>
  <div class="card">
    <h2>Users</h2>
    <table style="width:100%; border-collapse:collapse;">
      <thead>
        <tr>
          <th style="text-align:left; border-bottom:1px solid #e2e8f0; padding:8px;">Email</th>
          <th style="text-align:left; border-bottom:1px solid #e2e8f0; padding:8px;">Name</th>
          <th style="text-align:left; border-bottom:1px solid #e2e8f0; padding:8px;">Phone</th>
          <th style="text-align:left; border-bottom:1px solid #e2e8f0; padding:8px;">Admin</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="u in users" :key="u.id">
          <td style="padding:8px;">{{ u.email }}</td>
          <td style="padding:8px;">{{ u.full_name }}</td>
          <td style="padding:8px; white-space:nowrap;">{{ u.phone || '-' }}</td>
          <td style="padding:8px;">{{ u.is_admin ? 'Yes' : 'No' }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import api from '../../api/client'
const users = ref([])

onMounted(async () => {
  const { data } = await api.get('/users/')
  users.value = data
})
</script>
