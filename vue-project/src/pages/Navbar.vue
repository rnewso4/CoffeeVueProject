<script setup>
import { initials } from '@/functions/functions'
import { coffeeColor } from '@/variables';
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { signOut } from 'firebase/auth';
import { doc, updateDoc } from 'firebase/firestore';
import { auth, db } from '@/firebase';
import { Button, Menu } from 'primevue';
import AddEntry from './AddEntry.vue';

const router = useRouter();

const visible = ref(false);
const setVisible = (bool_val) => {
    visible.value = bool_val;
}

const handleLogout = async () => {
  await signOut(auth);
  router.push('/login');
};


const toggleDarkMode = async () => {
    const currentDark = document.documentElement.classList.contains('my-app-dark');
    document.documentElement.classList.toggle('my-app-dark');
    const newDark = !currentDark;
    localStorage.setItem('darkMode', newDark ? 'true' : 'false');
    const user = auth.currentUser;
    if (user) {
        try {
            await updateDoc(doc(db, 'users', user.uid), { darkMode: newDark });
        } catch (err) {
            console.error('Failed to update darkMode:', err);
        }
    }
};

const isDarkMode = ref(document.documentElement.classList.contains('my-app-dark'));
let darkModeObserver = null;

const navbarBackgroundColor = computed(() => isDarkMode.value ? '#18181b' : '#FFFFFF');

const textColor = computed(() => isDarkMode.value ? '#FFFFFF' : '#000000')

const menu = ref();
const items = ref([
    { label: 'Dark Mode', command: () => toggleDarkMode() },
    { label: 'Log Out', command: () => handleLogout() }
]);

const toggle = (event) => {
    menu.value.toggle(event);
};

onMounted(() => {
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
    <div id="container">
        <div id="logo">
            <div id="circle"></div>
        </div>
        <div id="items">
            <div id="create" class="navItem" @click="visible = true">
                <h2 class="navText">Generate</h2>
            </div>
        </div>
        <div class="card flex justify-center" style="display: flex; align-items: center; justify-content: center; width: 125px;">
        <Button class="initials-button" style="width: 40px; height: 40px;" severity="secondary" type="button" rounded :label="initials" @click="toggle" aria-haspopup="true" aria-controls="overlay_menu" />
        <Menu ref="menu" id="overlay_menu" :model="items" :popup="true" />
        </div>
        <add-entry :visible="visible" :setVisible="setVisible" title="Generate Entry Using AI"/>
    </div>
</template>

<style scoped>
#initials_button{
    display: flex;
    align-items: center;
    justify-content: center;
    width: 125px;
}

.initials-button {
    font-weight: 500 !important;
}

.initials-btn {
    width: 40px !important;
    min-width: 40px !important;
    height: 40px !important;
    padding: 0 !important;
    font-weight: bold;
    background-color: lightgray;
}
.navText {
    font-weight: normal;
    font-size: 1.1rem;
    color: v-bind(textColor);
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

.navItem:hover .navText {
    color: black;
}

#container {
    position: sticky;
    top: 0;
    width: 100%;
    height: 60px;
    display: flex;
    flex-direction: row;
    background-color: v-bind(navbarBackgroundColor);
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