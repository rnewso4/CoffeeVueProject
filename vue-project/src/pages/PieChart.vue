<script setup>
import Chart from 'primevue/chart';
import { Card } from 'primevue';

import { ref, onMounted, onUnmounted, computed, watch } from "vue";
import { top_revenues, backgroundColors, darkBackgroundColors } from '@/functions/functions';

const props = defineProps(['list'])

// In Vue 3.3+, refs passed as props are passed through (not unwrapped).
// props.list may be a ref object — use .value to get the array.
const listData = computed(() => props.list?.value ?? props.list ?? [])

const items_length = 5

const isDarkMode = ref(document.documentElement.classList.contains('my-app-dark'));
let darkModeObserver = null;

onMounted(() => {
    chartData.value = setChartData();
    chartOptions.value = setChartOptions();

    darkModeObserver = new MutationObserver(() => {
        isDarkMode.value = document.documentElement.classList.contains('my-app-dark');
    });
    darkModeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
});

onUnmounted(() => {
    darkModeObserver?.disconnect();
});

watch(isDarkMode, () => {
    chartData.value = setChartData();
    chartOptions.value = setChartOptions();
});

watch(listData, () => {
    chartData.value = setChartData();
}, { deep: true });

const chartData = ref();
const chartOptions = ref();

const setChartData = () => {
    const isDark = document.documentElement.classList.contains('my-app-dark');
    const colors = isDark ? darkBackgroundColors : backgroundColors;
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
        datasets.backgroundColor.push(colors[i]),
        datasets.borderColor.push(colors[i]);
    }
    return {
        labels: labels,
        datasets: [datasets]
    };
};

const setChartOptions = () => {
    const documentStyle = getComputedStyle(document.documentElement);
    const isDark = document.documentElement.classList.contains('my-app-dark');
    const textColor = isDark ? '#ffffff' : documentStyle.getPropertyValue('--p-text-color');

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
    <Card style="height: 100%; width: 100%;">
        <template #content>
            <Chart type="pie" :data="chartData" :options="chartOptions" id="centerChart"/>
        </template>
    </Card>
</template>

<style scoped>
#centerChart {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    padding: 5px;
    width: 100%;
}
:deep(.p-card-content) {
    display: flex;
    height: 100%;
    width: 100%;
}

:deep(.p-card-body) {
    height: 100%;
}
</style>