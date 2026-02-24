<script setup>
import Chart from 'primevue/chart';

import { ref, onMounted, computed } from "vue";
import { monthly_revenue, backgroundColors } from '@/functions/functions';

const props = defineProps(['list'])

// In Vue 3.3+, refs passed as props are passed through (not unwrapped).
// props.list may be a ref object — use .value to get the array.
const listData = computed(() => props.list?.value ?? props.list ?? [])

const num_of_columns = 3

const m_rev = monthly_revenue([...listData.value], num_of_columns)

console.log(m_rev)

onMounted(() => {
    chartData.value = setChartData();
    chartOptions.value = setChartOptions();
});

const chartData = ref();
const chartOptions = ref();

const setChartData = () => {
    let palette = [...backgroundColors]
    palette.reverse()
    let datasets = {
        label: "Revenue",
        data: [],
        backgroundColor: [],
        borderColor: [],
        borderWidth: 1
    }
    let labels = []
    for (let i = 0; i < m_rev.length; i++) {
        labels.push(m_rev[i].label)
        datasets.data.push(m_rev[i].price)
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
    const textColor = documentStyle.getPropertyValue('--p-text-color');
    const textColorSecondary = documentStyle.getPropertyValue('--p-text-muted-color');
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
                    label: (context) => `${context.label}: $${context.parsed.y.toFixed(2).toLocaleString()}`
                }
            },
        },
        scales: {
            x: {
                ticks: {
                    color: textColorSecondary
                },
                grid: {
                    color: surfaceBorder
                }
            },
            y: {
                display: false,
                beginAtZero: true,
                ticks: {
                    color: textColorSecondary,
                    callback: (value) => '$' + value.toLocaleString()
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
    <div style="display: flex; flex-direction: column; width: 100%;">
        <Chart type="bar" :data="chartData" :options="chartOptions" id="centerChart"/>
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