import { createApp } from 'vue'
import App from './App.vue'
import './style.css'

import { createBootstrap } from 'bootstrap-vue-next/plugins/createBootstrap'
import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue-next/dist/bootstrap-vue-next.css'

const app = createApp(App)

app.use(createBootstrap())
app.mount('#app')
