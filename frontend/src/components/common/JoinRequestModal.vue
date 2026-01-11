<script setup lang="ts">
import { computed } from 'vue'
import type { SearchItem } from '../../store/search'
import { useUserStore } from '../../store/users';

const props = defineProps<{
  visible: boolean
  item: SearchItem
}>()

const emit = defineEmits<{
  (e: 'submit', item: SearchItem): void
  (e: 'close'): void
}>()

const userStore = useUserStore()

const title = computed(() => {
  if (props.item.type === 'users') {
    return props.item.username
  }
  if (props.item.type === 'chats') {
    return props.item.name
  }
  return ''
})

const subtitle = computed(() => {
  if (props.item.type === 'users') {
    const first = props.item.first_name ?? ''
    const last = props.item.last_name ?? ''
    return `${first} ${last}`.trim()
  }

  if (props.item.type === 'chats') {
    const count = props.item.members?.length ?? 0
    return `${count} member${count === 1 ? '' : 's'}`
  }

  return ''
})

const avatarFallback = computed(() => {
  return props.item.type === 'users' ? '👤' : '💬'
})

const avatarUrl = computed(() => {
  const item = props.item

  // 👤 USER
  if (item.type === 'users') {
    return item.avatar || null
  }

  // 💬 CHAT
  if (item.type === 'chats') {
    // group chat
    if (item.chat_type === 'group') {
      return item.avatar || null
    }

    // normal 
    if (item.chat_type === 'normal' && item.members) {
      return userStore.getUserFromOneOfTheMembers(item.members)?.avatar
    }
  }

  return null
})

</script>


<template>
  <div v-if="visible" class="modal-overlay" @click.self="emit('close')">
    <div class="modal-content">

      <div class="modal-info">
        <!-- AVATAR -->
        <div class="avatar">
          <img v-if="avatarUrl" :src="avatarUrl" alt="avatar" />
          <div v-else class="avatar-fallback">
            {{ avatarFallback }}
          </div>
        </div>

        <!-- TEXT -->
        <div class="text">
          <div class="name">{{ title }}</div>
          <div v-if="subtitle" class="extra-info">{{ subtitle }}</div>
          <div v-if="item.description" class="description">
            {{ item.description }}
          </div>
        </div>
      </div>

      <!-- ACTIONS -->
      <div class="modal-actions">
        <button
          v-if="item.type === 'users' && item.is_open_for_messages"
          class="btn btn-primary"
          @click="emit('submit', item)"
        >
          Create chat
        </button>

        <button
          v-if="item.type === 'chats' && item.is_open_for_messages"
          class="btn btn-primary"
          @click="emit('submit', item)"
        >
          Join group
        </button>

        <button
          v-if="!item.is_open_for_messages"
          class="btn btn-primary"
          @click="emit('submit', item)"
        >
          Send join request
        </button>

        <button class="btn btn-danger" @click="emit('close')">
          Cancel
        </button>
      </div>
    </div>
  </div>
</template>
