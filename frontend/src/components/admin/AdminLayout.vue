<template>
  <div class="admin-shell" :class="{ collapsed }">
    <aside class="admin-sidebar">
      <div class="brand">
        <div class="logo">ME</div>
        <div class="brand-name">MedExam Admin</div>
      </div>
      <nav class="nav">
        <RouterLink v-if="isAdmin" to="/admin/branding" class="nav-item" :class="{active: $route.path.startsWith('/admin/branding')}">
          <span class="icon">🎨</span>
          <span>Branding</span>
        </RouterLink>
        <RouterLink v-if="isAdmin" to="/admin/users" class="nav-item" :class="{active: $route.path.startsWith('/admin/users')}">
          <span class="icon">👥</span>
          <span>Users</span>
        </RouterLink>
        <RouterLink v-if="isAdmin || isTeacher" to="/admin/categories" class="nav-item" :class="{active: $route.path.startsWith('/admin/categories')}">
          <span class="icon">🗂️</span>
          <span>Categories</span>
        </RouterLink>
        <RouterLink v-if="isAdmin || isTeacher" to="/admin/questions" class="nav-item" :class="{active: $route.path.startsWith('/admin/questions')}">
          <span class="icon">❓</span>
          <span>Questions</span>
        </RouterLink>
        <RouterLink v-if="isAdmin || isTeacher" to="/admin/readings" class="nav-item" :class="{active: $route.path.startsWith('/admin/readings')}">
          <span class="icon">📖</span>
          <span>Readings</span>
        </RouterLink>
        <RouterLink v-if="isAdmin || isTeacher" to="/admin/tryouts" class="nav-item" :class="{active: $route.path.startsWith('/admin/tryouts')}">
          <span class="icon">🧪</span>
          <span>Tryouts</span>
        </RouterLink>
        <RouterLink v-if="isAdmin || isTeacher" to="/admin/essays" class="nav-item" :class="{active: $route.path.startsWith('/admin/essays')}">
          <span class="icon">📝</span>
          <span>Essays Grading</span>
        </RouterLink>
        <RouterLink v-if="isAdmin" to="/admin/analytics" class="nav-item" :class="{active: $route.path.startsWith('/admin/analytics')}">
          <span class="icon">📊</span>
          <span>Analytics</span>
        </RouterLink>
        <RouterLink v-if="isAdmin || isTeacher" to="/admin/llm" class="nav-item" :class="{active: $route.path.startsWith('/admin/llm')}">
          <span class="icon">🤖</span>
          <span>Questions Generator</span>
        </RouterLink>
        <RouterLink v-if="isAdmin || isTeacher" to="/admin/llm-scan" class="nav-item" :class="{active: $route.path.startsWith('/admin/llm-scan')}">
          <span class="icon">🧾</span>
          <span>Question Scanner</span>
        </RouterLink>
        <RouterLink v-if="isAdmin" to="/admin/promos" class="nav-item" :class="{active: $route.path.startsWith('/admin/promos')}">
          <span class="icon">🏷️</span>
          <span>Promos</span>
        </RouterLink>
        <RouterLink v-if="isAdmin || isTeacher" to="/admin/blog" class="nav-item" :class="{active: $route.path.startsWith('/admin/blog')}">
          <span class="icon">✍️</span>
          <span>Blog</span>
        </RouterLink>
        <RouterLink v-if="isAdmin || isTeacher" to="/admin/zoom" class="nav-item" :class="{active: $route.path.startsWith('/admin/zoom')}">
          <span class="icon">🎥</span>
          <span>Zoom Discussions</span>
        </RouterLink>
        <RouterLink v-if="isAdmin" to="/admin/team" class="nav-item" :class="{active: $route.path.startsWith('/admin/team')}">
          <span class="icon">👤</span>
          <span>Team</span>
        </RouterLink>
      </nav>
    </aside>

    <main class="admin-main">
      <header class="admin-topbar">
        <div class="page-title">
          <slot name="title">Admin</slot>
        </div>
        <div class="topbar-actions">
          <button class="icon-btn" @click="toggleSidebar" :title="collapsed ? 'Expand sidebar' : 'Collapse sidebar'" aria-label="Toggle sidebar">{{ collapsed ? '➡️' : '⬅️' }}</button>
          <slot name="actions"></slot>
        </div>
      </header>
      <section class="admin-content">
        <slot />
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const collapsed = ref(false)
const isAdmin = ref(false)
const isTeacher = ref(false)
onMounted(() => {
  try { collapsed.value = localStorage.getItem('admin_sidebar_collapsed') === '1' } catch {}
  try {
    const user = JSON.parse(localStorage.getItem('user') || 'null')
    isAdmin.value = !!(user && user.is_admin === true)
    isTeacher.value = !!(user && user.is_teacher === true)
  } catch {}
})
function toggleSidebar(){
  collapsed.value = !collapsed.value
  try { localStorage.setItem('admin_sidebar_collapsed', collapsed.value ? '1' : '0') } catch {}
}
</script>

<style scoped>
/* Match NavBar height (Site header is 60px in NavBar.vue) */
:root { --header-h: 60px; }
.admin-shell{ display:flex; min-height: calc(100vh - var(--header-h)); gap:0; }
.admin-sidebar{ width: 240px; background: #0f172a; color:#e2e8f0; padding:16px 12px; position:sticky; top:var(--header-h); height: calc(100vh - var(--header-h)); border-right:1px solid #1f2937; transition: width .18s ease; overflow:hidden; }
.brand{ display:flex; align-items:center; gap:10px; padding:8px 10px 16px; margin-bottom:6px; border-bottom:1px solid rgba(255,255,255,.08); }
.logo{ width:32px; height:32px; border-radius:8px; background:#2563eb; color:#fff; font-weight:800; display:flex; align-items:center; justify-content:center; }
.brand-name{ font-weight:700; letter-spacing:.2px; }
.nav{ display:flex; flex-direction:column; gap:4px; padding-top:8px; }
.nav-item{ display:flex; align-items:center; gap:10px; color:#cbd5e1; padding:10px 12px; border-radius:8px; text-decoration:none; white-space:nowrap; }
.nav-item:hover{ background:#111827; color:#fff; }
.nav-item.active{ background:#1f2937; color:#fff; }
.icon{ width:18px; text-align:center; }

.admin-main{ flex:1; display:flex; flex-direction:column; min-width:0; }
.admin-topbar{ position:sticky; top:var(--header-h); z-index:5; backdrop-filter:saturate(1.2) blur(6px); background:rgba(255,255,255,.7); border-bottom:1px solid #e5e7eb; display:flex; align-items:center; justify-content:space-between; padding:12px 16px; }
.page-title{ font-weight:800; font-size:18px; color:#0f172a; }
.topbar-actions{ display:flex; gap:8px; align-items:center; }
.icon-btn{ border:1px solid #e5e7eb; background:#fff; border-radius:8px; padding:6px 8px; cursor:pointer; }
.admin-content{ padding:16px; display:block; }

.admin-shell.collapsed .admin-sidebar{ width:64px; }
.admin-shell.collapsed .brand-name{ display:none; }
.admin-shell.collapsed .nav-item{ gap:0; justify-content:center; }
.admin-shell.collapsed .nav-item span:not(.icon){ display:none; }
.admin-shell.collapsed .icon{ width:auto; }

@media (max-width: 980px){
  .admin-sidebar{ display:none; }
  .admin-shell{ display:block; }
  .admin-topbar{ position:static; top:auto; }
}
</style>
