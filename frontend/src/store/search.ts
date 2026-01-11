import { defineStore } from "pinia"
import axiosInstance from "../api/axios"

export interface SearchItem {
  uuid: string;
  type: 'users' | 'chats' | 'messages';

  // Users
  first_name?: string;
  last_name?: string;
  username?: string;

  // Chats
  name?: string;
  chat_type?: 'group' | 'normal';
  members?: string[]; // uuids of users
  user_names?: string[];
  is_yours?: boolean; // for chats: indicates if current user is a member

  // Users & Chats
  avatar?: string;
  is_open_for_messages?: boolean;
  is_visible?: boolean;
  description?: string;

  // Messages
  text?: string;
  chat?: string; // chat uuid for message
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
  getters: {
    globalItems(state): SearchItem[] {
      return state.items.filter(item => {
        if (item.type === 'users') return true
        if (item.type === 'chats') return !item.is_yours
        return false
      })
    },
    localItems(state): SearchItem[] {
      return state.items.filter(item => {
        if (item.type === 'chats') return item.is_yours
        if (item.type === 'messages') return true
        return false
      })
    }
  },
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
