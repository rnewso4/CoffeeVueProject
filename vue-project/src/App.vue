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
        const fullName = userDoc.exists() ? userDoc.data().fullName : ''
        setInitials(fullName || '')
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
