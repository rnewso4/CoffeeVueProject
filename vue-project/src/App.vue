<script setup>
import { RouterView } from 'vue-router'
import { onMounted } from 'vue'
import { onAuthStateChanged } from 'firebase/auth'
import { doc, getDoc } from 'firebase/firestore'
import { auth, db } from '@/firebase'
import { setInitials } from '@/functions/functions'

onMounted(() => {
  onAuthStateChanged(auth, async (user) => {
    if (user) {
      try {
        const userDoc = await getDoc(doc(db, 'users', user.uid))
        const data = userDoc.exists() ? userDoc.data() : {}
        const fullName = data.fullName || ''
        setInitials(fullName)
        const darkMode = data.darkMode === true
        if (darkMode) {
          document.documentElement.classList.add('my-app-dark')
        } else {
          document.documentElement.classList.remove('my-app-dark')
        }
        localStorage.setItem('darkMode', darkMode ? 'true' : 'false')
      } catch {
        setInitials('')
      }
    } else {
      setInitials('')
    }
  })
})
</script>

<template>
  <v-app>
    <RouterView />
  </v-app>
</template>

<style>
body, html {
  margin: 0;
  padding: 0;
}
</style>
