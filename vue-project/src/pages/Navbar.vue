<script setup>
    import { initials } from '@/functions/functions'
</script>

<template>
    <div id="container">
        <div id="logo">
            <div id="circle"></div>
        </div>
        <div id="items">
            <div id="create" class="navItem">
                <h2 class="navText">Create</h2>
            </div>
            <div id="list" class="navItem">
                <h2 class="navText">List</h2>
            </div>
            <div id="filter" class="navItem">
                <h2 class="navText">Filter</h2>
            </div>
        </div>
        <div id="profile">
            <div id="circle">
                <h1 id="initials">{{ initials || 'JD' }}</h1>
            </div>
        </div>
    </div>
</template>

<style scoped>
.navText {
    font-weight: normal;
    font-size: 1.1rem;
}
#create:hover {
    background-color: lightgrey;
}
#list:hover {
    background-color: lightgrey;
}
#filter:hover {
    background-color: lightgrey;
}
.navItem {
    width: 100px;
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
}
.navItem:hover {
    cursor: pointer;
    transition: background-color 0.3s ease-in-out;
}
#initials {
    font-size: 1.1rem;
    text-align: center;
}
#container{
    position: sticky;
    top: 0;
    width: 100%;
    height: 60px;
    display: flex;
    flex-direction: row;
    background-color: white;
}
#logo{
    width: 125px;
    justify-content: center;
    align-items: center;
    display: flex;
}
#items {
    flex-grow: 3;
    flex-direction: row;
    display: flex;
    justify-content: center;
    align-items: center;
}
#profile {
    justify-content: center;
    align-items: center;
    width: 125px;
    display: flex;
}
#circle {
  height: 40px;
  width: 40px;
  background-color: #bbb; /* or any color */
  border-radius: 50%; /* This is the key property */
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>