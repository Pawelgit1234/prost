import { createRouter, createWebHistory } from 'vue-router'
import SignIn from '../views/SignIn.vue'
import SignUp from '../views/SignUp.vue'
import Messenger from '../views/Messenger.vue'

const routes = [
  {
    path: "/signin",
    name: "SignIn",
    component: SignIn,
  },
  {
    path: "/signup",
    name: "SignUp",
    component: SignUp,
  },
  {
    path: "/messenger",
    name: "Messenger",
    component: Messenger,
  },
  // redirect
  {
    path: "/",
    redirect: "/signin",
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
