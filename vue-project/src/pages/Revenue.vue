<script setup>
import RevMenu from './RevMenu.vue';
import { Dialog, InputText, Button } from 'primevue';
import { ref } from 'vue';

const props = defineProps(['sort', 'setDialogVisible'])
const visible = ref(false);

const addFunc = () => {
    console.log("Add clicked")
}
</script>

<template>
    <div id="block">
        <div id="text">
            <h2 id="revenue">Revenues</h2>
        </div>
        <div id="add">
            <v-btn prepend-icon="mdi-plus-circle" variant="text" color="#CF761E" class="add-btn"
                @click="visible = true">Add</v-btn>
            <rev-menu :sort="props.sort" :setDialogVisible="props.setDialogVisible" />
            <Dialog v-model:visible="visible" modal header="Edit Profile" :style="{ width: '25rem' }">
                <span class="text-surface-500 dark:text-surface-400 block mb-8">Update your information.</span>
                <div class="flex items-center gap-4 mb-4">
                    <label for="username" class="font-semibold w-24">Username</label>
                    <InputText id="username" class="flex-auto" autocomplete="off" />
                </div>
                <div class="flex items-center gap-4 mb-8">
                    <label for="email" class="font-semibold w-24">Email</label>
                    <InputText id="email" class="flex-auto" autocomplete="off" />
                </div>
                <div class="flex justify-end gap-2">
                    <Button type="button" label="Cancel" severity="secondary" @click="visible = false"></Button>
                    <Button type="button" label="Save" @click="visible = false"></Button>
                </div>
            </Dialog>
        </div>
    </div>
</template>

<style scoped>
.add-btn {
    font-weight: bold;
    height: 100%;
}

#add {
    display: flex;
    align-items: center;
    justify-content: center;
}

#block {
    min-height: 50px;
    margin-right: 30px;
    margin-left: 30px;
    display: flex;
    justify-content: space-between;
}

#text {
    display: flex;
    justify-content: center;
    align-items: center;
}

#revenue {
    font-weight: normal;
}
</style>