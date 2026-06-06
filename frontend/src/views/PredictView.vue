<template>
  <div class="predict-view">
    <el-card class="predict-card">
      <template #header>
        <div class="card-header">
          <el-icon><DataLine /></el-icon>
          <span>房价预测</span>
        </div>
      </template>

      <el-form ref="predictFormRef" :model="predictForm" :rules="rules" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="房屋面积(㎡)" prop="area">
              <el-input v-model.number="predictForm.area" placeholder="请输入房屋面积">
                <template #append>㎡</template>
              </el-input>
            </el-form-item>

            <el-form-item label="房间数量" prop="rooms">
              <el-input-number v-model="predictForm.rooms" :min="1" :max="10" />
            </el-form-item>

            <el-form-item label="楼层" prop="floor">
              <el-input-number v-model="predictForm.floor" :min="1" :max="50" />
            </el-form-item>

            <el-form-item label="建造年份" prop="year">
              <el-input-number v-model="predictForm.year" :min="1900" :max="2030" />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="区域" prop="district">
              <el-select v-model="predictForm.district" placeholder="请选择区域">
                <el-option v-for="d in districts" :key="d" :label="d" :value="d" />
              </el-select>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="handlePredict" :loading="loading">
                开始预测
              </el-button>
              <el-button @click="resetForm">重置</el-button>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <el-divider />

      <div v-if="predictionResult" class="result-section">
        <h3>预测结果</h3>

        <div class="results-grid">
          <el-card class="result-card">
            <el-icon class="result-icon"><Money /></el-icon>
            <div class="result-info">
              <div class="result-value">{{ formatPrice(predictionResult.predicted_price) }}</div>
              <div class="result-label">预测房价</div>
            </div>
          </el-card>

          <el-card class="result-card">
            <el-icon class="result-icon"><PriceTag /></el-icon>
            <div class="result-info">
              <div class="result-value">{{ (predictionResult.confidence * 100).toFixed(1) }}%</div>
              <div class="result-label">预测置信度</div>
            </div>
          </el-card>
        </div>

        <el-collapse v-if="predictionResult.feature_importance">
          <el-collapse-item title="特征重要性详情">
            <el-table :data="featureImportanceData" style="width: 100%">
              <el-table-column prop="feature" label="特征" width="120" />
              <el-table-column prop="importance" label="重要性" width="100" />
              <el-table-column prop="percentage" label="占比" width="100" />
            </el-table>
          </el-collapse-item>
        </el-collapse>

        <el-collapse v-if="explanationResult">
          <el-collapse-item title="SHAP可解释性分析">
            <el-table :data="explanationResult.explanations" style="width: 100%">
              <el-table-column label="特征" width="120">
                <template #default="{ row }">{{ getFeatureName(row.feature) }}</template>
              </el-table-column>
              <el-table-column label="SHAP值" width="100">
                <template #default="{ row }">
                  <span :class="row.impact">{{ row.shap_value.toFixed(2) }}</span>
                </template>
              </el-table-column>
              <el-table-column label="重要性" width="100">
                <template #default="{ row }">{{ row.importance.toFixed(3) }}</template>
              </el-table-column>
              <el-table-column label="影响方向" width="100">
                <template #default="{ row }">
                  <el-tag :type="row.impact === 'positive' ? 'success' : 'danger'">
                    {{ row.impact === 'positive' ? '正向' : '负向' }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
            <div class="base-value">
              <p>基准值: {{ formatPrice(explanationResult.base_value) }}</p>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage, ElForm } from 'element-plus'
import { Money, PriceTag, DataLine } from '@element-plus/icons-vue'
import { predictionApi } from '@/api'
import type { PredictionResponse, ExplanationResponse } from '@/types'

const predictFormRef = ref<InstanceType<typeof ElForm>>()
const loading = ref(false)
const predictionResult = ref<PredictionResponse | null>(null)
const explanationResult = ref<ExplanationResponse | null>(null)

const predictForm = reactive({
  area: 100,
  rooms: 3,
  floor: 1,
  year: 2025,
  district: '泾渭街道'
})

const districts = [
  '泾渭街道', '鹿苑街道', '崇皇街道', '渭水片区', '通远街道', '耿镇街道'
]

const rules = {
  area: [
    { required: true, message: '请输入房屋面积', trigger: 'blur' },
    { type: 'number' as const, min: 1, message: '面积必须大于0', trigger: 'blur' }
  ],
  rooms: [
    { required: true, message: '请输入房间数量', trigger: 'blur' },
    { type: 'number' as const, min: 1, max: 10, message: '房间数量必须在1-10之间', trigger: 'blur' }
  ],
  floor: [
    { required: true, message: '请输入楼层', trigger: 'blur' },
    { type: 'number' as const, min: 1, max: 50, message: '楼层必须在1-50之间', trigger: 'blur' }
  ],
  year: [
    { required: true, message: '请输入建造年份', trigger: 'blur' },
    { type: 'number' as const, min: 1900, max: 2030, message: '建造年份必须在1900-2030之间', trigger: 'blur' }
  ],
  district: [
    { required: true, message: '请选择区域', trigger: 'blur' }
  ]
}

const featureImportanceData = computed(() => {
  if (!predictionResult.value?.feature_importance) return []
  return Object.entries(predictionResult.value.feature_importance).map(([feature, importance]) => ({
    feature,
    importance: importance.toFixed(4),
    percentage: `${(importance * 100).toFixed(1)}%`
  }))
})

const formatPrice = (price: number) =>
  new Intl.NumberFormat('zh-CN', {
    style: 'currency', currency: 'CNY',
    minimumFractionDigits: 0, maximumFractionDigits: 0
  }).format(price)

const getFeatureName = (feature: string): string => {
  const mapping: Record<string, string> = {
    'area': '面积', 'rooms': '房间数', 'floor': '楼层',
    'year': '建造年份', 'district': '区域', 'lat': '纬度',
    'lng': '经度', 'district_encoded': '区域编码', 'house_age': '房龄',
    'price_per_sqm': '单价'
  }
  return mapping[feature] || feature
}

const handlePredict = async () => {
  if (!predictFormRef.value) return

  await predictFormRef.value.validate(async (valid) => {
    if (!valid) {
      ElMessage.error('请填写完整表单')
      return
    }

    loading.value = true
    predictionResult.value = null
    explanationResult.value = null

    try {
      const predData = await predictionApi.predict(predictForm) as unknown as PredictionResponse
      predictionResult.value = predData

      const explData = await predictionApi.explain(predictForm) as unknown as ExplanationResponse
      explanationResult.value = explData

      ElMessage.success('预测成功')
    } catch {
      // Error handled by API interceptor
    } finally {
      loading.value = false
    }
  })
}

const resetForm = () => {
  predictFormRef.value?.resetFields()
  predictionResult.value = null
  explanationResult.value = null
}
</script>

<style scoped>
.predict-view { min-height: 100%; display: flex; flex-direction: column; }
.predict-card { margin-bottom: 24px; }
.card-header { display: flex; align-items: center; gap: 12px; }
.result-section { margin-top: 24px; margin-bottom: 24px; }
.results-grid {
  display: grid; grid-template-columns: repeat(2, 1fr);
  gap: 24px; margin-bottom: 24px;
}
.result-card {
  min-height: 120px; display: flex; align-items: center; gap: 16px; padding: 16px;
}
.result-icon {
  font-size: 28px; width: 56px; height: 56px;
  display: flex; align-items: center; justify-content: center;
  background: #ecf5ff; border-radius: 50%; flex-shrink: 0;
}
.result-value { font-size: 24px; font-weight: bold; color: #409eff; }
.result-label { font-size: 14px; color: #606266; }
.base-value { margin-top: 16px; padding: 16px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #409eff; }
.positive { color: #67c23a; font-weight: 600; }
.negative { color: #f56c6c; font-weight: 600; }

@media (max-width: 768px) {
  .results-grid { grid-template-columns: 1fr; }
}
</style>
