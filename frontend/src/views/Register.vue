<template>
  <div class="auth-wrap">
    <img class="illus left" :src="leftImg" alt="left" />
    <div class="panel card">
      <div class="brand">
        <img :src="logoImg" alt="logo" class="logo" />
        <h2>Register</h2>
      </div>
      <form @submit.prevent="submit" class="form">
        <label>Full Name</label>
        <input v-model="full_name" class="input" required />
        <label>Email</label>
        <input v-model="email" type="email" class="input" required />
        <label>Phone Number</label>
        <input v-model="phone" type="tel" class="input" placeholder="e.g. +628123456789" required />
        <label>Password</label>
        <input v-model="password" type="password" class="input" minlength="6" required />
        <label>Confirm Password</label>
        <input v-model="confirmPassword" type="password" class="input" minlength="6" required />
        <button class="btn primary full" :disabled="submitting" style="margin-top:8px;">{{ submitting ? 'Creating...' : 'Create Account' }}</button>
      </form>
      
    </div>
    <img class="illus right" :src="rightImg" alt="right" />
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import api from '../api/client'
import router from '../router'

const email = ref('')
const full_name = ref('')
const phone = ref('')
const password = ref('')
const confirmPassword = ref('')
const logoImg = ref('/logo.svg')
const leftImg = ref('/med-left.svg')
const rightImg = ref('/med-right.svg')
const submitting = ref(false)

const submit = async () => {
  // Basic validations
  if (password.value !== confirmPassword.value) {
    alert('Password dan konfirmasi password tidak sama.')
    return
  }
  if (!email.value || !full_name.value || !password.value) return
  const payload = {
    email: email.value,
    full_name: full_name.value,
    password: password.value,
    phone: phone.value
  }
  try{
    submitting.value = true
    await api.post('/auth/register', payload)
    router.push('/login')
  } catch (err){
    const msg = err?.response?.data?.detail || err?.message || 'Registration failed'
    // Specific duplicate email case from backend: "Email already registered"
    alert(msg)
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  const l = localStorage.getItem('branding_logo'); if (l) logoImg.value = l
  const il = localStorage.getItem('branding_auth_left'); if (il) leftImg.value = il
  const ir = localStorage.getItem('branding_auth_right'); if (ir) rightImg.value = ir
})
</script>

<style scoped>
.auth-wrap{ position:relative; display:flex; align-items:center; justify-content:center; min-height: calc(100vh - 140px); }
.panel{ width: 460px; position:relative; z-index:2; }
.brand{ display:flex; flex-direction:column; align-items:center; gap:8px; margin-bottom:8px; }
.logo{ height:44px; }
.form{ display:flex; flex-direction:column; gap:8px; }
.btn.full{ width:100%; }
.illus{ position:absolute; bottom:0; opacity:.9; max-width: 300px; }
.illus.left{ left: 20px; }
.illus.right{ right: 20px; }
@media (max-width: 900px){ .illus{ display:none; } }
</style>
