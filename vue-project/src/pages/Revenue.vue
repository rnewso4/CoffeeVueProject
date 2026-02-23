<script setup>
import RevMenu from './RevMenu.vue';

const props = defineProps(['sort'])

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
        <v-btn prepend-icon="mdi-plus-circle" variant="text" color="#CF761E" class="add-btn" density="comfortable" @click="addFunc">Add</v-btn>
        <rev-menu :sort="props.sort"/>
    </div>
 </div>
</template>

<style scoped>
.add-btn {
    font-weight: bold;
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
    margin-top: 10px;
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