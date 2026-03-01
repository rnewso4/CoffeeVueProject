<script setup>
import Chart from 'primevue/chart';
import Card from 'primevue/card';

import { ref, onMounted, onUnmounted, computed, watch } from "vue";
import { monthly_revenue, backgroundColors, darkBackgroundColors } from '@/functions/functions';

const props = defineProps(['list'])

// In Vue 3.3+, refs passed as props are passed through (not unwrapped).
// props.list may be a ref object — use .value to get the array.
const listData = computed(() => props.list?.value ?? props.list ?? [])

const num_of_columns = 5

const m_rev = computed(() => monthly_revenue([...listData.value], num_of_columns))

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

watch(m_rev, () => {
    chartData.value = setChartData();
}, { deep: true });

const chartData = ref();
const chartOptions = ref();

const setChartData = () => {
    const isDark = document.documentElement.classList.contains('my-app-dark');
    const colors = isDark ? darkBackgroundColors : backgroundColors;
    let palette = [...colors]
    palette.reverse()
    let datasets = {
        label: "Revenue",
        data: [],
        backgroundColor: [],
        borderColor: [],
        borderWidth: 1
    }
    let labels = []
    for (let i = 0; i < m_rev.value.length; i++) {
        labels.push(m_rev.value[i].label)
        datasets.data.push(m_rev.value[i].price)
        datasets.backgroundColor.push(palette[i]),
        datasets.borderColor.push(palette[i]);
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
    const textColorSecondary = isDark ? '#ffffff' : documentStyle.getPropertyValue('--p-text-muted-color');
    const surfaceBorder = documentStyle.getPropertyValue('--p-content-border-color');

    return {
        maintainAspectRatio: false,
        plugins: {
            title: {
                display: true,
                text: 'Monthly Revenue Values',
                color: textColor,
                // font: {
                //     size: 16
                // }
            },
            legend: {
                display: false,
                labels: {
                    color: textColor
                }
            },
            tooltip: {
                callbacks: {
                    label: (context) => `${context.label}: $${context.parsed.y.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                }
            },
        },
        scales: {
            x: {
                ticks: {
                    color: textColorSecondary
                },
                grid: {
                    display: false
                }
            },
            y: {
                display: false,
                beginAtZero: true,
                ticks: {
                    color: textColorSecondary,
                    callback: (value) => '$' + value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
                },
                grid: {
                    color: surfaceBorder
                }
            }
        }
    };
}
</script>


<template>
    <Card style="height: 100%; width: 100%;">
        <template #content>
            <Chart type="bar" :data="chartData" :options="chartOptions" id="centerChart"/>
        </template>
    </Card>
</template>

<style scoped>
:deep(.p-card-content) {
    display: flex;
    height: 100%;
    width: 100%;
}

:deep(.p-card-body) {
    height: 100%;
}

#centerChart {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    padding: 5px;
    width: 100%;
}
</style>