<template>
  <div class="card">
    <h2>Admin Dashboard</h2>
    <div style="display:flex; gap:8px; margin-top:8px;">
      <router-link to="/admin/users"><button class="btn">Users</button></router-link>
      <router-link to="/admin/categories"><button class="btn">Categories</button></router-link>
      <router-link to="/admin/questions"><button class="btn">Questions</button></router-link>
      <router-link to="/admin/promos"><button class="btn">Promos</button></router-link>
    </div>
  </div>
</template>
<script setup>
</script>
