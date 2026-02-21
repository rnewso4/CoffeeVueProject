<script setup>
import Navbar from './Navbar.vue';
import { coffeeColor } from '@/variables';
</script>

<template>
  <div>
    <navbar />
    <div id="temp">
      <h1>Home</h1>
    </div>
  </div>
</template>

<style scoped>
#temp{
  background-color: v-bind(coffeeColor);
  height: 120vh;
  width: 100%;
}
</style>