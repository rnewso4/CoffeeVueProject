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
import ToastService from 'primevue/toastservice';

// Apply cached dark mode before first paint to prevent flash
if (localStorage.getItem('darkMode') === 'true') {
  document.documentElement.classList.add('my-app-dark')
}

const app = createApp(App)

app.use(router)
app.use(vuetify)
app.use(ToastService);
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
