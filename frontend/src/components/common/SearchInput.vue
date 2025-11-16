<script setup lang="ts">
import { watch, ref, computed } from 'vue';

const props = defineProps<{
    placeholder?: string
    filterFn: (item: any, query: string) => boolean
    items: any[]
}>()

const emit = defineEmits<{
  (e: 'filtered', value: any[]): void
}>()

const query = ref("");

const filtered = computed(() => {
  const q = query.value.toLowerCase().trim()
  if (!q) return props.items

  return props.items.filter(item => {
    return props.filterFn(item, q)
  })
})

watch(filtered, () => {
  emit('filtered', filtered.value)
}, { immediate: true })
</script>

<template>
  <div class="search-input">
    <input
      type="text"
      v-model="query"
      class="form-control"
      :placeholder="placeholder ?? 'Search...'"
    />
  </div>
</template>
