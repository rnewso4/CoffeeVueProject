<script setup>
import Navbar from './Navbar.vue';
import { coffeeColor } from '@/variables';
import { ref, onMounted, onUnmounted, computed } from 'vue'
import book1 from '@/data/book1.csv'
import { sort as sortByDate, getAverage } from '@/functions/functions'
import { useSnackbar } from "vue3-snackbar";
import BarChart from './BarChart.vue';
import PieChart from './PieChart.vue';
import DataTable from './DataTable.vue';
import { Card } from 'primevue';
import Revenue from './Revenue.vue';

const avg_num = ref(0)
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

  top_padding += 1
  return false
}

const dialogVisible = ref(false);

const isDarkMode = ref(document.documentElement.classList.contains('my-app-dark'));
let darkModeObserver = null;

const mainBackgroundColor = computed(() => isDarkMode.value ? '#29292C' : coffeeColor);

const snackbar = useSnackbar();
const sort = () => {
  list.value = sortByDate([...list.value]);
  snackbar.add({
    type: 'success',
    text: 'Your list has been sorted'
  })
}

const setDialogVisible = (val) => {
  dialogVisible.value = val
  console.log("setting ref")
}

onMounted(() => {
  list.value = sortByDate([...list.value])
  avg_num.value = getAverage([...list.value])

  darkModeObserver = new MutationObserver(() => {
    isDarkMode.value = document.documentElement.classList.contains('my-app-dark');
  });
  darkModeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
});

onUnmounted(() => {
  darkModeObserver?.disconnect();
});

</script>

<template>
  <div id="main">
    <navbar />
    <div id="main_container">
      <div id="left">
        <Card style="flex: 1; min-height: 0; width: 100%;">
          <template #content>
          <div id="card_content">
          <revenue :sort="sort" :setDialogVisible="setDialogVisible" />
          <v-divider class="dividers" opacity="0.7" />
          <div id="average">
            <div>
              <p class="pText">Average</p>
            </div>
            <div>
              <p class="pText">${{ avg_num.toLocaleString() }}</p>
            </div>
          </div>
          <v-divider class="dividers" opacity="0.7" id="avg_divider" />
          <div id="scrollable_items">
            <div v-for="(item, index) in list">
              <v-divider class="dividers" opacity="0.7" v-show="show_divider(item, index)" id="list_divider" />
              <div id="ind_prices" :class="top_padding > 0 && 'temp_id'">
                <p>{{ item.date }}</p>
                <p>${{ parseFloat(item.price).toLocaleString() }}</p>
              </div>
            </div>
          </div>
          <div style="padding-bottom: 10px;"></div>
          <data-table :list="list" :dialogVisible="dialogVisible" :setDialogVisible="setDialogVisible" />
          </div>
          </template>
        </Card>
      </div>
      <div id="right">
        <div id="topChart" style="height: 100%; margin-bottom: 30px;">
          <bar-chart :list="list" />
        </div>
        <div style="height: 100%; display: flex; width: 100%;">
          <pie-chart :list="list" v-show="true" />
        </div>
      </div>
      <vue3-snackbar bottom right :duration="4000"></vue3-snackbar>
    </div>
  </div>

</template>

<style scoped>
:deep(.p-card) {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

:deep(.p-card-body),
:deep(.p-card-content) {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

#card_content {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

#scrollable_items {
  flex: 1;
  overflow-y: scroll;
  overflow-x: hidden;
  scrollbar-gutter: stable;
  min-height: 0;
}

/* Force scrollbar to always be visible */
#scrollable_items::-webkit-scrollbar {
  width: 8px;
}

#scrollable_items::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

#topChart {
  display: flex;
  max-height: 300px;
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
  flex-grow: 1;
  display: flex;
  flex-direction: column;
}

#left {
  width: 370px;
  min-height: 0;
  margin-right: 40px;
  display: flex;
  flex-direction: column;
}

#main_container {
  display: flex;
  flex-direction: row;
  flex: 1;
  min-height: 0;
  width: 100%;
  padding: 30px 40px 30px 40px;
  box-sizing: border-box;
}

#main {
  background-color: v-bind(mainBackgroundColor);
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  width: 100%;
}
</style>