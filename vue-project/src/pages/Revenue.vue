<script setup>
</script>

<template>
 <div id="block">
    <div id="text">
        <h2 id="revenue">Revenues</h2>
    </div>
    <!-- <div id="buttons">
        <div id="add"></div>
        <div id="menu"></div>
    </div> -->
 </div>
</template>

<style scoped>
#block {
    height: 50px;
    margin-right: 30px;
    margin-left: 30px;
    display: flex;
    justify-content: space-between;
    margin-top: 10px;
}
#text {
    /* width: 120px; */
    display: flex;
    justify-content: center;
    align-items: center;
}

#buttons {
    width: 100px;
    background-color: yellow;
}
#revenue {
    font-weight: normal;
}
</style>