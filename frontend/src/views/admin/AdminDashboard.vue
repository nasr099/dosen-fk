<template>
  <AdminLayout>
    <template #title>Dashboard</template>
    <div class="card">
      <h2 style="margin-top:0">Admin Dashboard</h2>
      <div style="display:flex; gap:8px; margin-top:8px; flex-wrap:wrap;">
        <router-link to="/admin/users"><button class="btn">Users</button></router-link>
        <router-link to="/admin/categories"><button class="btn">Categories</button></router-link>
        <router-link to="/admin/questions"><button class="btn">Questions</button></router-link>
        <router-link to="/admin/promos"><button class="btn">Promos</button></router-link>
        <router-link to="/admin/analytics"><button class="btn">Analytics</button></router-link>
        <router-link to="/admin/blog"><button class="btn">Blog</button></router-link>
        <router-link to="/admin/zoom"><button class="btn">Zoom</button></router-link>
        <router-link to="/admin/team"><button class="btn">Team</button></router-link>
      </div>
    </div>
  </AdminLayout>
</template>
<script setup>
import AdminLayout from '../../components/admin/AdminLayout.vue'
</script>
