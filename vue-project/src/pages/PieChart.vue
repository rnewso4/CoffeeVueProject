<script setup>
import Chart from 'primevue/chart';

import { ref, onMounted, computed } from "vue";
import { top_revenues, backgroundColors } from '@/functions/functions';

const props = defineProps(['list'])

// In Vue 3.3+, refs passed as props are passed through (not unwrapped).
// props.list may be a ref object — use .value to get the array.
const listData = computed(() => props.list?.value ?? props.list ?? [])

const items_length = 5

onMounted(() => {
    chartData.value = setChartData();
    chartOptions.value = setChartOptions();
});

const chartData = ref();
const chartOptions = ref();

const setChartData = () => {
    let datasets = {
        label: "Revenue",
        data: [],
        backgroundColor: [],
        borderColor: [],
        borderWidth: 1
    }
    let labels = []
    const this_list = top_revenues([...listData.value], items_length);
    for (let i = 0; i < this_list.length; i++) {
        labels.push(this_list[i].date)
        datasets.data.push(this_list[i].price)
        datasets.backgroundColor.push(backgroundColors[i]),
        datasets.borderColor.push(backgroundColors[i]);
    }
    return {
        labels: labels,
        datasets: [datasets]
    };
};

const setChartOptions = () => {
    const documentStyle = getComputedStyle(document.documentElement);
    const textColor = documentStyle.getPropertyValue('--p-text-color');

    return {
        maintainAspectRatio: false,
        plugins: {
            tooltip: {
                callbacks: {
                    label: (context) => `${context.label}: $${context.parsed.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                }
            },
            title: {
                display: true,
                text: 'Top Daily Revenue Values',
                color: textColor,
                // font: {
                //     size: 16
                // }
            },
            legend: {
                labels: {
                    color: textColor
                }
            }
        },
    };
}
</script>


<template>
    <div style="display: flex; flex-direction: column; width: 100%;">
        <Chart type="pie" :data="chartData" :options="chartOptions" id="centerChart"/>
    </div>
</template>

<style scoped>
#centerChart {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    padding: 5px;
}
</style>