<script setup>
import Navbar from './Navbar.vue';
import Revenue from './Revenue.vue';
import { coffeeColor } from '@/variables';
import { ref } from 'vue'
import book1 from '@/data/book1.csv'
import { sort as sortByDate } from '@/functions/functions'
import { useSnackbar } from "vue3-snackbar";
import Charts from './Charts.vue';

const avg_num = ref(2000.64)
let this_list = book1 ?? []
const list = ref(this_list)
let top_padding = 0
let month = 0

const show_divider = (item, index) => {
  if (index == 0) {
    top_padding = 0
    month = item.date.split("/")[0]
    return false
  }

  if (item.date.split("/")[0] != month) {
    month = item.date.split("/")[0]
    top_padding = 0
    return true
  }

  top_padding +=1
  return false
}

const snackbar = useSnackbar();
const sort = () => {
  list.value = sortByDate([...list.value]);
  snackbar.add({
    type: 'success',
    text: 'Your list has been sorted'
})
}

</script>

<template>
  <div id="main">
    <navbar />
    <div id="main_container">
      <div id="left">
        <revenue :sort="sort" />
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
        <div v-for="(item, index) in list">
          <v-divider class="dividers" opacity="0.7" v-show="show_divider(item, index)" id="list_divider" />
          <div id="ind_prices" :class="top_padding > 0 && 'temp_id'">
            <p>{{ item.date }}</p>
            <p>${{ parseFloat(item.price).toLocaleString() }}</p>
          </div>
        </div>
        <div style="padding-bottom: 10px;"></div>
      </div>
      <div id="right">
        <div id="topChart" style="height: 100%; margin-bottom: 30px;">
          <div class="chartContainers" style="margin-right: 40px;">
            <charts :list="list"/>
          </div>
          <div class="chartContainers"></div>
        </div>
        <div style="height: 100%; border: 5px lightcoral solid;"></div>
      </div>
      <vue3-snackbar bottom right :duration="4000"></vue3-snackbar>
    </div>
  </div>

</template>

<style scoped>
.chartContainers{
  background-color: white;
  border-radius: 30px;
  display: flex;
  width: 100%; 
}
#topChart{
  display: flex;
  flex-direction: row;
}
#ind_prices {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  margin-right: 30px;
  margin-left: 30px;
  align-items: center;
}
.temp_id {
  margin-top: 10px;
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
  min-height: 60px;
  align-items: center;
}

.dividers {
  margin-left: 15px;
  margin-right: 15px;
}

#right {
  border: 2px solid black;
  flex-grow: 1;
  display: flex;
  flex-direction: column;
}

#left {
  width: 330px;
  background-color: white;
  margin-right: 80px;
  border-radius: 30px;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow-y: scroll;
  overflow-x: hidden;
  scrollbar-gutter: stable;
}
#left::-webkit-scrollbar {
  width: 8px;
}
#left::-webkit-scrollbar-track {
  background: transparent;
}
#left::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.3);
  border-radius: 4px;
}

#main_container {
  display: flex;
  flex-direction: row;
  flex: 1;
  min-height: 0;
  width: 100%;
  padding: 70px 80px 70px 80px;
  box-sizing: border-box;
}

#main {
  background-color: v-bind(coffeeColor);
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  width: 100%;
}
</style>