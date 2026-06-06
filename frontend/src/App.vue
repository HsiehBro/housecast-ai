<template>
  <!-- 初始化中 -->
  <div v-if="!userStore.isInitialized" class="app-loading">
    <el-icon class="is-loading" :size="40" color="#667eea"><Loading /></el-icon>
  </div>

  <div class="app" v-else>
    <!-- 未登录：只显示路由页面（登录/注册） -->
    <template v-if="!userStore.isLoggedIn">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </template>

    <!-- 已登录：显示完整布局 -->
    <template v-else>
      <!-- 顶部导航栏 -->
      <el-header class="main-header">
        <div class="header-left">
          <el-button
            class="menu-toggle"
            text
            @click="isMenuCollapsed = !isMenuCollapsed"
            v-if="isMobile"
          >
            <el-icon :size="24">
              <Menu v-if="isMenuCollapsed" />
              <Close v-else />
            </el-icon>
          </el-button>
          <div class="logo-section">
            <div class="logo-icon">
              <el-icon size="24"><House /></el-icon>
            </div>
            <span class="logo-text" v-if="!isMenuCollapsed">智能房价预测系统</span>
          </div>
        </div>
        <div class="header-right">
          <div class="header-actions">
            <el-dropdown placement="bottom-end">
              <div class="user-avatar">
                <el-avatar :size="36">
                  {{ userStore.user?.username?.charAt(0) || 'U' }}
                </el-avatar>
              </div>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="showProfile">
                    <el-icon><User /></el-icon>
                    个人中心
                  </el-dropdown-item>
                  <el-dropdown-item divided @click="handleLogout">
                    <el-icon><SwitchButton /></el-icon>
                    退出登录
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </el-header>

      <!-- 主体内容区 -->
      <el-container class="main-container">
        <!-- 移动端菜单遮罩层 -->
        <div
          v-if="isMobile && !isMenuCollapsed"
          class="sidebar-overlay active"
          @click="isMenuCollapsed = true"
        ></div>

        <!-- 左侧导航栏 -->
        <el-aside
          :class="['sidebar', { 'collapsed': isMenuCollapsed, 'mobile': isMobile }]"
          :style="{ width: isMenuCollapsed ? '64px' : '240px' }"
        >
          <el-scrollbar>
            <el-menu
              :default-active="activeMenu"
              :collapse="isMenuCollapsed"
              :collapse-transition="false"
              class="sidebar-menu"
              @select="handleMenuSelect"
            >
              <el-menu-item index="/">
                <el-icon><House /></el-icon>
                <template #title>首页看板</template>
              </el-menu-item>
              <el-menu-item index="/houses">
                <el-icon><Document /></el-icon>
                <template #title>房源管理</template>
              </el-menu-item>
              <el-menu-item index="/predict">
                <el-icon><DataLine /></el-icon>
                <template #title>房价预测</template>
              </el-menu-item>
              <el-menu-item index="/charts">
                <el-icon><TrendCharts /></el-icon>
                <template #title>数据可视化</template>
              </el-menu-item>
              <el-menu-item index="/map">
                <el-icon><Location /></el-icon>
                <template #title>地图展示</template>
              </el-menu-item>
              <el-menu-item index="/profile">
                <el-icon><User /></el-icon>
                <template #title>个人中心</template>
              </el-menu-item>
            </el-menu>
          </el-scrollbar>
        </el-aside>

        <!-- 主内容区 -->
        <el-main
          :class="['main-content', { 'collapsed': isMenuCollapsed, 'mobile': isMobile }]"
        >
          <router-view v-slot="{ Component }">
            <transition name="fade" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </el-main>
      </el-container>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/store'
import {
  House, DataLine, Location, Menu, Close,
  User, SwitchButton, TrendCharts, Document, Loading
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const isMenuCollapsed = ref(false)
const isMobile = ref(false)
const activeMenu = ref('/')

const checkMobile = () => {
  isMobile.value = window.innerWidth <= 768
  if (isMobile.value) {
    isMenuCollapsed.value = true
  }
}

const handleMenuSelect = (index: string) => {
  if (isMobile.value) {
    isMenuCollapsed.value = true
  }
  router.push(index)
}

const showProfile = () => {
  router.push('/profile')
}

const handleLogout = async () => {
  await userStore.logout()
  router.push('/login')
}

const handleResize = () => {
  checkMobile()
}

onMounted(async () => {
  await userStore.initialize()
  checkMobile()
  activeMenu.value = route.path

  // Watch route changes for active menu
  router.afterEach((to) => {
    activeMenu.value = to.path
    if (isMobile.value) {
      isMenuCollapsed.value = true
    }
  })

  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style>
.app-loading {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f7fa;
}

.app {
  height: 100vh;
  overflow: hidden;
  background-color: #f5f7fa;
}

.main-header {
  height: 64px !important;
  background-color: #ffffff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  position: fixed;
  top: 0; left: 0; right: 0;
  z-index: 1000;
}

.header-left { display: flex; align-items: center; gap: 20px; }
.logo-section { display: flex; align-items: center; gap: 12px; }
.logo-icon {
  width: 40px; height: 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  color: white;
}
.logo-text {
  font-size: 18px; font-weight: 600;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.menu-toggle {
  color: #606266; border: none; background: transparent;
  padding: 8px; cursor: pointer; border-radius: 4px; transition: all 0.3s;
}
.menu-toggle:hover { background-color: #f5f7fa; }
.header-right { display: flex; align-items: center; gap: 20px; }
.header-actions { display: flex; align-items: center; gap: 16px; }
.user-avatar { cursor: pointer; transition: all 0.3s; }
.user-avatar:hover { transform: scale(1.05); }

.main-container {
  margin-top: 64px;
  height: calc(100vh - 64px);
  display: flex;
  width: 100%;
}

.sidebar {
  background-color: #001529;
  transition: width 0.3s ease;
  position: relative;
  box-shadow: 2px 0 8px rgba(0, 21, 41, 0.15);
  flex-shrink: 0;
  overflow: hidden;
}

.sidebar.collapsed { width: 64px !important; }

.sidebar.mobile {
  position: fixed !important;
  top: 64px; left: 0; bottom: 0;
  z-index: 999;
  transform: translateX(-100%);
  transition: transform 0.3s ease;
}

.sidebar.mobile:not(.collapsed) { transform: translateX(0); }

/* Fix: el-scrollbar and el-menu must be transparent on dark sidebar */
.sidebar .el-scrollbar {
  background-color: transparent;
}
.sidebar .el-scrollbar__wrap {
  background-color: transparent;
}
.sidebar .el-scrollbar__bar.is-vertical {
  right: 2px;
}
.sidebar-menu {
  border-right: none !important;
  background-color: transparent !important;
}
.sidebar-menu .el-menu-item {
  color: rgba(255, 255, 255, 0.65) !important;
  background-color: transparent !important;
  border-radius: 6px;
  margin: 4px 12px;
  transition: all 0.3s;
}
.sidebar-menu .el-menu-item:hover {
  background-color: rgba(255, 255, 255, 0.08) !important;
  color: #fff !important;
}
.sidebar-menu .el-menu-item.is-active {
  background-color: #1890ff !important;
  color: #fff !important;
  font-weight: 500;
}
.sidebar-menu .el-menu-item .el-icon {
  font-size: 18px; margin-right: 12px; width: 24px; text-align: center;
  color: inherit;
}
.sidebar.collapsed .el-menu-item { text-align: center; padding: 0 16px; }
.sidebar.collapsed .el-menu-item .el-icon { margin-right: 0; }

.main-content {
  padding: 24px;
  overflow-y: auto;
  background-color: #f5f7fa;
  flex: 1;
  min-width: 0;
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.sidebar-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 998;
  display: none;
}
.sidebar-overlay.active { display: block; }

@media (max-width: 768px) {
  .main-header { padding: 0 16px; }
  .logo-text { display: none; }
  .main-content { padding: 16px; }
  .sidebar.mobile { width: 240px !important; }
}
</style>
