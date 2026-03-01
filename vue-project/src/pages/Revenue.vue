<script setup>
import RevMenu from './RevMenu.vue';
import { Dialog, InputText, Button, FloatLabel } from 'primevue';
import { ref } from 'vue';
import { zodResolver } from '@primevue/forms/resolvers/zod';
import { useToast } from "primevue/usetoast";
import { z } from 'zod';
import { Form } from '@primevue/forms';
import Toast from 'primevue/toast';
import DatePicker from 'primevue/datepicker';
import InputNumber from 'primevue/inputnumber';
import { collection, doc, addDoc, Timestamp } from 'firebase/firestore';
import { db, auth } from '@/firebase';


const props = defineProps(['sort', 'setDialogVisible'])
const visible = ref(false);

const toast = useToast();
const initialValues = ref({
    username: '',
    email: ''
});

// const resolver = ref(zodResolver(
//     z.object({
//         username: z.string().min(1, { message: 'Username is required.' }),
//         email: z.string().min(1, { message: 'Email is required.' }).email({ message: 'Invalid email address.' })
//     })
// ));

const resolver = ({ values }) => {
    const errors = {};

    // if (!values.username) {
    //     errors.username = [{ message: 'Username is required.' }];
    // }

    return {
        values, // (Optional) Used to pass current form values to submit event.
        errors
    };
};

const onFormSubmit = async ({ valid, values }) => {
    if (valid) {
        const user = auth.currentUser;
        if (!user) {
            toast.add({ severity: 'warn', summary: 'Not signed in.', detail: 'Sign in to add entries.', life: 5000 });
            return;
        }
        try {
            const docData = {
                hours: values.hours ?? null,
                employees: values.employees ?? null,
                spend: values.spend ?? null,
                foot_traffic: values.foot_traffic ?? null,
                date: values.date ? Timestamp.fromDate(values.date instanceof Date ? values.date : new Date(values.date)) : null,
                price: values.price ?? null,
                customers: values.customers ?? null,
                avg_order_val: values.avg_order_val ?? null,
            };
            const entriesRef = collection(doc(db, 'users', user.uid), 'entries');
            await addDoc(entriesRef, docData);
            toast.add({ severity: 'success', summary: 'Form is submitted.', life: 3000 });
            visible.value = false;
            setTimeout(() => window.location.reload(), 800);
        } catch (err) {
            console.error('Firebase save error:', err);
            toast.add({ severity: 'error', summary: 'Save failed.', detail: err?.message ?? 'Could not save to Firebase.', life: 5000 });
        }
    }
};

const items = [
    { field: 'hours', header: 'Operating Hours' },
    { field: 'employees', header: 'Number of Employees' },
    { field: 'spend', header: 'Daily Spend' },
    { field: 'foot_traffic', header: 'Location Foot Traffic' },
];

const items2 = [
    { field: 'date', header: 'Date' },
    { field: 'price', header: 'Daily Revenue' },
    { field: 'customers', header: 'Customers' },
    { field: 'avg_order_val', header: 'Average Order Value' },
];

const integerField = (field) => {
    if (field === "hours" || field === "employees" || field === "foot_traffic" || field === "customers") return true
    return false;
}

const floatField = (field) => {
    if (field === "spend" || field === "price" || field === "avg_order_val") return true;
    return false;
}

const maxForField = (field) => {
    if (field === 'hours') return 23;
    return Number.MAX_SAFE_INTEGER;
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
            <Dialog v-model:visible="visible" modal header="Create Entry"
                :style="{ width: 'fit-content', maxWidth: '90vw' }">
                <Form v-slot="$form" :resolver="resolver" :initialValues="initialValues" @submit="onFormSubmit"
                    class="flex flex-col gap-4 w-full sm:w-56">
                    <div style="display: flex; width: 100%; flex-direction: row;">
                        <div style="display: flex; flex-direction: column;">
                            <div v-for="item of items" class="flex items-center" style="padding: 10px;">
                                <FloatLabel variant="on">
                                    <InputNumber id="on_label" :name="item.field" inputId="minmaxfraction" :minFractionDigits="2" :maxFractionDigits="2" fluid v-if="floatField(item.field)"/>
                                    <InputNumber id="on_label" :name="item.field" inputId="integeronly" fluid v-if="integerField(item.field)" :min="1" :max="maxForField(item.field)"/>
                                    <label for="on_label">{{ item.header }}</label>
                                </FloatLabel>
                            </div>
                        </div>
                        <div style="display: flex; flex-direction: column;">
                            <div v-for="item of items2" class="flex items-center" style="padding: 10px;">
                                <FloatLabel variant="on">
                                    <InputNumber id="on_label" :name="item.field" inputId="minmaxfraction" :minFractionDigits="2" :maxFractionDigits="2" fluid v-if="floatField(item.field)"/>
                                    <InputNumber id="on_label" :name="item.field" inputId="integeronly" fluid v-if="integerField(item.field)" :min="1"/>
                                    <DatePicker name="date" fluid v-if="item.field === 'date'"/>
                                    <label for="on_label">{{ item.header }}</label>
                                </FloatLabel>
                            </div>
                        </div>
                    </div>
                    <div class="flex justify-end gap-2" id="bottomButtons">
                        <Button type="button" label="Cancel" severity="secondary" @click="visible = false"></Button>
                        <Button type="submit" label="Save" severity="contrast"></Button>
                    </div>
                </Form>
                <Toast position="bottom-right"/>
            </Dialog>
        </div>
    </div>
</template>

<style scoped>
#bottomButtons {
    margin-top: 10px;
    display: flex;
    align-items: flex-end;
    justify-content: center;
    gap: 10px;
}

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