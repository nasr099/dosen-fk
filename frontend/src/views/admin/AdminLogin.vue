<template>
  <div class="card" style="max-width:420px; margin: 0 auto;">
    <h2>Admin Login</h2>
    <form @submit.prevent="submit">
      <label>Email</label>
      <input v-model="email" type="email" class="input" required />
      <label>Password</label>
      <input v-model="password" type="password" class="input" required />
      <button class="btn" style="margin-top:12px; width:100%">Login</button>
    </form>
  </div>
</template>
<script setup>
import { ref } from 'vue'
import api from '../../api/client'
import { useAuthStore } from '../../store/auth'
import router from '../../router'

const email = ref('')
const password = ref('')
const auth = useAuthStore()

const submit = async () => {
  const params = new URLSearchParams()
  params.append('username', email.value)
  params.append('password', password.value)
  const { data } = await api.post('/auth/login', params)
  const me = await api.get('/users/me', { headers: { Authorization: `Bearer ${data.access_token}` }})
  const isAdmin = me.data.is_admin === true
  const isTeacher = me.data.is_teacher === true
  if (!isAdmin && !isTeacher) {
    alert('Not authorized')
    return
  }
  auth.setAuth(data.access_token, me.data)
  // Teachers go to a permitted page; admins go to /admin/users
  if (isAdmin) router.push('/admin/users')
  else router.push('/admin/categories')
}
</script>
