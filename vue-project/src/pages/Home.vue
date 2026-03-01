<script setup>
import Navbar from './Navbar.vue';
import { coffeeColor } from '@/variables';
import { ref, onMounted, onUnmounted, computed } from 'vue'
import book1 from '@/data/book1.csv'
import { getAverage, sort as sortByDate } from '@/functions/functions'
import { useSnackbar } from "vue3-snackbar";
import BarChart from './BarChart.vue';
import PieChart from './PieChart.vue';
import DataTable from './DataTable.vue';
import { Card } from 'primevue';
import Revenue from './Revenue.vue';
import { auth, db } from '@/firebase';
import { onAuthStateChanged } from 'firebase/auth';
import { collection, doc, writeBatch, getDocs, query, orderBy } from 'firebase/firestore';

function normalizeEntry(entry) {
  const date = entry.date;
  let dateStr = '';
  if (date && typeof date === 'string') {
    dateStr = date;
  } else if (date && typeof date.toDate === 'function') {
    const d = date.toDate();
    dateStr = `${d.getMonth() + 1}/${d.getDate()}/${d.getFullYear()}`;
  }
  const price = entry.price != null ? Number(entry.price) : 0;
  return { ...entry, date: dateStr, price };
}

const avg_num = ref(0)
const list = ref([])
let top_padding = 0
let month = 0
const snackbar = useSnackbar();
const CACHE_KEY_PREFIX = 'coffee-entries-';

function getCacheKey(uid) {
  return `${CACHE_KEY_PREFIX}${uid}`;
}

function readEntriesFromCache(uid) {
  try {
    const raw = localStorage.getItem(getCacheKey(uid));
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

function writeEntriesToCache(uid, entries) {
  try {
    localStorage.setItem(getCacheKey(uid), JSON.stringify(entries));
  } catch (e) {
    console.warn('Failed to write entries cache:', e);
  }
}


async function loadEntriesFromFirebase() {
  const user = auth.currentUser;
  if (!user) {
    list.value = [];
    avg_num.value = 0;
    return;
  }
  // Use cache immediately so refresh doesn't require waiting for Firestore
  const cached = readEntriesFromCache(user.uid);
  if (cached && cached.length >= 0) {
    list.value = [...cached];
    avg_num.value = getAverage([...list.value]);
  }
  try {
    const entriesRef = collection(doc(db, 'users', user.uid), 'entries');
    const q = query(entriesRef, orderBy('date', 'desc'));
    const snapshot = await getDocs(q);
    const entries = snapshot.docs
      .filter((d) => d.id !== '_init' && !d.data()._placeholder)
      .map((d) => normalizeEntry({ id: d.id, ...d.data() }));
    list.value = [...entries];
    console.log(list.value)
    avg_num.value = getAverage([...list.value]);
    writeEntriesToCache(user.uid, list.value);
  } catch (e) {
    if (!cached) {
      snackbar.add({ type: 'error', text: 'Failed to load entries.' });
      list.value = [];
      avg_num.value = 0;
    }
    // If we had cache, keep showing it; only clear on error when there was no cache
  }
  if (list.value.length < 1) {
    let this_list = book1 ?? []
    list.value = sortByDate(this_list)
    avg_num.value = getAverage([...list.value])
  }
}

const sendListToFirebase = async () => {
  const user = auth.currentUser;
  if (!user) {
    snackbar.add({ type: 'error', text: 'You must be signed in to sync to Firebase.' });
    return;
  }
  const entries = list.value ?? [];
  if (entries.length === 0) {
    snackbar.add({ type: 'info', text: 'No entries to send.' });
    return;
  }
  const BATCH_SIZE = 500;
  const entriesRef = collection(doc(db, 'users', user.uid), 'entries');
  try {
    for (let i = 0; i < entries.length; i += BATCH_SIZE) {
      const batch = writeBatch(db);
      const chunk = entries.slice(i, i + BATCH_SIZE);
      for (const entry of chunk) {
        const docRef = doc(entriesRef);
        const { id, ...data } = entry;
        batch.set(docRef, data);
      }
      await batch.commit();
    }
    snackbar.add({ type: 'success', text: 'Sending complete' });
  } catch (e) {
    console.error('Firebase sync failed:', e);
    snackbar.add({ type: 'error', text: 'Failed to send entries. Try again.' });
  }
}

const show_divider = (item, index) => {
  const dateStr = item?.date;
  if (index == 0) {
    top_padding = 0
    month = typeof dateStr === 'string' ? dateStr.split("/")[0] : ''
    return false
  }

  if (typeof dateStr !== 'string') return false
  if (dateStr.split("/")[0] != month) {
    month = dateStr.split("/")[0]
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

const sort = () => {
  snackbar.add({
    type: 'success',
    text: 'Your list has been sorted'
  })
}

const setDialogVisible = (val) => {
  dialogVisible.value = val
}

onMounted(() => {
  darkModeObserver = new MutationObserver(() => {
    isDarkMode.value = document.documentElement.classList.contains('my-app-dark');
  });
  darkModeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });

  onAuthStateChanged(auth, (user) => {
    loadEntriesFromFirebase();
  });
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
                    <p>${{ (typeof item.price === 'number' ? item.price : parseFloat(item.price) || 0).toLocaleString()
                      }}</p>
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