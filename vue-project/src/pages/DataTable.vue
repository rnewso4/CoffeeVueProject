<script setup>
import { computed, ref } from 'vue';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import { Button, Dialog } from 'primevue';

const props = defineProps(['list', 'dialogVisible', 'setDialogVisible'])

// In Vue 3.3+, refs passed as props are passed through (not unwrapped).
// props.list may be a ref object — use .value to get the array.
const listData = computed(() => props.list?.value ?? props.list ?? [])


const columns = [
    { field: 'date', header: 'Date' },
    { field: 'price', header: 'Price' },
    { field: 'customers', header: 'Customers' },
    { field: 'avg_order_val', header: 'Average Order Value' },
    { field: 'hours', header: 'Operating Hours' },
    { field: 'employees', header: 'Number of Employees' },
    { field: 'spend', header: 'Daily Spend' },
    { field: 'foot_traffic', header: 'Location Foot Traffic' },
];
</script>

<template>
    <Dialog :visible="props.dialogVisible" @update:visible="(v) => props.setDialogVisible(v)" header="Revenue Table"
        :style="{ width: '75vw' }" maximizable modal :contentStyle="{ height: '60%' }">
        <DataTable :value="listData" scrollable scrollHeight="flex" tableStyle="min-width: 50rem" paginator :rows="5"
            :rowsPerPageOptions="[5, 10, 20, 50]">
            <Column v-for="col of columns" :key="col.field" :field="col.field" :header="col.header" sortable>
                <template v-if="col.field === 'price'" #body="{ data }">
                    ${{ parseFloat(data.price).toLocaleString(undefined, {
                        minimumFractionDigits: 2,
                    maximumFractionDigits: 2 }) }}
                </template>
            </Column>
        </DataTable>
    </Dialog>

</template>

<style scoped></style>