<script setup>
import { Form } from '@primevue/forms';
import { Dialog, FloatLabel, InputNumber, DatePicker, Button, Toast } from 'primevue';
import { zodResolver } from '@primevue/forms/resolvers/zod';
import { useToast } from "primevue/usetoast";
import { z } from 'zod';
import { collection, doc, addDoc, Timestamp } from 'firebase/firestore';
import { db, auth } from '@/firebase';
import { ref } from 'vue';

const toast = useToast();

const props = defineProps(['visible', 'setVisible', 'title'])

// Form values for Generate button and Save (API order: customers, avg_order_val, hours, employees, spend, foot_traffic)
const formValues = ref({
    hours: null,
    employees: null,
    spend: null,
    foot_traffic: null,
    date: null,
    price: null,
    customers: null,
    avg_order_val: null
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
        const v = formValues.value;
        try {
            const docData = {
                hours: v.hours ?? null,
                employees: v.employees ?? null,
                spend: v.spend ?? null,
                foot_traffic: v.foot_traffic ?? null,
                date: v.date ? Timestamp.fromDate(v.date instanceof Date ? v.date : new Date(v.date)) : null,
                price: v.price ?? null,
                customers: v.customers ?? null,
                avg_order_val: v.avg_order_val ?? null,
            };
            const entriesRef = collection(doc(db, 'users', user.uid), 'entries');
            await addDoc(entriesRef, docData);
            toast.add({ severity: 'success', summary: 'Form is submitted.', life: 3000 });
            props.setVisible(false)
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

const showGenerate = () => {
    if (props.title === "Create Entry") return false;
    return true;
}

const generate = async () => {
    const v = formValues.value;
    const customers = v.customers ?? 0;
    const avg_order_val = v.avg_order_val ?? 0;
    const hours = v.hours ?? 0;
    const employees = v.employees ?? 0;
    const spend = v.spend ?? 0;
    const foot_traffic = v.foot_traffic ?? 0;

    const apiBase = import.meta.env.VITE_API_URL || 'http://54.205.33.101:5000';
    const url = `${apiBase}/api/data/${customers}/${avg_order_val}/${hours}/${employees}/${spend}/${foot_traffic}/`;
    console.log(url);

    try {
        toast.add({ severity: 'info', summary: 'Generating...', detail: 'Calling server...', life: 2000 });
        const res = await fetch(url, { method: 'GET' });
        if (!res.ok) throw new Error(`Server error: ${res.status}`);
        const data = await res.json();
        toast.add({
            severity: 'success',
            summary: 'Generated revenue',
            detail: typeof data === 'object' ? JSON.stringify(data) : String(data),
            life: 8000
        });
    } catch (err) {
        console.error('Generate error:', err);
        toast.add({
            severity: 'error',
            summary: 'Generate failed',
            detail: err?.message ?? 'Could not reach server.',
            life: 6000
        });
    }
};
</script>

<template>
    <Dialog v-model:visible="props.visible" modal :header="props.title" :style="{ width: 'fit-content', maxWidth: '90vw' }"
        @update:visible="(v) => props.setVisible(v)">
        <Form v-slot="$form" :resolver="resolver" :initialValues="formValues" @submit="onFormSubmit"
            class="flex flex-col gap-4 w-full sm:w-56">
            <div style="display: flex; width: 100%; flex-direction: row;">
                <div style="display: flex; flex-direction: column;">
                    <div v-for="item of items" class="flex items-center" style="padding: 10px;">
                        <FloatLabel variant="on">
                            <InputNumber id="on_label" :name="item.field" inputId="minmaxfraction"
                                :minFractionDigits="2" :maxFractionDigits="2" fluid v-if="floatField(item.field)"
                                v-model="formValues[item.field]" />
                            <InputNumber id="on_label" :name="item.field" inputId="integeronly" fluid
                                v-if="integerField(item.field)" :min="1" :max="maxForField(item.field)"
                                v-model="formValues[item.field]" />
                            <label for="on_label">{{ item.header }}</label>
                        </FloatLabel>
                    </div>
                </div>
                <div style="display: flex; flex-direction: column;">
                    <div v-for="item of items2" class="flex items-center" style="padding: 10px;">
                        <FloatLabel variant="on">
                            <InputNumber id="on_label" :name="item.field" inputId="minmaxfraction"
                                :minFractionDigits="2" :maxFractionDigits="2" fluid v-if="floatField(item.field)"
                                v-model="formValues[item.field]" />
                            <InputNumber id="on_label" :name="item.field" inputId="integeronly" fluid
                                v-if="integerField(item.field)" :min="1"
                                v-model="formValues[item.field]" />
                            <DatePicker name="date" fluid v-if="item.field === 'date'" v-model="formValues.date" />
                            <label for="on_label">{{ item.header }}</label>
                        </FloatLabel>
                    </div>
                </div>
            </div>
            <div class="flex justify-end gap-2" id="bottomButtons">
                <div style="display: flex; width: 100%;" v-if="showGenerate()">
                    <Button type="button" label="Generate" severity="primary" @click="generate()"></Button>
                </div>
                <div id="leftButtons">
                    <Button type="button" label="Cancel" severity="secondary" @click="props.setVisible(false)"></Button>
                    <Button type="submit" label="Save" severity="contrast"></Button>
                </div>
            </div>
        </Form>
        <Toast position="bottom-right" />
    </Dialog>
</template>

<style scoped>
#bottomButtons {
    margin-top: 10px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
#leftButtons {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 10px;
    width: 100%;
}
</style>