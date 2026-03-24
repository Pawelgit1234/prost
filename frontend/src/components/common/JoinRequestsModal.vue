<script setup lang="ts">
import type { JoinRequestI } from '../../store/join_requests';


const props = defineProps<{
  visible: boolean
  requests: JoinRequestI[]
  title: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'approve', uuid: string): void
  (e: 'reject', uuid: string): void
}>()

function fullName(r: JoinRequestI) {
  const name = `${r.sender_first_name} ${r.sender_last_name}`
  return name
}
</script>

<template>
  <div v-if="visible" class="modal-overlay" @click.self="emit('close')">
    <div class="modal-content wide">
      <h3>{{ title }}</h3>

      <div v-if="requests.length" class="req-list">
        <div
          v-for="r in requests"
          :key="r.uuid"
          class="req-card"
        >
          <div class="req-user">
            <img
              v-if="r.avatar"
              :src="r.avatar"
              class="avatar"
            />
            <div v-else class="avatar placeholder">
              {{ r.sender_username[0]?.toUpperCase() }}
            </div>

            <div class="user-info">
              <div class="name">
                {{ fullName(r) }}
              </div>
              <div class="username">
                {{ r.sender_username }}
              </div>
            </div>
          </div>

          <div class="req-actions">
            <button
              class="btn btn-primary"
              @click="emit('approve', r.uuid)"
            >
              Approve
            </button>

            <button
              class="btn btn-danger"
              @click="emit('reject', r.uuid)"
            >
              Reject
            </button>
          </div>
        </div>
      </div>

      <div v-else class="empty">
        No join requests
      </div>

      <div class="modal-actions">
        <button class="btn btn-danger" @click="emit('close')">
          Close
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.wide {
  width: 720px;
  max-width: 95vw;
}

/* ---- list ---- */

.req-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 12px 0;
  max-height: 420px;
  overflow-y: auto;
}

.req-card {
  border: 1px solid #ddd;
  border-radius: 10px;
  padding: 10px 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

/* ---- user block ---- */

.req-user {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}

.avatar.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ddd;
  font-weight: 600;
  color: #555;
}

.user-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.name {
  font-weight: 600;
  font-size: 14px;
}

.username {
  font-size: 13px;
  color: #666;
}

/* ---- actions ---- */

.req-actions {
  display: flex;
  gap: 8px;
}

.empty {
  text-align: center;
  padding: 24px;
  color: #777;
}
</style>