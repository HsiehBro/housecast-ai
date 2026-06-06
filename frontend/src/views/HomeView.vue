<template>
  <!-- HomeView 已被重定向到 EnterpriseDashboard -->
  <div class="home-redirect">
    <el-result
      icon="warning"
      title="页面已更新"
      sub-title="首页已迁移到新的企业级仪表盘，正在跳转..."
    >
      <template #extra>
        <el-button type="primary" @click="goToDashboard">立即跳转</el-button>
      </template>
    </el-result>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const goToDashboard = () => {
  router.push('/')
}
</script>

<style scoped>
.home-redirect {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>