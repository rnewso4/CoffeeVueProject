<script setup>
import Navbar from './Navbar.vue';
import Revenue from './Revenue.vue';
import { coffeeColor } from '@/variables';
import { ref } from 'vue'


</script>

<template>
  <div id="main">
    <navbar />
    <div id="main_container">
      <div id="left">
        <revenue />
        <v-divider class="dividers" opacity="0.7" />
        <div id="average">
          <div>
            <p class="pText">Average</p>
          </div>
          <div>
            <p class="pText">$2,000.64</p>
          </div>
        </div>
        <v-divider class="dividers" opacity="0.7" />
      </div>
      <div id="right"></div>
    </div>
  </div>
</template>

<style scoped>
.pText {
  font-weight: bolder;
}
#average {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  margin-right: 30px;
  margin-left: 30px;
  height: 60px;
  align-items: center;
}

.dividers {
  margin-left: 15px;
  margin-right: 15px;
}

#right {
  background-color: brown;
  flex-grow: 1;
}

#left {
  width: 330px;
  background-color: white;
  margin-right: 80px;
  border-radius: 30px;
  display: flex;
  flex-direction: column;
}

#main_container {
  display: flex;
  flex-direction: row;
  flex: 1;
  width: 100%;
  padding: 70px 80px 70px 80px;
  box-sizing: border-box;
}

#main {
  background-color: v-bind(coffeeColor);
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  width: 100%;
}
</style>