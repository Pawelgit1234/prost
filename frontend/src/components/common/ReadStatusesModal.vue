<script setup lang="ts">
import { computed } from 'vue'
import type { ReadStatusI } from '../../store/messages'
import type { UserI } from '../../store/auth';

const props = defineProps<{
  visible: boolean
  readStatuses: ReadStatusI[]
  users: UserI[]
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

// Map user_uuid -> user
const userMap = computed(() => {
  const map: Record<string, UserI> = {}
  for (const u of props.users) {
    map[u.uuid] = u
  }
  return map
})

// Format date
function formatDate(dateStr: string) {
  const d = new Date(dateStr)
  return d.toLocaleString([], {
    day: '2-digit',
    month: '2-digit',
    year: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<template>
  <div v-if="visible" class="modal-overlay" @click.self="emit('close')">
    <div class="modal-content">
      <h3>Read Status</h3>

      <div class="scroll-box">
        <div
          v-for="rs in readStatuses"
          :key="rs.user_uuid"
          class="scroll-box-item"
        >
          <div>
            <strong>
              {{ userMap[rs.user_uuid]?.username ?? rs.user_uuid }}
            </strong>
          </div>

          <div>
            Status:
            <span v-if="rs.is_read">Read ✓</span>
            <span v-else>Unread</span>
          </div>

          <div>
            Updated:
            {{ formatDate(rs.updated_at) }}
          </div>
        </div>
      </div>

      <div class="modal-actions">
        <button class="btn btn-primary" @click="emit('close')">
          Close
        </button>
      </div>
    </div>
  </div>
</template>
