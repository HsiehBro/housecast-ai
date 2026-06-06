<template>
  <div class="houses-view">
    <!-- 筛选工具栏 -->
    <el-card class="filter-card">
      <el-form :model="filters" inline>
        <el-form-item label="区域">
          <el-select v-model="filters.district" @change="onFilterChange" style="width: fit-content; min-width: 120px">
            <el-option
              v-for="d in districtList"
              :key="d"
              :label="d"
              :value="d"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="排序">
          <el-select v-model="filters.ordering" @change="onFilterChange" style="width: fit-content; min-width: 100px">
            <el-option label="价格升序" value="price" />
            <el-option label="价格降序" value="-price" />
            <el-option label="面积升序" value="area" />
            <el-option label="面积降序" value="-area" />
            <el-option label="最新" value="-created_at" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 数据表格 -->
    <el-card class="table-card">
      <div class="table-header">
        <h3>房源列表</h3>
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>
          新增房源
        </el-button>
      </div>

      <el-table
        :data="housesStore.houses"
        stripe
        style="width: 100%"
        v-loading="housesStore.loading"
      >
        <el-table-column prop="name" label="小区名称" min-width="150" />
        <el-table-column prop="district" label="区域" width="120" />
        <el-table-column prop="area" label="面积" width="100">
          <template #default="{ row }">{{ row.area }}㎡</template>
        </el-table-column>
        <el-table-column label="房型" width="120">
          <template #default="{ row }">{{ row.rooms }}室{{ row.halls }}厅{{ row.bathrooms }}卫</template>
        </el-table-column>
        <el-table-column label="楼层" width="120">
          <template #default="{ row }">{{ row.floor }}/{{ row.total_floors }}层</template>
        </el-table-column>
        <el-table-column prop="year" label="年份" width="80" />
        <el-table-column label="单价" width="130">
          <template #default="{ row }">{{ formatPrice(parseFloat(row.price_per_sqm)) }}/㎡</template>
        </el-table-column>
        <el-table-column label="总价" width="150">
          <template #default="{ row }">{{ formatPrice(parseFloat(row.price)) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button size="small" type="primary" @click="handleEdit(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页器 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="housesStore.currentPage"
          v-model:page-size="housesStore.pageSize"
          :total="housesStore.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="housesStore.setPageSize"
          @current-change="housesStore.setPage"
        />
      </div>
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑房源' : '新增房源'"
      width="800px"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="120px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="小区名称" prop="name">
              <el-input v-model="formData.name" placeholder="请输入小区名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="区域" prop="district">
              <el-select v-model="formData.district" placeholder="请选择区域">
                <el-option v-for="d in districtList" :key="d" :label="d" :value="d" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="面积(㎡)" prop="area">
              <el-input-number v-model="formData.area" :min="1" :max="1000" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="房间数" prop="rooms">
              <el-input-number v-model="formData.rooms" :min="1" :max="10" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="厅数" prop="halls">
              <el-input-number v-model="formData.halls" :min="0" :max="5" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="卫生间" prop="bathrooms">
              <el-input-number v-model="formData.bathrooms" :min="1" :max="10" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="所在楼层" prop="floor">
              <el-input-number v-model="formData.floor" :min="1" :max="100" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="总楼层" prop="total_floors">
              <el-input-number v-model="formData.total_floors" :min="1" :max="100" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="建造年份" prop="year">
              <el-input-number v-model="formData.year" :min="1900" :max="2030" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="朝向" prop="orientation">
              <el-select v-model="formData.orientation" placeholder="请选择朝向">
                <el-option label="东" value="东" /><el-option label="南" value="南" />
                <el-option label="西" value="西" /><el-option label="北" value="北" />
                <el-option label="东南" value="东南" /><el-option label="西南" value="西南" />
                <el-option label="东北" value="东北" /><el-option label="西北" value="西北" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="装修" prop="decoration">
              <el-select v-model="formData.decoration" placeholder="请选择装修">
                <el-option label="毛坯" value="毛坯" /><el-option label="简装" value="简装" />
                <el-option label="精装" value="精装" /><el-option label="豪装" value="豪装" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="总价(元)" prop="price">
              <el-input-number v-model="formData.price" :min="1" :step="10000" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="房源类型" prop="property_type">
              <el-select v-model="formData.property_type" placeholder="请选择">
                <el-option label="住宅" value="住宅" /><el-option label="公寓" value="公寓" />
                <el-option label="别墅" value="别墅" /><el-option label="商住" value="商住" />
                <el-option label="其他" value="其他" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, ElForm } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { housesApi } from '@/api'
import { useHousesStore } from '@/store'
import type { House } from '@/types'

const housesStore = useHousesStore()
const formRef = ref<InstanceType<typeof ElForm>>()
const dialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref<number | null>(null)
const submitting = ref(false)

const filters = reactive({
  district: '泾渭街道' as string,
  ordering: '-created_at' as string
})

const districtList = [
  '泾渭街道', '鹿苑街道', '崇皇街道', '渭水片区', '通远街道', '耿镇街道'
]

const formData = reactive({
  name: '',
  district: '',
  area: 100,
  rooms: 3,
  halls: 2,
  bathrooms: 1,
  floor: 1,
  total_floors: 20,
  year: 2025,
  orientation: '南',
  decoration: '精装',
  price: 5000000,
  property_type: '住宅'
})

const formRules = {
  name: [{ required: true, message: '请输入小区名称', trigger: 'blur' }],
  district: [{ required: true, message: '请选择区域', trigger: 'change' }],
  area: [{ required: true, message: '请输入面积', trigger: 'blur' }],
  rooms: [{ required: true, message: '请输入房间数', trigger: 'blur' }],
  year: [{ required: true, message: '请输入建造年份', trigger: 'blur' }],
  price: [{ required: true, message: '请输入总价', trigger: 'blur' }]
}

const formatPrice = (price: number) =>
  new Intl.NumberFormat('zh-CN', {
    style: 'currency', currency: 'CNY',
    minimumFractionDigits: 0, maximumFractionDigits: 0
  }).format(price)

const handleSearch = () => {
  housesStore.district = filters.district || undefined
  housesStore.ordering = filters.ordering || undefined
  housesStore.currentPage = 1
  housesStore.fetchHouses()
}

const onFilterChange = () => {
  handleSearch()
}

const handleReset = () => {
  filters.district = '泾渭街道'
  filters.ordering = '-created_at'
  handleSearch()
}

const resetForm = () => {
  Object.assign(formData, {
    name: '', district: '', area: 100, rooms: 3, halls: 2,
    bathrooms: 1, floor: 1, total_floors: 20, year: 2020,
    orientation: '南', decoration: '精装', price: 5000000, property_type: '住宅'
  })
}

const handleAdd = () => {
  isEditing.value = false
  editingId.value = null
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (row: House) => {
  isEditing.value = true
  editingId.value = row.id
  Object.assign(formData, {
    name: row.name, district: row.district, area: row.area,
    rooms: row.rooms, halls: row.halls, bathrooms: row.bathrooms,
    floor: row.floor, total_floors: row.total_floors, year: row.year,
    orientation: row.orientation, decoration: row.decoration,
    price: parseFloat(row.price), property_type: row.property_type
  })
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      const payload = { ...formData, price: String(formData.price) }
      if (isEditing.value && editingId.value) {
        await housesApi.update(editingId.value, payload)
        ElMessage.success('编辑成功')
      } else {
        await housesApi.create(payload)
        ElMessage.success('新增成功')
      }
      dialogVisible.value = false
      housesStore.fetchHouses()
    } catch {
      // Error handled by API interceptor
    } finally {
      submitting.value = false
    }
  })
}

const handleDelete = (row: House) => {
  ElMessageBox.confirm(`确定要删除房源 "${row.name}" 吗？`, '提示', {
    confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning'
  }).then(async () => {
    try {
      await housesApi.delete(row.id)
      ElMessage.success('删除成功')
      housesStore.fetchHouses()
    } catch {
      // Error handled by API interceptor
    }
  })
}

onMounted(() => {
  housesStore.district = filters.district
  housesStore.ordering = filters.ordering
  housesStore.fetchHouses()
})
</script>

<style scoped>
.houses-view { min-height: 100%; }
.filter-card { margin-bottom: 24px; }
.filter-card .el-form { margin-bottom: 0; }
.table-card { border-radius: 12px; }
.table-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.table-header h3 { margin: 0; font-size: 18px; font-weight: 600; }
.pagination { margin-top: 20px; display: flex; justify-content: flex-end; }

:deep(.el-table) { border-radius: 8px; overflow: hidden; }
:deep(.el-table th) { background-color: #f5f7fa; }
</style>
