import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'
import LoginView from '../LoginView.vue'

// Mock authApi for store interactions
vi.mock('@/api', () => ({
  authApi: {
    login: vi.fn(),
    logout: vi.fn(),
    refresh: vi.fn(),
    me: vi.fn()
  }
}))

const router = createRouter({
  history: createMemoryHistory(),
  routes: [
    { path: '/', name: 'Dashboard', component: { template: '<div>' } },
    { path: '/login', name: 'Login', component: LoginView },
    { path: '/register', name: 'Register', component: { template: '<div>' } }
  ]
})

function mountLogin() {
  return mount(LoginView, {
    global: {
      plugins: [router, ElementPlus, createPinia()]
    }
  })
}

describe('LoginView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    setActivePinia(createPinia())
  })

  // ===== Rendering =====

  it('renders login card', () => {
    const wrapper = mountLogin()
    expect(wrapper.find('.login-card').exists()).toBe(true)
  })

  it('renders title with system name', () => {
    const wrapper = mountLogin()
    expect(wrapper.find('h2').text()).toContain('智能房价预测系统')
  })

  it('renders username input', () => {
    const wrapper = mountLogin()
    const inputs = wrapper.findAll('input')
    expect(inputs.length).toBeGreaterThanOrEqual(2)
  })

  it('renders login button', () => {
    const wrapper = mountLogin()
    expect(wrapper.find('.login-button').exists()).toBe(true)
  })

  it('login button shows login text', () => {
    const wrapper = mountLogin()
    expect(wrapper.find('.login-button').text()).toContain('登录')
  })

  it('renders register link', () => {
    const wrapper = mountLogin()
    const link = wrapper.find('.register-link a')
    expect(link.exists()).toBe(true)
  })

  it('register link points to /register', () => {
    const wrapper = mountLogin()
    const link = wrapper.find('.register-link a')
    const href = link.attributes('href') || link.attributes('to')
    expect(href).toContain('/register')
  })

  // ===== Form structure =====

  it('has a form element', () => {
    const wrapper = mountLogin()
    expect(wrapper.find('form').exists() || wrapper.find('.el-form').exists()).toBe(true)
  })

  it('has password input with type password', () => {
    const wrapper = mountLogin()
    const inputs = wrapper.findAll('input')
    const passwordInput = inputs.find(input => input.attributes('type') === 'password')
    expect(passwordInput).toBeDefined()
  })

  // ===== Loading state =====

  it('login button is not loading by default', () => {
    const wrapper = mountLogin()
    expect(wrapper.find('.login-button').classes()).not.toContain('is-loading')
  })

  // ===== Form validation =====

  it('form has validation rules', () => {
    const wrapper = mountLogin()
    // The component should define rules object
    expect(wrapper.vm.rules).toBeDefined()
    expect(wrapper.vm.rules.username).toBeDefined()
    expect(wrapper.vm.rules.password).toBeDefined()
  })

  it('username validation requires at least 3 characters', () => {
    const wrapper = mountLogin()
    const usernameRules = wrapper.vm.rules.username
    const hasMinRule = usernameRules.some(
      (r: { min?: number }) => r.min !== undefined && r.min >= 3
    )
    expect(hasMinRule).toBe(true)
  })

  it('password validation requires at least 8 characters', () => {
    const wrapper = mountLogin()
    const passwordRules = wrapper.vm.rules.password
    const hasMinRule = passwordRules.some(
      (r: { min?: number }) => r.min !== undefined && r.min >= 8
    )
    expect(hasMinRule).toBe(true)
  })

  // ===== Reactive form data =====

  it('loginForm reactive data starts empty', () => {
    const wrapper = mountLogin()
    expect(wrapper.vm.loginForm.username).toBe('')
    expect(wrapper.vm.loginForm.password).toBe('')
  })

  it('loading ref starts as false', () => {
    const wrapper = mountLogin()
    expect(wrapper.vm.loading).toBe(false)
  })
})

describe('LoginView - User Store Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('uses useUserStore', () => {
    const wrapper = mountLogin()
    expect(wrapper.vm.userStore).toBeDefined()
  })
})
