<template>
  <div class="dashboard">
    <!-- 统计卡片区域 -->
    <div class="stats-section">
      <div class="stats-grid">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon revenue">
              <el-icon size="24"><Money /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ formatNumber(totalHouses) }}</div>
              <div class="stat-label">总房源数</div>
            </div>
          </div>
        </el-card>

        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon price">
              <el-icon size="24"><PriceTag /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ formatPrice(avgPrice) }}</div>
              <div class="stat-label">平均房价</div>
            </div>
          </div>
        </el-card>

        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon prediction">
              <el-icon size="24"><DataLine /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ districtCount }}</div>
              <div class="stat-label">覆盖区域</div>
            </div>
          </div>
        </el-card>

        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon accuracy">
              <el-icon size="24"><TrendCharts /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ formatPrice(avgPricePerSqm) }}/㎡</div>
              <div class="stat-label">平均单价</div>
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-section">
      <el-row :gutter="24">
        <el-col :xs="24" :md="16">
          <el-card class="chart-card">
            <template #header>
              <div class="card-header">
                <h3>房价趋势图
                  <el-tag v-if="trendMethod === 'cagr'" type="warning" size="small" style="margin-left: 8px">基于历史增长率估算</el-tag>
                </h3>
                <el-radio-group v-model="trendYears" size="small" @change="fetchTrend">
                  <el-radio-button :value="3">未来3年</el-radio-button>
                  <el-radio-button :value="5">未来5年</el-radio-button>
                  <el-radio-button :value="10">未来10年</el-radio-button>
                </el-radio-group>
              </div>
            </template>
            <div ref="trendChartRef" class="chart-container" v-loading="trendLoading"></div>
          </el-card>
        </el-col>

        <el-col :xs="24" :md="8">
          <el-card class="chart-card">
            <template #header>
              <div class="card-header">
                <h3>房型分布</h3>
              </div>
            </template>
            <div ref="roomTypeChartRef" class="chart-container" v-loading="loading"></div>
          </el-card>
        </el-col>
      </el-row>

      <el-card class="chart-card">
        <template #header>
          <div class="card-header">
            <h3>区域价格对比</h3>
          </div>
        </template>
        <div ref="districtChartRef" class="chart-container large" v-loading="loading"></div>
      </el-card>
    </div>

    <!-- 最新房源列表 -->
    <div class="latest-section" v-if="recentHouses.length > 0">
      <el-card class="list-card">
        <template #header>
          <div class="card-header">
            <h3>最新房源</h3>
            <router-link to="/houses">
              <el-button type="primary" link>查看全部</el-button>
            </router-link>
          </div>
        </template>

        <el-table :data="recentHouses" stripe style="width: 100%">
          <el-table-column label="房源信息" min-width="200">
            <template #default="{ row }">
              <div class="house-name">{{ row.name }}</div>
              <div class="house-location">{{ row.district }}</div>
            </template>
          </el-table-column>

          <el-table-column prop="area" label="面积" width="100">
            <template #default="{ row }">
              {{ row.area }}㎡
            </template>
          </el-table-column>

          <el-table-column prop="rooms" label="房型" width="100">
            <template #default="{ row }">
              {{ row.rooms }}室{{ row.halls }}厅
            </template>
          </el-table-column>

          <el-table-column prop="price" label="价格" width="150">
            <template #default="{ row }">
              {{ formatPrice(parseFloat(row.price)) }}
            </template>
          </el-table-column>

          <el-table-column prop="year" label="年份" width="80">
            <template #default="{ row }">
              {{ row.year }}
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 空状态 -->
    <el-empty v-if="!loading && totalHouses === 0" description="暂无房源数据" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { Money, PriceTag, DataLine, TrendCharts } from '@element-plus/icons-vue'
import { housesApi, predictionApi } from '@/api'
import type { House, TrendData } from '@/types'

const loading = ref(true)
const trendLoading = ref(false)
const houses = ref<House[]>([])
const trendYears = ref(3)
const trendMethod = ref<TrendData['method']>('none')

const trendChartRef = ref<HTMLElement>()
const roomTypeChartRef = ref<HTMLElement>()
const districtChartRef = ref<HTMLElement>()

let trendChartInstance: echarts.ECharts | null = null
let roomTypeChartInstance: echarts.ECharts | null = null
let districtChartInstance: echarts.ECharts | null = null

const totalHouses = computed(() => houses.value.length)

const avgPrice = computed(() => {
  if (houses.value.length === 0) return 0
  const sum = houses.value.reduce((acc, h) => acc + parseFloat(h.price), 0)
  return Math.round(sum / houses.value.length)
})

const avgPricePerSqm = computed(() => {
  if (houses.value.length === 0) return 0
  const sum = houses.value.reduce((acc, h) => acc + parseFloat(h.price_per_sqm), 0)
  return Math.round(sum / houses.value.length)
})

const districtCount = computed(() => {
  return new Set(houses.value.map(h => h.district)).size
})

const recentHouses = computed(() => {
  return [...houses.value]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 10)
})

const formatNumber = (num: number) => new Intl.NumberFormat('zh-CN').format(num)

const formatPrice = (price: number) =>
  new Intl.NumberFormat('zh-CN', {
    style: 'currency', currency: 'CNY',
    minimumFractionDigits: 0, maximumFractionDigits: 0
  }).format(price)

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

  const allYearsSet = new Set([...histYears, ...fullPredYears])
  const allYears = [...allYearsSet].sort((a, b) => a - b)

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
        areaStyle: { opacity: 0.15 },
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

const initRoomTypeChart = () => {
  if (!roomTypeChartRef.value) return
  roomTypeChartInstance = echarts.init(roomTypeChartRef.value)
  const roomCounts: Record<number, number> = {}
  houses.value.forEach(h => { roomCounts[h.rooms] = (roomCounts[h.rooms] || 0) + 1 })
  const data = Object.entries(roomCounts).map(([k, v]) => ({ value: v, name: `${k}室` }))

  roomTypeChartInstance.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    series: [{
      type: 'pie', radius: '50%', data,
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0, 0, 0, 0.5)' } }
    }]
  })
}

const initDistrictChart = () => {
  if (!districtChartRef.value) return
  districtChartInstance = echarts.init(districtChartRef.value)
  const districtPrices: Record<string, number[]> = {}
  houses.value.forEach(h => {
    if (!districtPrices[h.district]) districtPrices[h.district] = []
    districtPrices[h.district].push(parseFloat(h.price_per_sqm))
  })
  const districts = Object.keys(districtPrices)
  const avgPrices = districts.map(d => {
    const prices = districtPrices[d]
    return Math.round(prices.reduce((a, b) => a + b, 0) / prices.length * 100) / 100
  })

  districtChartInstance.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: (params: unknown) => {
        const items = (Array.isArray(params) ? params : [params]) as Array<{
          axisValue: string
          marker: string
          value: number
        }>
        let text = `${items[0].axisValue}<br/>`
        for (const it of items) {
          text += `${it.marker} 均价: ${formatPrice2(it.value)} 元/㎡<br/>`
        }
        return text
      }
    },
    xAxis: { type: 'category', data: districts },
    yAxis: {
      type: 'value',
      name: '均价(元/㎡)',
      axisLabel: { formatter: (val: number) => formatPrice2(val) }
    },
    series: [{ data: avgPrices, type: 'bar' }]
  })
}

const handleResize = () => {
  trendChartInstance?.resize()
  roomTypeChartInstance?.resize()
  districtChartInstance?.resize()
}

onMounted(async () => {
  try {
    loading.value = true
    const [housesData, trendData] = await Promise.all([
      housesApi.list({ page: 1, page_size: 200 }) as Promise<unknown>,
      predictionApi.trend(trendYears.value) as Promise<unknown>
    ])
    houses.value = (housesData as unknown as { results: House[] }).results
    await nextTick()
    const trend = trendData as unknown as TrendData
    trendMethod.value = trend.method
    initTrendChart(trend)
    initRoomTypeChart()
    initDistrictChart()
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
  roomTypeChartInstance?.dispose()
  districtChartInstance?.dispose()
})
</script>

<style scoped>
.dashboard { min-height: 100%; }

.stats-section { margin-bottom: 24px; }
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
}

.stat-card { border: none; border-radius: 12px; transition: all 0.3s; }
.stat-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1); }
.stat-content { display: flex; align-items: center; gap: 16px; }
.stat-icon {
  width: 56px; height: 56px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center; color: white;
}
.stat-icon.revenue { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.stat-icon.price { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
.stat-icon.prediction { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
.stat-icon.accuracy { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
.stat-info { flex: 1; }
.stat-value { font-size: 28px; font-weight: bold; color: #303133; line-height: 1.2; }
.stat-label { font-size: 14px; color: #909399; margin-bottom: 8px; }

.charts-section { margin-bottom: 24px; }
.chart-card { border: none; border-radius: 12px; margin-bottom: 24px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.card-header h3 { margin: 0; font-size: 16px; font-weight: 600; color: #303133; }
.chart-container { height: 300px; position: relative; }
.chart-container.large { height: 400px; }

.latest-section { margin-bottom: 24px; }
.list-card { border: none; border-radius: 12px; }
.house-name { font-weight: 500; color: #303133; margin-bottom: 4px; }
.house-location { font-size: 12px; color: #909399; }

@media (max-width: 768px) {
  .stats-grid { grid-template-columns: 1fr; gap: 16px; }
  .chart-container { height: 250px; }
  .chart-container.large { height: 300px; }
}
</style>
