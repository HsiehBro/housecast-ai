<template>
  <div class="profile-view">
    <el-row :gutter="24">
      <el-col :span="8">
        <!-- 用户信息卡片 -->
        <el-card class="user-card">
          <div class="user-avatar-section">
            <el-avatar :size="120" class="user-avatar">
              {{ user?.username?.charAt(0) || 'U' }}
            </el-avatar>
          </div>

          <div class="user-info">
            <h2>{{ user?.username || '用户' }}</h2>
            <p class="user-email">{{ user?.email || '' }}</p>
            <p class="user-phone">{{ user?.phone || '未设置手机号' }}</p>
          </div>

          <div class="user-stats">
            <div class="stat-item">
              <div class="stat-label">注册时间</div>
              <div class="stat-value">{{ formatDate(user?.created_at) }}</div>
            </div>
          </div>
        </el-card>

        <!-- 功能菜单 -->
        <el-card class="menu-card">
          <el-menu :default-active="activeMenu" class="profile-menu" @select="handleMenuSelect">
            <el-menu-item index="basic">
              <el-icon><User /></el-icon>
              <span>基本信息</span>
            </el-menu-item>
            <el-menu-item index="password">
              <el-icon><Lock /></el-icon>
              <span>修改密码</span>
            </el-menu-item>
          </el-menu>
        </el-card>
      </el-col>

      <el-col :span="16">
        <!-- 基本信息编辑 -->
        <el-card v-if="activeMenu === 'basic'" class="content-card">
          <template #header>
            <div class="card-header">
              <h3>基本信息</h3>
              <el-button type="primary" @click="handleSave" :loading="saving">保存修改</el-button>
            </div>
          </template>

          <el-form ref="basicFormRef" :model="basicForm" :rules="basicRules" label-width="100px">
            <el-form-item label="用户名" prop="username">
              <el-input v-model="basicForm.username" />
            </el-form-item>

            <el-form-item label="邮箱" prop="email">
              <el-input v-model="basicForm.email" />
            </el-form-item>

            <el-form-item label="手机号码" prop="phone">
              <el-input v-model="basicForm.phone" />
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 修改密码 -->
        <el-card v-if="activeMenu === 'password'" class="content-card">
          <template #header>
            <div class="card-header">
              <h3>修改密码</h3>
            </div>
          </template>

          <el-form ref="passwordFormRef" :model="passwordForm" :rules="passwordRules" label-width="100px">
            <el-form-item label="当前密码" prop="currentPassword">
              <el-input v-model="passwordForm.currentPassword" type="password" show-password placeholder="请输入当前密码" />
            </el-form-item>

            <el-form-item label="新密码" prop="newPassword">
              <el-input v-model="passwordForm.newPassword" type="password" show-password placeholder="请输入新密码" />
            </el-form-item>

            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input v-model="passwordForm.confirmPassword" type="password" show-password placeholder="请再次输入新密码" />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="handleChangePassword" :loading="changingPassword">确认修改</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElForm } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/store'
import { authApi } from '@/api'
import type { User as UserType } from '@/types'

const userStore = useUserStore()
const user = ref<UserType | null>(null)

const activeMenu = ref('basic')
const basicFormRef = ref<InstanceType<typeof ElForm>>()
const passwordFormRef = ref<InstanceType<typeof ElForm>>()
const saving = ref(false)
const changingPassword = ref(false)

const basicForm = reactive({
  username: '',
  email: '',
  phone: ''
})

const basicRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email' as const, message: '请输入正确的邮箱', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^$|^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ]
}

const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const validateConfirm = (_rule: unknown, value: string, callback: (error?: Error) => void) => {
  if (value !== passwordForm.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  currentPassword: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, max: 20, message: '密码长度在 8 到 20 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' }
  ]
}

const formatDate = (dateStr: string | undefined): string => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const handleMenuSelect = (index: string) => {
  activeMenu.value = index
}

const loadUser = async () => {
  try {
    await userStore.fetchUser()
    user.value = userStore.user
    if (user.value) {
      basicForm.username = user.value.username
      basicForm.email = user.value.email
      basicForm.phone = user.value.phone
    }
  } catch {
    ElMessage.error('加载用户信息失败')
  }
}

const handleSave = async () => {
  if (!basicFormRef.value) return

  await basicFormRef.value.validate(async (valid) => {
    if (!valid) return

    saving.value = true
    try {
      await authApi.updateMe({
        username: basicForm.username,
        email: basicForm.email,
        phone: basicForm.phone
      })
      await userStore.fetchUser()
      ElMessage.success('保存成功')
    } catch {
      // Error handled by API interceptor
    } finally {
      saving.value = false
    }
  })
}

const handleChangePassword = async () => {
  if (!passwordFormRef.value) return

  await passwordFormRef.value.validate(async (valid) => {
    if (!valid) return

    changingPassword.value = true
    try {
      await authApi.changePassword({
        old_password: passwordForm.currentPassword,
        new_password: passwordForm.newPassword,
        new_password_confirm: passwordForm.confirmPassword
      })
      ElMessage.success('密码修改成功，请重新登录')
      // Clear tokens and redirect to login — old token is invalid after password change
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    } catch {
      // Error handled by API interceptor
    } finally {
      changingPassword.value = false
    }
  })
}

onMounted(() => {
  loadUser()
})
</script>

<style scoped>
.profile-view { min-height: 100%; }
.user-card { text-align: center; margin-bottom: 24px; }
.user-avatar-section { margin-bottom: 20px; }
.user-avatar { border: 4px solid #f0f2f5; }
.user-info h2 { margin: 0 0 8px; font-size: 20px; font-weight: 600; }
.user-email, .user-phone { color: #909399; font-size: 14px; margin: 4px 0; }
.user-stats { margin-top: 24px; }
.stat-item { text-align: center; }
.stat-label { font-size: 12px; color: #909399; }
.stat-value { font-size: 14px; color: #303133; font-weight: 500; }
.menu-card { margin-bottom: 24px; }
.profile-menu { border-right: none; }
.content-card { margin-bottom: 24px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.card-header h3 { margin: 0; font-size: 18px; font-weight: 600; }

@media (max-width: 768px) {
  .profile-view { padding: 16px; }
}
</style>
