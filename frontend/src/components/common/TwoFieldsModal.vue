<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  visible: boolean
  title: string
  placeholder1?: string
  placeholder2?: string
}>()

const emit = defineEmits<{
  (e: 'submit', value1: string, value2: string): void
  (e: 'close'): void
}>()

const value1 = ref('')
const value2 = ref('')

function handleSubmit() {
  const v1 = value1.value.trim()
  const v2 = value2.value.trim()

  if (!v1) return

  emit('submit', v1, v2)
}

watch(() => props.visible, (v) => {
  if (v) {
    value1.value = ''
    value2.value = ''
  }
})
</script>

<template>
  <div v-if="visible" class="modal-overlay" @click.self="emit('close')">
    <div class="modal-content">
      <h3>{{ title }}</h3>

      <div class="inputs">
        <input
          v-model="value1"
          :placeholder="placeholder1"
          @keyup.enter="handleSubmit"
        />

        <input
          v-model="value2"
          :placeholder="placeholder2"
          @keyup.enter="handleSubmit"
        />
      </div>

      <div class="modal-actions">
        <button class="btn btn-primary" @click="handleSubmit">OK</button>
        <button class="btn btn-danger" @click="emit('close')">Cancel</button>
      </div>
    </div>
  </div>
</template>

<style>
.inputs {
  display: flex;
  flex-direction: column;
  gap: 24px;
  margin-bottom: 10px;
}
</style>