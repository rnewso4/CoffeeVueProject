<script setup>
import Navbar from './Navbar.vue';
import Revenue from './Revenue.vue';
import { coffeeColor } from '@/variables';
import { ref } from 'vue'

const avg_num = ref(2000.64)
let this_list = [{ date: "2/20/23", price: 2000.48 }, { date: "2/21/23", price: 2220.48 }, { date: "1/20/23", price: 2110.48 }]
const list = ref(this_list)
let top_padding = 0
let first = true
let boolll = true

let month = this_list[0].date.split("/")[0]
let show_divider = (item) => {
  if (item.date.split("/")[0] != month) {
    month = item.date.split("/")[0]
    top_padding = 0
    return true
  }
  if (first) first = false;
  else top_padding +=1
  return false
}


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
            <p class="pText">${{ avg_num.toLocaleString() }}</p>
          </div>
        </div>
        <v-divider class="dividers" opacity="0.7" id="avg_divider"/>
        <div v-for="item in list">
          <v-divider class="dividers" opacity="0.7" v-show="show_divider(item)" id="list_divider" />
          <div id="ind_prices">
            <p>{{ item.date }}</p>
            <p :id="top_padding > 0 && 'temp_id'">${{ item.price.toLocaleString() }}</p>
          </div>
        </div>
      </div>
      <div id="right"></div>
    </div>
  </div>
</template>

<style scoped>
#ind_prices {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  margin-right: 30px;
  margin-left: 30px;
  align-items: center;
}
#temp_id {
  padding-top: 10px;
}
#list_divider {
  margin-bottom: 18px;
  margin-top: 18px;
}
#avg_divider {
  margin-bottom: 18px;
}

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