import { createApp } from 'vue'

import App from './App.vue'
import router from './router'
import './style.css'

import { createBootstrap } from 'bootstrap-vue-next/plugins/createBootstrap'
import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue-next/dist/bootstrap-vue-next.css'

import pinia from './store/index'

const app = createApp(App)
app.use(createBootstrap())
app.use(pinia)
app.use(router)
app.mount('#app')
