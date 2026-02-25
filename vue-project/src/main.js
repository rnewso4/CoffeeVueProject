import '@mdi/font/css/materialdesignicons.css'
import { createApp } from 'vue'

import App from './App.vue'
import router from './router'
import vuetify from './plugins/vuetify'
import { VueFire, VueFireAuth } from 'vuefire'
import { firebaseApp } from './firebase'
import { SnackbarService, Vue3Snackbar } from "vue3-snackbar";
import PrimeVue from 'primevue/config';
import Material from '@primeuix/themes/material'
import "vue3-snackbar/styles";

const app = createApp(App)

app.use(router)
app.use(vuetify)
app.use(SnackbarService);
app.use(VueFire, {
    // imported above but could also just be created here
    firebaseApp,
    modules: [
      // we will see other modules later on
      VueFireAuth(),
    ],
  });
app.use(PrimeVue, {
    theme: {
        preset: Material,
        options: {
          darkModeSelector: '.my-app-dark',
      }
    }
});

app.component("vue3-snackbar", Vue3Snackbar);
app.mount('#app')
