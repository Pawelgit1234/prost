<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import SearchInput from './SearchInput.vue';
import type { ChatI } from '../../store/chats';

const props = defineProps<{
  visible: boolean
  title: string
  placeholder?: string
  chats: ChatI[]
  filterFn: (chat: ChatI) => boolean // true -> in matched
}>()

const emit = defineEmits<{
  (e: 'submit', value: ChatI[]): void
  (e: 'close'): void
}>()

const selected = ref(props.chats.filter(c => props.filterFn(c)))

const unselected = computed(() => {
    return props.chats.filter(c => !selected.value.includes(c))
})

const filteredUnmatched = ref<ChatI[]>([])

watch(() => props.visible, (val) => {
  if (val) {
    selected.value = props.chats.filter(c => props.filterFn(c));
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
                  v-for="c in selected"
                  :key="c.uuid"
                  @click="selected = selected.filter(x => x !== c)"
                  class="chat-item"
                >
                    {{ c.name }}
                </div>
            </div>

            <hr>

            <SearchInput
                :placeholder="placeholder"
                :items="unselected"
                :filterFn="(chat, q) => chat.name.toLowerCase().includes(q)"
                @filtered="val => filteredUnmatched = val"
            />

            <hr>

            <h4>Available</h4>
            <div class="scroll-box">
                <div v-for="c in filteredUnmatched" :key="c.uuid" @click="selected.push(c)" class="chat-item">
                    {{ c.name }}
                </div>
            </div>

            <div class="modal-actions">
                <button class="btn btn-primary" @click="emit('submit', selected)">Submit</button>
                <button class="btn btn-danger" @click="emit('close')">Cancel</button>
            </div>
        </div>
    </div>
</template>

<style scoped>
.scroll-box {
  max-height: 200px;
  overflow-y: auto;
  padding: 6px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: #fafafa;
  margin-bottom: 12px;
}

.chat-item {
  padding: 6px 8px;
  border-radius: 4px;
  margin-bottom: 4px;
  cursor: pointer;
  transition: background 0.2s;
}

.chat-item:hover {
  background: #e8e8e8;
}
</style>
