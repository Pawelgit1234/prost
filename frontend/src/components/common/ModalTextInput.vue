<script setup lang="ts">
import { defineProps, defineEmits, ref } from 'vue'

const props = defineProps<{
  visible: boolean
  title: string
  placeholder?: string
}>()

const emit = defineEmits<{
  (e: 'submit', value: string): void
  (e: 'close'): void
}>()

const inputValue = ref('')

function handleSubmit() {
  if (inputValue.value.trim()) {
    emit('submit', inputValue.value.trim())
  }
}
</script>

<template>
  <div v-if="visible" class="modal-overlay" @click.self="emit('close')">
    <div class="modal-content">
      <h3>{{ title }}</h3>
      <input
        v-model="inputValue"
        :placeholder="placeholder"
        @keyup.enter="handleSubmit"
      />
      <div class="modal-actions">
        <button class="btn btn-primary" @click="handleSubmit">OK</button>
        <button class="btn btn-danger" @click="emit('close')">Cancel</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 20px;
  border-radius: 8px;
  width: 400px;
  max-width: 90%;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.3);
}

.modal-actions {
  display: flex;
  justify-content: flex-start;
  gap: 10px;
  margin-top: 15px;
}
</style>
