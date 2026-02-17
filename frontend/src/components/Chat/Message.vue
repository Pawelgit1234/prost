<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '../../store/auth'
import type { MessageI } from '../../store/messages'

const props = defineProps<{
  message: MessageI
}>()

const authStore = useAuthStore()

// Check if message belongs to current user
const isMine = computed(() => {
  return props.message.user_uuid === authStore.currentUser?.uuid
})

// Format date/time
const formattedTime = computed(() => {
  const date = new Date(props.message.created_at)
  const now = new Date()

  const isToday =
    date.getDate() === now.getDate() &&
    date.getMonth() === now.getMonth() &&
    date.getFullYear() === now.getFullYear()

  // Format time HH:mm
  const time = date.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit'
  })

  if (isToday) {
    return time
  }

  // If not today → show date + time
  return (
    date.toLocaleDateString([], {
      day: '2-digit',
      month: '2-digit',
      year: '2-digit'
    }) +
    ' ' +
    time
  )
})
</script>

<template>
  <div class="message-row" :class="{ mine: isMine }">
    <div class="message-bubble" :class="{ mine: isMine }">
      <div class="content">
        {{ message.content }}
      </div>

      <div class="time">
        {{ formattedTime }}
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Row alignment */
.message-row {
  display: flex;
  width: 100%;
}

.message-row.mine {
  justify-content: flex-end;
}

/* Bubble style */
.message-bubble {
  background: #eeeeee;
  padding: 8px 12px;
  border-radius: 12px;
  margin: 4px 0;
  max-width: 60%;
  word-break: break-word;
  display: flex;
  flex-direction: column;
}

/* My messages */
.message-bubble.mine {
  background: #4caf50;
  color: white;
}

/* Content text */
.content {
  font-size: 14px;
}

/* Time style */
.time {
  font-size: 11px;
  opacity: 0.7;
  margin-top: 4px;
  align-self: flex-end;
}
</style>
