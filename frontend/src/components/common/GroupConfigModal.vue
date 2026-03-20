<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import type { ChatI, GroupConfigI } from '../../store/chats';

const props = defineProps<{
  visible: boolean
  group: ChatI | null
}>()

const emit = defineEmits<{
  (e: 'save', config: GroupConfigI): void
  (e: 'avatar', file: File): void
  (e: 'close'): void
}>()

const form = ref<GroupConfigI>({
  uuid: '',
  name: '',
  description: null,
  is_visible: true,
  is_open_for_messages: true,
  avatar_url: null,
})

const avatarFile = ref<File | null>(null)

function onAvatarChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files?.length) return
  avatarFile.value = input.files[0]
}

const previewUrl = computed(() => {
  if (avatarFile.value) return URL.createObjectURL(avatarFile.value)
  return form.value.avatar_url
})

watch(
  () => props.visible,
  (v) => {
    if (!v || !props.group) return

    form.value = {
      uuid: props.group.uuid,
      name: props.group.name,
      description: props.group.description,
      is_visible: props.group.is_visible,
      is_open_for_messages: props.group.is_open_for_messages,
      avatar_url: props.group.avatar ?? null,
    }

    avatarFile.value = null
  },
  { immediate: true }
)

function save() {
  emit('save', form.value)
  if (avatarFile.value) emit('avatar', avatarFile.value)
}
</script>

<template>
  <div v-if="visible" class="modal-overlay" @click.self="emit('close')">
    <div class="modal-content">
      <h3>Group settings</h3>

      <img
        v-if="previewUrl"
        :src="previewUrl"
        class="avatar-preview"
      />

      <div class="form-grid">
        <label>
          Group name
          <input v-model="form.name" />
        </label>

        <label>
          Description
          <textarea v-model="form.description"/>
        </label>

        <label class="row">
          Visible group
          <input type="checkbox" v-model="form.is_visible" />
        </label>

        <label class="row">
          Open for messages
          <input type="checkbox" v-model="form.is_open_for_messages" />
        </label>

        <label>
          Avatar
          <input type="file" accept="image/*" @change="onAvatarChange" />
        </label>
      </div>

      <div class="modal-actions">
        <button class="btn btn-primary" @click="save">Save</button>
        <button class="btn btn-danger" @click="emit('close')">Cancel</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.form-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.form-grid input,
.form-grid textarea {
  width: 100%;
  padding: 6px;
}

.row {
  margin-left: 5px;
  display: flex;
  align-items: center;
  gap: 8px;
  line-height: 1;
}

.row input[type="checkbox"] {
  margin: 0;
  width: 16px;
  height: 16px;
}

.avatar-preview {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  object-fit: cover;
  margin-bottom: 10px;
}
</style>