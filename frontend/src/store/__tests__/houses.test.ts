import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useHousesStore } from '../houses'
import { housesApi } from '@/api'
import type { House, HouseListResponse } from '@/types'

vi.mock('@/api', () => ({
  housesApi: {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn()
  }
}))

const mockHouse: House = {
  id: 1, name: 'Test', address: 'Addr', district: '浦东新区',
  property_type: '住宅', area: 100, rooms: 3, halls: 2, bathrooms: 1,
  floor: 5, total_floors: 20, year: 2020, orientation: '南',
  decoration: '精装', price: '5000000.00', price_per_sqm: '50000.00',
  lat: 31.23, lng: 121.47, status: 'available',
  created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-01T00:00:00Z'
}

// Interceptor extracts response.data, so mock returns the data directly
const mockResponse: HouseListResponse = {
  count: 1, next: null, previous: null, results: [mockHouse]
}
const emptyResponse: HouseListResponse = {
  count: 0, next: null, previous: null, results: []
}

describe('useHousesStore', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setActivePinia(createPinia())
  })

  it('initializes with empty state', () => {
    const store = useHousesStore()
    expect(store.houses).toEqual([])
    expect(store.total).toBe(0)
    expect(store.loading).toBe(false)
    expect(store.currentPage).toBe(1)
    expect(store.pageSize).toBe(20)
  })

  it('fetchHouses calls API and updates state', async () => {
    vi.mocked(housesApi.list).mockResolvedValueOnce(mockResponse as never)

    const store = useHousesStore()
    await store.fetchHouses()

    expect(housesApi.list).toHaveBeenCalledWith({ page: 1, page_size: 20, district: undefined, ordering: undefined })
    expect(store.houses).toEqual([mockHouse])
    expect(store.total).toBe(1)
    expect(store.loading).toBe(false)
  })

  it('fetchHouses passes filter params', async () => {
    vi.mocked(housesApi.list).mockResolvedValueOnce(emptyResponse as never)

    const store = useHousesStore()
    store.district = '浦东新区'
    store.ordering = '-price'
    await store.fetchHouses()

    expect(housesApi.list).toHaveBeenCalledWith({
      page: 1, page_size: 20, district: '浦东新区', ordering: '-price'
    })
  })

  it('fetchHouses sets loading state', async () => {
    let resolveFn: (value: unknown) => void
    const promise = new Promise(resolve => { resolveFn = resolve })
    vi.mocked(housesApi.list).mockReturnValueOnce(promise as never)

    const store = useHousesStore()
    const fetchPromise = store.fetchHouses()

    expect(store.loading).toBe(true)
    resolveFn!(emptyResponse)
    await fetchPromise
    expect(store.loading).toBe(false)
  })

  it('setPage updates currentPage and fetches', async () => {
    vi.mocked(housesApi.list).mockResolvedValue(emptyResponse as never)

    const store = useHousesStore()
    await store.setPage(3)

    expect(store.currentPage).toBe(3)
    expect(housesApi.list).toHaveBeenCalledWith(
      expect.objectContaining({ page: 3 })
    )
  })

  it('setPageSize updates pageSize and resets to page 1', async () => {
    vi.mocked(housesApi.list).mockResolvedValue(emptyResponse as never)

    const store = useHousesStore()
    store.currentPage = 5
    await store.setPageSize(50)

    expect(store.pageSize).toBe(50)
    expect(store.currentPage).toBe(1)
  })

  it('deleteHouse removes house from list', async () => {
    vi.mocked(housesApi.list).mockResolvedValueOnce({
      count: 2, next: null, previous: null, results: [mockHouse, { ...mockHouse, id: 2 }]
    } as never)
    vi.mocked(housesApi.delete).mockResolvedValueOnce({ status: 204 })
    vi.mocked(housesApi.list).mockResolvedValueOnce({
      count: 1, next: null, previous: null, results: [mockHouse]
    } as never)

    const store = useHousesStore()
    await store.fetchHouses()
    expect(store.houses).toHaveLength(2)

    await store.deleteHouse(2)
    expect(housesApi.delete).toHaveBeenCalledWith(2)
  })

  it('fetchHouses handles errors', async () => {
    vi.mocked(housesApi.list).mockRejectedValueOnce(new Error('Network error'))

    const store = useHousesStore()
    await store.fetchHouses()

    expect(store.loading).toBe(false)
  })
})
