import { createRouter, createWebHistory } from 'vue-router'
import { onAuthStateChanged } from 'firebase/auth'
import { auth } from '@/firebase'
import Login from '@/pages/Login.vue'
import Register from '@/pages/Register.vue'
import Home from '@/pages/Home.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      component: Login,
      meta: { requiresGuest: true },
    },
    {
      path: '/register',
      component: Register,
      meta: { requiresGuest: true },
    },
    {
      path: '/',
      component: Home,
      meta: { requiresAuth: true },
    },
    {
      path: '/home',
      component: Home,
      meta: { requiresAuth: true },
    },
  ],
})

let authReady = false
const authReadyPromise = new Promise((resolve) => {
  onAuthStateChanged(auth, () => {
    authReady = true
    resolve()
  })
})

router.beforeEach(async (to) => {
  await authReadyPromise
  const user = auth.currentUser

  if (to.meta.requiresAuth && !user) {
    return { path: '/login' }
  }
  if (to.meta.requiresGuest && user) {
    return { path: '/home' }
  }
})

export default router
