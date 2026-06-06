import { defineStore } from 'pinia'
import { housesApi } from '@/api'
import type { House, HouseListParams, HouseListResponse } from '@/types'

export const useHousesStore = defineStore('houses', {
  state: () => ({
    houses: [] as House[],
    total: 0,
    loading: false,
    currentPage: 1,
    pageSize: 20,
    district: undefined as string | undefined,
    ordering: undefined as string | undefined
  }),

  actions: {
    async fetchHouses() {
      this.loading = true
      try {
        const params: HouseListParams = {
          page: this.currentPage,
          page_size: this.pageSize
        }
        if (this.district) params.district = this.district
        if (this.ordering) params.ordering = this.ordering

        const data = await housesApi.list(params) as unknown as HouseListResponse
        this.houses = data.results
        this.total = data.count
      } catch {
        // Error is already handled by the API interceptor
      } finally {
        this.loading = false
      }
    },

    async setPage(page: number) {
      this.currentPage = page
      await this.fetchHouses()
    },

    async setPageSize(size: number) {
      this.pageSize = size
      this.currentPage = 1
      await this.fetchHouses()
    },

    async setDistrict(district: string | undefined) {
      this.district = district
      this.currentPage = 1
      await this.fetchHouses()
    },

    async setOrdering(ordering: string | undefined) {
      this.ordering = ordering
      await this.fetchHouses()
    },

    async deleteHouse(id: number) {
      await housesApi.delete(id)
      await this.fetchHouses()
    }
  }
})
