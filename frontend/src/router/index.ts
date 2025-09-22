import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Messenger from '../views/Messenger.vue'
import GoogleCallback from '../views/GoogleCallback.vue';
import { useAuthStore } from '../store/auth';

const routes = [
  {
    path: "/login",
    name: "Login",
    component: Login,
    meta: { guestOnly: true },
  },
  {
    path: "/register",
    name: "Register",
    component: Register,
    meta: { guestOnly: true },
  },
  {
    path: "/auth/google",
    name: "Google",
    component: GoogleCallback,
    meta: { guestOnly: true },
  },
  {
    path: "/messenger",
    name: "Messenger",
    component: Messenger,
    meta: { requiresAuth: true },
  },
  // redirect
  {
    path: "/",
    redirect: "/login",
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    return next('/login')
  }

  if (to.meta.guestOnly && authStore.isLoggedIn) {
    return next('/messenger')
  }

  next()
})

export default router
