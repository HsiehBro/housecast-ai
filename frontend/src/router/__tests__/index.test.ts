import { describe, it, expect, vi, beforeEach } from 'vitest'
import { routes } from '../index'

describe('Router configuration', () => {
  it('has all required routes', () => {
    const routePaths = routes.map(r => r.path)
    expect(routePaths).toContain('/')
    expect(routePaths).toContain('/login')
    expect(routePaths).toContain('/register')
    expect(routePaths).toContain('/houses')
    expect(routePaths).toContain('/predict')
    expect(routePaths).toContain('/charts')
    expect(routePaths).toContain('/map')
    expect(routePaths).toContain('/profile')
  })

  it('protected routes have requiresAuth meta', () => {
    const protectedRoutes = routes.filter(r => r.meta?.requiresAuth)
    const protectedPaths = protectedRoutes.map(r => r.path)
    expect(protectedPaths).toContain('/')
    expect(protectedPaths).toContain('/houses')
    expect(protectedPaths).toContain('/predict')
    expect(protectedPaths).toContain('/charts')
    expect(protectedPaths).toContain('/map')
    expect(protectedPaths).toContain('/profile')
  })

  it('login and register routes do not require auth', () => {
    const loginRoute = routes.find(r => r.path === '/login')
    const registerRoute = routes.find(r => r.path === '/register')
    expect(loginRoute?.meta?.requiresAuth).toBeFalsy()
    expect(registerRoute?.meta?.requiresAuth).toBeFalsy()
  })

  it('all routes have name property', () => {
    for (const route of routes) {
      if (route.path === '/:pathMatch(.*)*') continue
      expect(route.name, `Route ${route.path} should have a name`).toBeDefined()
    }
  })

  it('all routes have component', () => {
    for (const route of routes) {
      if (route.path === '/:pathMatch(.*)*') continue
      expect(route.component, `Route ${route.path} should have a component`).toBeDefined()
    }
  })

  it('register route exists with Register name', () => {
    const registerRoute = routes.find(r => r.path === '/register')
    expect(registerRoute).toBeDefined()
    expect(registerRoute?.name).toBe('Register')
  })
})
