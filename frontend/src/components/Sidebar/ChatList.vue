<script setup lang="ts">
import { defineProps, defineEmits } from 'vue';
import type { ChatType } from '../../stores/chats';

const props = defineProps<{
  chats: ChatType[];
  selectedChatUuid: string;
}>();

const emit = defineEmits<{
  (e: 'update:selectedChat', chatUuid: string): void;
}>();

function selectChat(chatUuid: string) {
  emit('update:selectedChat', chatUuid);
}
</script>

<template>
  <div class="chat-list">
    <div
      v-for="chat in chats"
      :key="chat.uuid"
      :class="['chat-item', { selected: chat.uuid === selectedChatUuid }]"
      @click="selectChat(chat.uuid)"
    >
      <div class="chat-name">{{ chat.name }}</div>
      <div class="chat-last-message">{{ chat.lastMessage }}</div>
    </div>
  </div>
</template>

<style scoped>
.chat-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px;
}

.chat-item {
  padding: 8px 12px;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.2s;
  display: flex;
  flex-direction: column;
}

.chat-item:hover {
  background-color: #f0f0f0;
}

.chat-item.selected {
  background-color: #d1f5d3;
  font-weight: bold;
}

.chat-name {
  font-weight: bold;
}

.chat-last-message {
  font-size: 0.85rem;
  color: gray;
}
</style>
