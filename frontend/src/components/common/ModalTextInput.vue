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
