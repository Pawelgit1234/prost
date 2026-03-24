import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Messenger from '../views/Messenger.vue'
import GoogleCallback from '../views/GoogleCallback.vue';
import { useAuthStore } from '../store/auth';
import { useInvitationStore } from '../store/invitations';

const routes = [
  {
    path: "/invite/:uuid",
    name: "Invite",
    meta: { invite: true },
  },
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
  {
  path: '/:catchAll(.*)', // catches all non existing routes
    redirect: (to) => {
      const authStore = useAuthStore()
      return authStore.isLoggedIn ? '/messenger' : '/login'
    }
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  const invitationStore = useInvitationStore()

  if (to.meta.invite) {
    const uuid = to.params.uuid as string

    if (!authStore.isLoggedIn) {
      return next('/login')
    }

    await invitationStore.join_via_invitation(uuid)
    return next('/messenger')
  }

  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    return next('/login')
  }

  if (to.meta.guestOnly && authStore.isLoggedIn) {
    return next('/messenger')
  }

  next()
})

export default router
