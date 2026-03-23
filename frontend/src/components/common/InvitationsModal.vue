<script setup lang="ts">
import { ref } from 'vue'
import type { InvitationI, InvitationLifeTimeType } from '../../store/invitations'

const props = defineProps<{
  visible: boolean
  invitations: InvitationI[]
  title: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'delete', uuid: string): void
  (e: 'create', payload: {
    lifetime: InvitationLifeTimeType
    max_uses: number | null
  }): void
}>()

/* ---------- Create form state ---------- */
const lifetime = ref<InvitationLifeTimeType>('1h')
const maxUses = ref<number | null>(null)

function createInvite() {
  emit('create', {
    lifetime: lifetime.value,
    max_uses: maxUses.value || null
  })
}

/* ---------- Helpers ---------- */
function inviteLink(uuid: string) {
  return `${import.meta.env.VITE_FRONT_ENDPOINT}/invite/${uuid}`
}

async function copy(uuid: string) {
  await navigator.clipboard.writeText(inviteLink(uuid))
}

function lifetimeLabel(l: string) {
  switch (l) {
    case '10m': return '10 minutes'
    case '1h': return '1 hour'
    case '1d': return '1 day'
    default: return 'Unlimited'
  }
}
</script>

<template>
  <div v-if="visible" class="modal-overlay" @click.self="emit('close')">
    <div class="modal-content wide two-col">
      <h3>{{ title }}</h3>

      <div class="layout">
        <!-- LEFT: invitations list -->
        <div class="left">
          <div v-if="invitations.length" class="invite-list">
            <div
              v-for="i in invitations"
              :key="i.uuid"
              class="invite-card"
            >
              <div class="invite-main">
                <div class="invite-link">
                  {{ inviteLink(i.uuid) }}
                </div>

                <div class="invite-meta">
                  <span>⏳ {{ lifetimeLabel(i.lifetime) }}</span>
                  <span v-if="i.max_uses">🔢 {{ i.max_uses }} uses</span>
                  <span v-else>♾ unlimited</span>
                </div>
              </div>

              <div class="invite-actions">
                <button class="btn" @click="copy(i.uuid)">Copy</button>
                <button
                  class="btn btn-danger"
                  @click="emit('delete', i.uuid)"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>

          <div v-else class="empty">
            No invitations yet
          </div>
        </div>

        <!-- RIGHT: create form -->
        <div class="right">
          <h4>Create invitation</h4>

          <label>Lifetime</label>
          <select v-model="lifetime" class="input">
            <option value="10m">10 minutes</option>
            <option value="1h">1 hour</option>
            <option value="1d">1 day</option>
            <option value="unlimited">Unlimited</option>
          </select>

          <label>Max uses</label>
          <input
            type="number"
            min="1"
            class="input"
            v-model.number="maxUses"
            placeholder="Unlimited"
          />

          <div class="modal-actions">
            <button class="btn btn-primary" @click="createInvite">
              Create invitation
            </button>
          </div>
        </div>
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
  width: 900px;
  max-width: 95vw;
}

.layout {
  display: flex;
  gap: 20px;
  margin-top: 10px;
}

.left {
  flex: 2;
  min-width: 0;
}

.right {
  flex: 1;
  border-left: 1px solid #eee;
  padding-left: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.input {
  padding: 6px 8px;
  border-radius: 6px;
  border: 1px solid #ccc;
  font-size: 14px;
}

/* ---- invitations ---- */

.invite-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 12px 0;
  max-height: 420px;
  overflow-y: auto;
}

.invite-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 10px;
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.invite-main {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.invite-link {
  font-family: monospace;
  font-size: 13px;
  word-break: break-all;
}

.invite-meta {
  display: flex;
  gap: 12px;
  font-size: 13px;
  color: #666;
}

.invite-actions {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.empty {
  text-align: center;
  padding: 24px;
  color: #777;
}
</style>