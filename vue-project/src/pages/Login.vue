<script setup>
    import { ref } from 'vue'
    import { useRouter } from 'vue-router'
    import { signInWithEmailAndPassword } from 'firebase/auth'
    import { auth } from '@/firebase'

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
    const loading = ref(false)
    const errorMessage = ref('')

    const onSubmit = async () => {
        if (!email.value || !password.value) return
        loading.value = true
        errorMessage.value = ''
        try {
            await signInWithEmailAndPassword(auth, email.value, password.value)
            router.push('/')
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
    <div id="login">
        <div id="left">
            <h1 id="welcome" class="items">Weclome Back!</h1>
            <v-form @submit.prevent="onSubmit" style="width: 100%;">
                <div class="items" id="additionalpadding"><v-text-field 
                    label="Email" 
                    v-model="email"
                    prepend-icon="mdi-email" 
                    variant="solo-filled"
                    :rules="[rules.required, rules.email]"
                ></v-text-field></div>
                <div class="items" id="additionalpadding"><v-text-field
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
                <div id="forgot"><v-btn variant="text" density="compact" width="174px">Forgot Password?</v-btn></div>
                <div class="items" id="additionalpadding" v-if="errorMessage">
                    <v-alert type="error" density="compact" closable>{{ errorMessage }}</v-alert>
                </div>
                <div class="items" id="additionalpadding"><v-btn color="#933D00" width="100%" class="font-weight-bold" type="submit" style="margin-top: 70px;" :loading="loading" :disabled="loading">Login</v-btn></div>
                <div id="signup">
                    <p style="margin-right: 5px;">Don't have an account?</p>
                    <div><v-btn type="button" variant="text" density="compact" color="#933D00" width="20px" class="font-weight-bold" to="/register">Sign Up</v-btn></div>
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

#signup {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    margin-top: 20px;
}

#forgot{
    justify-content: flex-end;
    width: 100%;
    display: flex;
    padding-left: 10%;
    padding-right: 10%;
}
#additionalpadding{
    padding-left: 10%;
    padding-right: 10%;
}
#welcome {
    font-family: 'Carter One', sans-serif;
    text-align: center;
    margin-bottom: 50px;
}
#login {
    min-height: 100vh;
    display: grid;
    grid-template-columns: 1fr 1fr;
}
#left {
    background-color: #FFF4E6;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding-left: 5%;
    padding-right: 5%;
}
#left .items {
    width: 100%;
    justify-content: center;
    display: flex;
}
#right {
    background-color: #FFF;
    display: flex;
}
</style>