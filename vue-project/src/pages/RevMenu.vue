<script setup>
import { ref } from 'vue';

const props = defineProps(['sort', 'setDialogVisible'])

const items = ref([
    { title: 'Sort', onClick: props.sort },
    { title: 'Filter', onClick: () => {console.log("clicked")}},
    { title: 'View Table', onClick: () => props.setDialogVisible(true) }
]);
</script>

<template>
    <div>
        <v-menu>
            <template v-slot:activator="{ props }">
                <v-btn icon="mdi-dots-vertical" variant="text" width="20px" v-bind="props"></v-btn>
            </template>
            <v-list>
                <v-list-item v-for="(item, index) in items" :key="index" :value="index">
                    <v-list-item-title @click="item.onClick">{{ item.title }}</v-list-item-title>
                </v-list-item>
            </v-list>
        </v-menu>
    </div>
</template>

<style scoped></style>