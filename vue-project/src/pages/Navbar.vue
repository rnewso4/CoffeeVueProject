<script setup>
import { initials } from '@/functions/functions'
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { signOut } from 'firebase/auth';
import { auth } from '@/firebase';

const router = useRouter();

const handleLogout = async () => {
  await signOut(auth);
  router.push('/login');
};


const toggleDarkMode = () => {
    document.documentElement.classList.toggle('my-app-dark');
}


const items = ref([
    { title: 'Dark Mode', onClick: toggleDarkMode},
    { title: 'Log Out', onClick: handleLogout }
]);
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
        <v-menu>
            <template v-slot:activator="{ props }">
                <div id="initials_button">
                <v-btn variant="tonal" rounded="circle" class="initials-btn" v-bind="props">{{initials}}</v-btn>
                </div>
            </template>
            <v-list>
                <v-list-item v-for="(item, index) in items" :key="index" :value="index">
                    <v-list-item-title @click="item.onClick">{{ item.title }}</v-list-item-title>
                </v-list-item>
            </v-list>
        </v-menu>
    </div>
</template>

<style scoped>
#initials_button{
    display: flex;
    align-items: center;
    justify-content: center;
    width: 125px;
}

.initials-btn {
    width: 40px !important;
    min-width: 40px !important;
    height: 40px !important;
    padding: 0 !important;
    font-weight: bold;
}
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

#container {
    position: sticky;
    top: 0;
    width: 100%;
    height: 60px;
    display: flex;
    flex-direction: row;
    background-color: white;
}

#logo {
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

#circle {
    height: 40px;
    width: 40px;
    background-color: #bbb;
    border-radius: 50%;
    display: flex;
    justify-content: center;
    align-items: center;
}
</style>