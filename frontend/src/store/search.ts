import { defineStore } from "pinia"
import axiosInstance from "../api/axios"

export interface SearchItem {
  uuid: string
  type: 'users' | 'chats' | 'messages'
  name?: string
  text?: string
  username?: string
}

export const useSearchStore = defineStore('search', {
  state: () => ({
    query: '',
    items: [] as SearchItem[],
    queries: [] as string[], // from redis cache
    page: 1,
    pageSize: 20,
    total: 0,
    loading: false,
    hasMore: true,
  }),

  actions: {
    reset(query: string) {
      this.query = query
      this.items = []
      this.page = 1
      this.total = 0
      this.hasMore = true
    },
    async fetchSearchPage() {
        if (this.loading || !this.hasMore) return

        this.loading = true

        const { data } = await axiosInstance.get('/search/global', {
            params: {
                q: this.query,
                page: this.page,
            }
        })

        this.items.push(...data.items)
        this.total = data.total

        if (this.items.length >= this.total) {
            this.hasMore = false
        } else {
            this.page++
        }

        this.loading = false
    },
    async loadHistory() {
        const { data } = await axiosInstance.get('/search/history')
        this.queries = data.items
    }
  },
})
