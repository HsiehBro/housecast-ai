<template>
  <div class="map-view">
    <el-card class="map-card">
      <template #header>
        <div class="card-header">
          <div class="map-header">
            <el-icon><Location /></el-icon>
            <span>地图展示</span>
          </div>
          <div class="layer-toggle">
            <el-checkbox v-model="showHeatmap" @change="updateLayers">热力图</el-checkbox>
            <el-checkbox v-model="showMarkers" @change="updateLayers">房源标记</el-checkbox>
          </div>
        </div>
      </template>

      <!-- Filter bar -->
      <el-form :model="filters" inline class="filter-bar">
        <el-form-item label="区域">
          <el-select v-model="filters.district" placeholder="全部" clearable style="width: 130px">
            <el-option v-for="d in districtList" :key="d" :label="d" :value="d" />
          </el-select>
        </el-form-item>

        <el-form-item label="总价(万)">
          <el-input-number
            v-model="filters.minPrice"
            :min="0" :step="10" :precision="0"
            controls-position="right"
            placeholder="最低"
            style="width: 110px"
          />
          <span class="range-sep">—</span>
          <el-input-number
            v-model="filters.maxPrice"
            :min="0" :step="10" :precision="0"
            controls-position="right"
            placeholder="最高"
            style="width: 110px"
          />
        </el-form-item>

        <el-form-item label="房型">
          <el-select v-model="filters.rooms" placeholder="全部" clearable style="width: 90px">
            <el-option :value="1" label="1室" />
            <el-option :value="2" label="2室" />
            <el-option :value="3" label="3室" />
            <el-option :value="4" label="4室" />
          </el-select>
        </el-form-item>

        <el-form-item label="面积(㎡)">
          <el-input-number
            v-model="filters.minArea"
            :min="0" :step="10" :precision="0"
            controls-position="right"
            placeholder="最小"
            style="width: 100px"
          />
          <span class="range-sep">—</span>
          <el-input-number
            v-model="filters.maxArea"
            :min="0" :step="10" :precision="0"
            controls-position="right"
            placeholder="最大"
            style="width: 100px"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="applyFilters" :loading="loading">筛选</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- Map -->
      <div id="map-container" class="map-container" v-loading="loading"></div>

      <!-- Stats -->
      <div class="stats-bar" v-if="houses.length > 0">
        <span>共 <strong>{{ houses.length }}</strong> 套房源</span>
        <span>均价 <strong>{{ avgPricePerSqm }}</strong> 元/㎡</span>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Location } from '@element-plus/icons-vue'
import { housesApi } from '@/api'
import type { MapHouse, MapHouseParams } from '@/types'

declare global {
  interface Window {
    AMap: {
      Map: new (container: string, options: Record<string, unknown>) => AMapInstance
      Marker: new (options: Record<string, unknown>) => AMapMarker
      InfoWindow: new (options: Record<string, unknown>) => AMapInfoWindow
      Pixel: new (x: number, y: number) => unknown
      HeatMap: new (map: AMapInstance, options: Record<string, unknown>) => AMapHeatMap
    }
  }
}

interface AMapInstance {
  add: (overlay: unknown) => void
  remove: (overlay: unknown) => void
  destroy: () => void
  setZoomAndCenter: (zoom: number, center: [number, number]) => void
  getCenter: () => { getLng: () => number; getLat: () => number }
}

interface AMapMarker {
  on: (event: string, callback: () => void) => void
  getPosition: () => unknown
}

interface AMapInfoWindow {
  open: (map: AMapInstance, position: unknown) => void
  close: () => void
  setContent: (content: string) => void
}

interface AMapHeatMap {
  setDataSet: (data: { data: Array<{ lng: number; lat: number; count: number }> }) => void
  show: () => void
  hide: () => void
}

const GAOLING_CENTER: [number, number] = [109.09, 34.53]
const GAOLING_ZOOM = 13

const districtList = [
  '泾渭街道', '鹿苑街道', '崇皇街道', '渭水片区', '通远街道', '耿镇街道'
]

const mapInstance = ref<AMapInstance | null>(null)
const markers = ref<AMapMarker[]>([])
const heatmap = ref<AMapHeatMap | null>(null)
const infoWindow = ref<AMapInfoWindow | null>(null)
const loading = ref(false)
const houses = ref<MapHouse[]>([])

const showHeatmap = ref(false)
const showMarkers = ref(true)

const filters = reactive({
  district: '' as string,
  minPrice: undefined as number | undefined,
  maxPrice: undefined as number | undefined,
  rooms: undefined as number | undefined,
  minArea: undefined as number | undefined,
  maxArea: undefined as number | undefined,
})

const avgPricePerSqm = computed(() => {
  if (houses.value.length === 0) return '—'
  const sum = houses.value.reduce((acc, h) => acc + parseFloat(h.price_per_sqm), 0)
  return (sum / houses.value.length).toFixed(0)
})

const formatPrice = (price: number) =>
  new Intl.NumberFormat('zh-CN', {
    style: 'currency', currency: 'CNY',
    minimumFractionDigits: 0, maximumFractionDigits: 0
  }).format(price)

const loadMapScript = (): Promise<void> => {
  return new Promise((resolve, reject) => {
    if (window.AMap) {
      resolve()
      return
    }

    const key = import.meta.env.VITE_AMAP_KEY || ''

    // Set security config for JS API 2.0 — route through Vite proxy
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    ;(window as any)._AMapSecurityConfig = {
      serviceHost: '/_AMapService',
    }

    const script = document.createElement('script')
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${key}&plugin=AMap.HeatMap`
    script.async = true
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('地图加载失败'))
    document.head.appendChild(script)
  })
}

const buildInfoContent = (house: MapHouse) => `
  <div class="info-card">
    <div class="info-title">${house.name || house.district}</div>
    <div class="info-row"><span>区域</span><span>${house.district}</span></div>
    <div class="info-row"><span>面积</span><span>${house.area}㎡</span></div>
    <div class="info-row"><span>房型</span><span>${house.rooms}室</span></div>
    <div class="info-row"><span>楼层</span><span>${house.floor}层</span></div>
    <div class="info-row"><span>年份</span><span>${house.year}年</span></div>
    <div class="info-row"><span>总价</span><span>${formatPrice(parseFloat(house.price))}</span></div>
    <div class="info-row"><span>单价</span><span>${parseFloat(house.price_per_sqm).toFixed(0)} 元/㎡</span></div>
  </div>
`

const clearMarkers = () => {
  markers.value.forEach(m => mapInstance.value?.remove(m))
  markers.value = []
}

const clearOverlays = () => {
  clearMarkers()
  heatmap.value?.hide()
}

const addMarkersToMap = (data: MapHouse[]) => {
  if (!window.AMap || !mapInstance.value) return
  clearMarkers()

  const iw = infoWindow.value

  data.forEach(house => {
    if (house.lat == null || house.lng == null) return

    const marker = new window.AMap.Marker({
      position: [house.lng, house.lat],
      offset: new window.AMap.Pixel(-6, -6),
      content: '<div class="house-dot"></div>',
    })

    marker.on('click', () => {
      if (iw) {
        iw.setContent(buildInfoContent(house))
        iw.open(mapInstance.value!, marker.getPosition())
      }
    })

    mapInstance.value!.add(marker)
    markers.value.push(marker)
  })
}

const addHeatmapToMap = (data: MapHouse[]) => {
  if (!window.AMap || !mapInstance.value || !window.AMap.HeatMap) return

  if (!heatmap.value) {
    heatmap.value = new window.AMap.HeatMap(mapInstance.value, {
      radius: 30,
      opacity: [0, 0.8],
      gradient: {
        0.2: '#1e90ff',
        0.5: '#00bfff',
        0.7: '#ffdd00',
        0.9: '#ff6600',
        1.0: '#ff0000',
      },
    })
  }

  const heatData = data
    .filter(h => h.lat != null && h.lng != null)
    .map(h => ({ lng: h.lng!, lat: h.lat!, count: 1 }))

  heatmap.value.setDataSet({ data: heatData })
  if (showHeatmap.value) {
    heatmap.value.show()
  } else {
    heatmap.value.hide()
  }
}

const updateLayers = () => {
  if (showHeatmap.value) {
    heatmap.value?.show()
  } else {
    heatmap.value?.hide()
  }

  if (showMarkers.value && houses.value.length > 0) {
    addMarkersToMap(houses.value)
  } else {
    clearMarkers()
  }
}

const fetchHouses = async (params?: MapHouseParams) => {
  loading.value = true
  try {
    const data = await housesApi.mapList(params) as unknown as MapHouse[]
    houses.value = data

    infoWindow.value?.close()
    addMarkersToMap(data)
    addHeatmapToMap(data)

    if (data.length === 0) {
      ElMessage.info('没有符合条件的房源')
    }
  } catch {
    ElMessage.error('加载房源数据失败')
  } finally {
    loading.value = false
  }
}

const applyFilters = () => {
  const params: MapHouseParams = {}
  if (filters.district) params.district = filters.district
  if (filters.rooms) params.rooms = filters.rooms
  if (filters.minPrice) params.min_price = filters.minPrice * 10000
  if (filters.maxPrice) params.max_price = filters.maxPrice * 10000
  if (filters.minArea) params.min_area = filters.minArea
  if (filters.maxArea) params.max_area = filters.maxArea
  fetchHouses(params)
}

const resetFilters = () => {
  filters.district = ''
  filters.minPrice = undefined
  filters.maxPrice = undefined
  filters.rooms = undefined
  filters.minArea = undefined
  filters.maxArea = undefined
  fetchHouses()
}

onMounted(async () => {
  try {
    await loadMapScript()
    mapInstance.value = new window.AMap.Map('map-container', {
      zoom: GAOLING_ZOOM,
      center: GAOLING_CENTER,
    })
    infoWindow.value = new window.AMap.InfoWindow({
      offset: new window.AMap.Pixel(0, -20),
      closeWhenClickMap: true,
    })
    fetchHouses()
  } catch {
    ElMessage.error('地图加载失败，请检查网络连接')
  }
})

onUnmounted(() => {
  clearOverlays()
  if (mapInstance.value) {
    mapInstance.value.destroy()
    mapInstance.value = null
  }
})
</script>

<style scoped>
.map-view { min-height: 100%; }
.map-card { margin-bottom: 24px; border: 1px solid #e4e7ed; border-radius: 12px; box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05); }
.card-header { display: flex; align-items: center; justify-content: space-between; padding: 0 16px; }
.map-header { display: flex; align-items: center; gap: 12px; }
.map-header .el-icon { font-size: 24px; color: #409eff; }
.layer-toggle { display: flex; gap: 16px; }

.filter-bar {
  padding: 12px 16px 0;
  margin-bottom: 12px;
  border-bottom: 1px solid #ebeef5;
}
.filter-bar :deep(.el-form-item) { margin-bottom: 12px; }
.range-sep { margin: 0 4px; color: #c0c4cc; }

.map-container { width: 100%; height: 600px; border-radius: 8px; border: 2px solid #e4e7ed; overflow: hidden; }

.stats-bar {
  display: flex; gap: 24px; justify-content: center;
  padding: 12px 0; color: #606266; font-size: 14px;
}
.stats-bar strong { color: #409eff; }

/* Marker dot */
:deep(.house-dot) {
  width: 12px; height: 12px; border-radius: 50%;
  background: #409eff; border: 2px solid #fff;
  box-shadow: 0 0 4px rgba(64, 158, 255, 0.6);
  cursor: pointer; transition: transform 0.15s;
}
:deep(.house-dot:hover) { transform: scale(1.4); }

/* Info window */
:deep(.info-card) { padding: 12px 16px; min-width: 200px; font-size: 14px; }
:deep(.info-title) { font-weight: 600; font-size: 16px; color: #303133; margin-bottom: 8px; border-bottom: 1px solid #ebeef5; padding-bottom: 8px; }
:deep(.info-row) { display: flex; justify-content: space-between; padding: 3px 0; color: #606266; }
:deep(.info-row span:last-child) { color: #303133; font-weight: 500; }

@media (max-width: 768px) {
  .map-container { height: 400px; }
  .filter-bar :deep(.el-form-item) { margin-right: 0; }
  .card-header { flex-direction: column; gap: 8px; align-items: flex-start; }
}
</style>
