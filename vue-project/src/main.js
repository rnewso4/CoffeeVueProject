import '@mdi/font/css/materialdesignicons.css'
import { createApp } from 'vue'

import App from './App.vue'
import router from './router'
import vuetify from './plugins/vuetify'
import { VueFire, VueFireAuth } from 'vuefire'
import { firebaseApp } from './firebase'

const app = createApp(App)

app.use(router)
app.use(vuetify)
app.use(VueFire, {
    // imported above but could also just be created here
    firebaseApp,
    modules: [
      // we will see other modules later on
      VueFireAuth(),
    ],
  })

app.mount('#app')
