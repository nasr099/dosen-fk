import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Profile from '../views/Profile.vue'
import CategoryList from '../views/CategoryList.vue'
import Exam from '../views/Exam.vue'
import Result from '../views/Result.vue'
import SetOverview from '../views/SetOverview.vue'
import Team from '../views/Team.vue'
import BlogList from '../views/BlogList.vue'
import BlogDetail from '../views/BlogDetail.vue'

import AdminLogin from '../views/admin/AdminLogin.vue'
import AdminUsers from '../views/admin/AdminUsers.vue'
import AdminCategories from '../views/admin/AdminCategories.vue'
import AdminQuestions from '../views/admin/AdminQuestions.vue'
import AdminPromos from '../views/admin/AdminPromos.vue'
import AdminSetEdit from '../views/admin/AdminSetEdit.vue'
import AdminBranding from '../views/admin/AdminBranding.vue'
import AdminTeam from '../views/admin/AdminTeam.vue'
import AdminBlogList from '../views/admin/AdminBlogList.vue'
import AdminBlogEdit from '../views/admin/AdminBlogEdit.vue'

const routes = [
  { path: '/', component: Home },
  { path: '/blog', name: 'blog-list', component: BlogList },
  { path: '/blog/:slug', name: 'blog-detail', component: BlogDetail, props: true },
  { path: '/login', component: Login },
  { path: '/register', component: Register },
  { path: '/profile', component: Profile },
  { path: '/categories', component: CategoryList },
  { path: '/exam/:categoryId', name: 'exam', component: Exam, props: true },
  { path: '/set/:setId', name: 'set-overview', component: SetOverview, props: true },
  { path: '/result/:sessionId', name: 'result', component: Result, props: true },
  { path: '/team', component: Team },

  { path: '/admin/login', component: AdminLogin },
  { path: '/admin/users', component: AdminUsers },
  { path: '/admin/categories', component: AdminCategories },
  { path: '/admin/questions', component: AdminQuestions },
  { path: '/admin/sets/:setId', component: AdminSetEdit, props: true },
  { path: '/admin/promos', component: AdminPromos },
  { path: '/admin/branding', component: AdminBranding },
  { path: '/admin/team', component: AdminTeam },
  { path: '/admin/blog', component: AdminBlogList },
  { path: '/admin/blog/new', component: AdminBlogEdit, props: { isNew: true } },
  { path: '/admin/blog/:postId', component: AdminBlogEdit, props: true },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (to.hash) {
      return { el: to.hash, behavior: 'smooth' }
    }
    if (savedPosition) return savedPosition
    return { top: 0 }
  },
})

export default router
