<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps<{
  items: { label: string; action: () => void; disabled?: boolean }[]
  x: number
  y: number
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const menuRef = ref<HTMLElement | null>(null)

function handleClickOutside(e: MouseEvent) {
  if (menuRef.value && !menuRef.value.contains(e.target as Node)) {
    emit('close')
  }
}

onMounted(() => document.addEventListener('mousedown', handleClickOutside))
onBeforeUnmount(() => document.removeEventListener('mousedown', handleClickOutside))
</script>

<template>
  <div
    v-if="visible"
    class="context-menu"
    :style="{ top: y + 'px', left: x + 'px' }"
    ref="menuRef"
  >
    <div
      v-for="(item, index) in items"
      :key="index"
      class="context-item"
      :class="{ disabled: item.disabled }"
      @click="!item.disabled && item.action(); emit('close')"
    >
      {{ item.label }}
    </div>
  </div>
</template>

<style scoped>
.context-menu {
  position: fixed;
  background: white;
  border: 1px solid #ccc;
  border-radius: 6px;
  box-shadow: 0 4px 8px rgba(0,0,0,0.15);
  padding: 6px 0;
  min-width: 140px;
  z-index: 9999;
}

.context-item {
  padding: 8px 12px;
  cursor: pointer;
  transition: background 0.2s;
}

.context-item:hover {
  background-color: #f0f0f0;
}

.context-item.disabled {
  color: #aaa;
  cursor: not-allowed;
  pointer-events: none;
}
</style>
