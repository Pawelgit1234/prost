<script setup lang="ts" generic="T">
import { computed, watch, shallowRef } from 'vue';
import SearchInput from './SearchInput.vue';

const props = defineProps<{
  visible: boolean
  title: string
  placeholder?: string

  items: T[]
  filterFn: (item: T) => boolean // true -> in selected
  getKey: (item: T) => string | number // key
  getLabel: (item: T) => string 
}>()

const emit = defineEmits<{
  (e: 'submit', value: T[]): void
  (e: 'close'): void
}>()

const selected = shallowRef(props.items.filter(i => props.filterFn(i)))
const unselected = computed(() => {
    return props.items.filter(i => !selected.value.includes(i))
})

const filteredUnmatched = shallowRef<T[]>([])

watch(() => props.visible, (val) => {
  if (val) {
    selected.value = props.items.filter(i => props.filterFn(i));
  }
});
</script>

<template>
    <div v-if="visible" class="modal-overlay" @click.self="emit('close')">
        <div class="modal-content">
            <h3>{{ title }}</h3>

            <h4>Selected</h4>
            <div class="scroll-box">
                <div
                  v-for="i in selected"
                  :key="getKey(i)"
                  @click="selected = selected.filter(x => x !== i)"
                  class="scroll-box-item"
                >
                    {{ getLabel(i) }}
                </div>
            </div>

            <hr>

            <SearchInput
                :placeholder="placeholder"
                :items="unselected"
                :filterFn="(item, q) => getLabel(item).toLowerCase().includes(q)"
                @filtered="val => filteredUnmatched = val"
            />

            <hr>

            <h4>Available</h4>
            <div class="scroll-box">
                <div v-for="i in filteredUnmatched" 
                :key="getKey(i)"
                @click="selected = [...selected, i]"
                class="scroll-box-item">
                    {{ getLabel(i) }}
                </div>
            </div>

            <div class="modal-actions">
                <button class="btn btn-primary" @click="emit('submit', selected)">Submit</button>
                <button class="btn btn-danger" @click="emit('close')">Cancel</button>
            </div>
        </div>
    </div>
</template>
