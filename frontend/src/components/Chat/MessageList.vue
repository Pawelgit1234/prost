<script setup lang="ts">
import Message from './Message.vue'
import type { MessageI } from '../../store/messages';

const props = defineProps<{ // ToDo: Props на pinia
  messages: MessageI[]
}>()
</script>

<template>
  <div class="message-list">
    <Message
      v-for="m in messages"
      :key="m.uuid"
      v-bind="m"
    />
  </div>
</template>

<style scoped>
.message-list {
  flex: 1;
  padding: 10px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}
</style>
