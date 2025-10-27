import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Profile from '../views/Profile.vue'
import CategoryList from '../views/CategoryList.vue'
import CategoryHeads from '../views/CategoryHeads.vue'
import SubCategories from '../views/SubCategories.vue'
import Exam from '../views/Exam.vue'
import Result from '../views/Result.vue'
import SetOverview from '../views/SetOverview.vue'
import Team from '../views/Team.vue'
import ZoomDiscussions from '../views/ZoomDiscussions.vue'
import ZoomDiscussionDetail from '../views/ZoomDiscussionDetail.vue'
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
import AdminZoom from '../views/admin/AdminZoom.vue'
import AdminEssayGrading from '../views/admin/AdminEssayGrading.vue'
import AdminAnalytics from '../views/admin/AdminAnalytics.vue'

const routes = [
  { path: '/', component: Home },
  { path: '/blog', name: 'blog-list', component: BlogList },
  { path: '/blog/:slug', name: 'blog-detail', component: BlogDetail, props: true },
  { path: '/login', component: Login },
  { path: '/register', component: Register },
  { path: '/profile', component: Profile },
  { path: '/categories', component: CategoryHeads },
  { path: '/categories/:headId', component: SubCategories, props: true },
  { path: '/categories/:headId/:subId', component: CategoryList, props: true },
  { path: '/exam/:categoryId', name: 'exam', component: Exam, props: true },
  { path: '/set/:setId', name: 'set-overview', component: SetOverview, props: true },
  { path: '/result/:sessionId', name: 'result', component: Result, props: true },
  { path: '/team', component: Team },
  { path: '/zoom', component: ZoomDiscussions },
  { path: '/zoom/:id', component: ZoomDiscussionDetail, props: true },

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
  { path: '/admin/zoom', component: AdminZoom },
  { path: '/admin/essays', component: AdminEssayGrading },
  { path: '/admin/analytics', component: AdminAnalytics },
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

// Route guard: only admins can access /admin routes (except /admin/login)
router.beforeEach((to, from, next) => {
  if (to.path.startsWith('/admin') && to.path !== '/admin/login'){
    // Read user from localStorage to avoid requiring Pinia instance here
    let user = null
    try { user = JSON.parse(localStorage.getItem('user') || 'null') } catch { user = null }
    const isAdmin = !!(user && user.is_admin === true)
    const isTeacher = !!(user && user.is_teacher === true)

    if (!isAdmin && !isTeacher){
      return next('/admin/login')
    }
    // Teachers are limited to a subset of admin pages
    if (isTeacher && !isAdmin){
      const allowed = [
        '/admin/categories',
        '/admin/questions',
        '/admin/sets',
        '/admin/essays',
        '/admin/zoom',
        '/admin/blog',
      ]
      const ok = allowed.some(p => to.path === p || to.path.startsWith(p + '/'))
      if (!ok){
        return next('/admin/categories')
      }
    }
  }
  return next()
})

export default router
