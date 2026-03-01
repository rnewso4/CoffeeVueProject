<script setup>
    import { ref } from 'vue'
    import { useRouter } from 'vue-router'
    import { createUserWithEmailAndPassword } from 'firebase/auth'
    import { collection, doc, setDoc, serverTimestamp } from 'firebase/firestore'
    import { auth, db } from '@/firebase'
    import { coffeeColor } from '@/variables'
    import { setInitials } from '@/functions/functions'

    const router = useRouter()

    const rules = {
        required: value => !!value || 'Required.',
        min: v => v.length >= 8 || 'Min 8 characters',
        emailMatch: () => (`The email and password you entered don't match`),
        email: value => {
        const pattern = /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/
        return pattern.test(value) || 'Invalid e-mail.'
        }
    }

    const show1 = ref(false)
    const password = ref('')
    const email = ref('')
    const fullName = ref('')
    const loading = ref(false)
    const errorMessage = ref('')

    const onSubmit = async () => {
        if (!email.value || !password.value) return
        loading.value = true
        errorMessage.value = ''
        try {
            const userCredential = await createUserWithEmailAndPassword(auth, email.value, password.value)
            const user = userCredential.user

            await setDoc(doc(db, 'users', user.uid), {
                email: user.email,
                fullName: fullName.value || '',
                darkMode: false,
                createdAt: serverTimestamp()
            })

            // Create blank entries subcollection for this user
            const entriesRef = collection(doc(db, 'users', user.uid), 'entries')
            await setDoc(doc(entriesRef, '_init'), {
                _placeholder: true,
                date: serverTimestamp()
            })

            setInitials(fullName.value || "")

            router.push('/home')
        } catch (err) {
            let code = ''
            if (err && typeof err === 'object' && 'code' in err) {
                code = err.code
            }
            if (code === 'auth/invalid-credential' || code === 'auth/wrong-password' || code === 'auth/user-not-found') {
                errorMessage.value = 'Invalid email or password.'
            } else {
                errorMessage.value = err && err.message ? err.message : 'Login failed.'
            }
        } finally {
            loading.value = false
        }
    }
</script>
<template>
    <div id="main">
        <div id="container">
            <h2 id="header">Create an Account</h2>
            <v-form @submit.prevent="onSubmit">
                <div class="items"><v-text-field label="Full Name" v-model="fullName" prepend-icon="mdi-account" variant="solo-filled"></v-text-field></div>
                <div class="items"><v-text-field 
                    label="Email" 
                    v-model="email"
                    prepend-icon="mdi-email" 
                    variant="solo-filled"
                    :rules="[rules.required, rules.email]"
                ></v-text-field></div>
                <div class="items"><v-text-field
                    prepend-icon="mdi-lock"
                    v-model="password"
                    :append-inner-icon="show1 ? 'mdi-eye' : 'mdi-eye-off'"
                    :rules="[rules.required, rules.min]"
                    :type="show1 ? 'text' : 'password'"
                    hint="At least 8 characters"
                    label="Password"
                    name="input-10-1"
                    counter
                    variant="solo-filled"
                    @click:append-inner="show1 = !show1"
                ></v-text-field></div>
                <div class="items" v-if="errorMessage">
                    <v-alert type="error" density="compact" closable>{{ errorMessage }}</v-alert>
                </div>
                <div id="buttondiv"><v-btn type="submit" color="#933D00" width="100%" class="font-weight-bold" :loading="loading" :disabled="loading">Sign Up</v-btn></div>
                <div id="login">
                    <p style="margin-right: 5px;">Already have an account?</p>
                    <div><v-btn type="button" variant="text" density="compact" color="#933D00" width="16px" class="font-weight-bold" to="/login">Login</v-btn></div>
                </div>
            </v-form>
        </div>
    </div>
</template>
<style scoped>
@font-face {
    font-family: 'Carter One';
    src: url('@/assets/fonts/CarterOne.ttf') format('truetype');
    font-weight: normal;
    font-style: normal;
}
#login {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    margin-top: 40px;
    margin-bottom: 10PX;
}
#buttondiv {
    margin: 30px 0 30px 0;/*TRBL */
}
#header {
    font-family: 'Carter One', sans-serif;
    font-weight: normal;
    font-size: 1.5rem;
    margin-bottom: 30px;
    padding-left: 5px;
}
#main {
    background-color: v-bind(coffeeColor);
    height: 100%;
    width: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
}
#container {
    background-color: #FFF;
    height: 70%;
    min-height: fit-content;
    min-width: 315px;
    width: 30%;
    max-width: 500px;
    border-radius: 60px;
    justify-content: center;
    align-items: center;
    padding: 50px 30px 5px 30px;/*TRBL */
}
#container .items {
    margin-bottom: 5px;
}
</style>