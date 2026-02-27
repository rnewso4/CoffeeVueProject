<script setup>
import RevMenu from './RevMenu.vue';
import { Dialog, InputText, Button, FloatLabel } from 'primevue';
import { ref } from 'vue';
import { zodResolver } from '@primevue/forms/resolvers/zod';
import { useToast } from "primevue/usetoast";
import { z } from 'zod';
import { Form } from '@primevue/forms';
import Toast from 'primevue/toast';


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

const onFormSubmit = ({ valid, values }) => {
    if (valid) {
        console.log(values)
        toast.add({ severity: 'success', summary: 'Form is submitted.', life: 3000 });
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
    { field: 'price', header: 'Price' },
    { field: 'customers', header: 'Customers' },
    { field: 'avg_order_val', header: 'Average Order Value' },
];

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
                                    <InputText id="on_label" :name="item.field" />
                                    <label for="on_label">{{ item.header }}</label>
                                </FloatLabel>
                            </div>
                        </div>
                        <div style="display: flex; flex-direction: column;">
                            <div v-for="item of items2" class="flex items-center" style="padding: 10px;">
                                <FloatLabel variant="on">
                                    <InputText id="on_label" :name="item.field" />
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