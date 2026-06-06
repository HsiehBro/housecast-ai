<template>
  <div class="charts-view">
    <el-card class="chart-card">
      <template #header>
        <div class="card-header">
          <div class="chart-header">
            <el-icon><DataAnalysis /></el-icon>
            <span>房价趋势图</span>
            <el-tag v-if="trendMethod === 'cagr'" type="warning" size="small">基于历史增长率估算</el-tag>
          </div>
          <el-radio-group v-model="trendYears" size="small" @change="fetchTrend">
            <el-radio-button :value="3">未来3年</el-radio-button>
            <el-radio-button :value="5">未来5年</el-radio-button>
            <el-radio-button :value="10">未来10年</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      <div ref="trendChartRef" class="chart-container" v-loading="trendLoading"></div>
    </el-card>

    <div class="charts-grid">
      <el-card class="chart-card">
        <template #header>
          <div class="card-header">
            <div class="chart-header">
              <el-icon><PieChart /></el-icon>
              <span>区域价格分布</span>
            </div>
          </div>
        </template>
        <div ref="districtChartRef" class="chart-container" v-loading="loading"></div>
      </el-card>

      <el-card class="chart-card">
        <template #header>
          <div class="card-header">
            <div class="chart-header">
              <el-icon><DataLine /></el-icon>
              <span>房型分布</span>
            </div>
          </div>
        </template>
        <div ref="roomChartRef" class="chart-container" v-loading="loading"></div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { DataAnalysis, PieChart, DataLine } from '@element-plus/icons-vue'
import { housesApi, predictionApi } from '@/api'
import type { House, TrendData } from '@/types'

const trendChartRef = ref<HTMLElement>()
const districtChartRef = ref<HTMLElement>()
const roomChartRef = ref<HTMLElement>()

const loading = ref(true)
const trendLoading = ref(false)
const trendYears = ref(3)
const trendMethod = ref<TrendData['method']>('none')

let trendChartInstance: echarts.ECharts | null = null
let districtChartInstance: echarts.ECharts | null = null
let roomChartInstance: echarts.ECharts | null = null

const formatPrice2 = (val: number) => val.toFixed(2)

const fetchTrend = async () => {
  try {
    trendLoading.value = true
    const data = await predictionApi.trend(trendYears.value) as unknown as TrendData
    trendMethod.value = data.method
    initTrendChart(data)
  } catch {
    ElMessage.error('加载趋势数据失败')
  } finally {
    trendLoading.value = false
  }
}

const initTrendChart = (data: TrendData) => {
  if (!trendChartRef.value) return
  if (!trendChartInstance) {
    trendChartInstance = echarts.init(trendChartRef.value)
  }

  const histYears = data.historical.map(p => p.year)
  const histPrices = data.historical.map(p => p.avg_price)
  const predYears = data.predicted.map(p => p.year)
  const predPrices = data.predicted.map(p => p.avg_price)

  // Bridge: overlap the last historical point in predicted series for continuity
  const bridgeYear = histYears.length > 0 ? histYears[histYears.length - 1] : null
  const bridgePrice = histPrices.length > 0 ? histPrices[histPrices.length - 1] : null
  const fullPredYears = bridgeYear != null ? [bridgeYear, ...predYears] : predYears
  const fullPredPrices = bridgePrice != null ? [bridgePrice, ...predPrices] : predPrices

  // All x-axis categories: unique years in order
  const allYearsSet = new Set([...histYears, ...fullPredYears])
  const allYears = [...allYearsSet].sort((a, b) => a - b)

  // Map prices to index positions; null where data doesn't exist
  const histData: (number | null)[] = allYears.map(y => {
    const idx = histYears.indexOf(y)
    return idx >= 0 ? histPrices[idx] : null
  })
  const predData: (number | null)[] = allYears.map(y => {
    const idx = fullPredYears.indexOf(y)
    return idx >= 0 ? fullPredPrices[idx] : null
  })

  trendChartInstance.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: (params: unknown) => {
        const items = (Array.isArray(params) ? params : [params]) as Array<{
          axisValue: number
          marker: string
          seriesName: string
          value: number | null
        }>
        let text = `${items[0].axisValue}年<br/>`
        for (const it of items) {
          if (it.value != null) {
            text += `${it.marker} ${it.seriesName}: ${formatPrice2(it.value)} 元/㎡<br/>`
          }
        }
        return text
      }
    },
    legend: { data: ['历史均价', '预测均价'] },
    xAxis: { type: 'category', data: allYears, boundaryGap: false },
    yAxis: {
      type: 'value',
      name: '单价(元/㎡)',
      axisLabel: { formatter: (val: number) => formatPrice2(val) }
    },
    series: [
      {
        name: '历史均价',
        type: 'line',
        data: histData,
        smooth: true,
        connectNulls: true,
        itemStyle: { color: '#409eff' }
      },
      {
        name: '预测均价',
        type: 'line',
        data: predData,
        smooth: true,
        connectNulls: true,
        lineStyle: { type: 'dashed' },
        itemStyle: { color: '#e6a23c' }
      }
    ]
  }, true)
}

const initDistrictChart = (houses: House[]) => {
  if (!districtChartRef.value) return
  districtChartInstance = echarts.init(districtChartRef.value)

  const districtPrices: Record<string, number[]> = {}
  houses.forEach(h => {
    if (!districtPrices[h.district]) districtPrices[h.district] = []
    districtPrices[h.district].push(parseFloat(h.price_per_sqm))
  })

  const districts = Object.keys(districtPrices)
  const avgPrices = districts.map(d => {
    const prices = districtPrices[d]
    return prices.reduce((sum, p) => sum + p, 0) / prices.length
  })

  districtChartInstance.setOption({
    tooltip: {
      trigger: 'item',
      formatter: (params: unknown) => {
        const p = params as { name: string; value: number; percent: number }
        return `${p.name}<br/>均价: ${formatPrice2(p.value)} 元/㎡ (${p.percent}%)`
      }
    },
    legend: { orient: 'vertical', left: 'left' },
    series: [{
      name: '价格', type: 'pie', radius: '50%',
      data: districts.map((d, i) => ({ value: Math.round(avgPrices[i] * 100) / 100, name: d })),
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0, 0, 0, 0.5)' } }
    }]
  })
}

const initRoomChart = (houses: House[]) => {
  if (!roomChartRef.value) return
  roomChartInstance = echarts.init(roomChartRef.value)

  const roomCounts: Record<number, number> = {}
  houses.forEach(h => { roomCounts[h.rooms] = (roomCounts[h.rooms] || 0) + 1 })

  const rooms = Object.keys(roomCounts).sort()
  const counts = rooms.map(r => roomCounts[Number(r)])

  roomChartInstance.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: rooms.map(r => `${r}室`) },
    yAxis: { type: 'value', name: '数量' },
    series: [{ data: counts, type: 'bar' }]
  })
}

const handleResize = () => {
  trendChartInstance?.resize()
  districtChartInstance?.resize()
  roomChartInstance?.resize()
}

onMounted(async () => {
  try {
    loading.value = true
    const [trendData, housesData] = await Promise.all([
      predictionApi.trend(trendYears.value) as Promise<unknown>,
      housesApi.list({ page: 1, page_size: 200 })
    ])
    const trend = trendData as unknown as TrendData
    const houses: House[] = (housesData as unknown as { results: House[] }).results ?? []

    trendMethod.value = trend.method
    initTrendChart(trend)
    initDistrictChart(houses)
    initRoomChart(houses)
  } catch {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  trendChartInstance?.dispose()
  districtChartInstance?.dispose()
  roomChartInstance?.dispose()
})
</script>

<style scoped>
.charts-view { min-height: 100%; }
.chart-card { margin-bottom: 24px; border: 1px solid #e4e7ed; border-radius: 12px; box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05); }
.card-header { display: flex; align-items: center; justify-content: space-between; padding: 0 16px; }
.chart-header { display: flex; align-items: center; gap: 12px; }
.chart-header .el-icon { font-size: 24px; color: #409eff; }
.chart-container { width: 100%; height: 500px; padding: 20px; background: #fff; border-radius: 8px; }
.charts-grid { display: grid; grid-template-columns: 1fr; gap: 24px; }

@media (min-width: 1200px) { .charts-grid { grid-template-columns: 2fr 1fr; } }
@media (max-width: 768px) { .chart-container { height: 300px; } }
</style>
