<script setup>
import { ref } from 'vue';
import { Button, Menu } from 'primevue';
import 'primeicons/primeicons.css'

const props = defineProps(['sort', 'setDialogVisible'])

const menu = ref();
const items = ref([
    { label: 'Sort', command: () => props.sort() },
    { label: 'Filter', command: () => console.log("clicked") },
    { label: 'View Table', command: () => props.setDialogVisible(true) }
]);

const toggle = (event) => {
    menu.value.toggle(event);
};
</script>

<template>
    <div class="card flex justify-center">
        <Button style="width: 20px;" severity="contrast" type="button" variant="text" icon="pi pi-ellipsis-v" @click="toggle" aria-haspopup="true" aria-controls="overlay_menu" />
        <Menu ref="menu" id="overlay_menu" :model="items" :popup="true" />
    </div>
</template>

<style scoped>

</style>