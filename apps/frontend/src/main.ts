import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router'
import i18n from './i18n'
import { setupClerk } from './plugins/clerk'

const app = createApp(App)

app.use(router)
app.use(i18n)
setupClerk(app)

app.mount('#app')
