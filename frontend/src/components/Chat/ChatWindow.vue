<script setup lang="ts">
import { ref, watch, nextTick } from 'vue';
import type { MessageType } from '../../stores/messages';
import MessageList from './MessageList.vue';

const props = defineProps<{
  chatUuid: string;
  messages: MessageType[];
}>();

const emit = defineEmits<{
  (e: 'sendMessage', msg: MessageType): void;
}>();

const newMessage = ref('');
const messagesRef = ref<HTMLElement | null>(null);

// Autoscroll down
watch(() => props.messages.length, async () => {
  await nextTick();
  messagesRef.value?.scrollTo({ top: messagesRef.value.scrollHeight });
});

function sendMessage() {
  if (!newMessage.value.trim()) return;

  const msg: MessageType = {
    chatUuid: props.chatUuid,
    author: 'Me',
    text: newMessage.value,
    datetime: new Date().toLocaleTimeString().slice(0, 5),
    isMine: true,
    wasUpdated: false,
    uuid: crypto.randomUUID(),
  };

  emit('sendMessage', msg);
  newMessage.value = '';
}
</script>

<template>
  <div class="chat-window-inner" ref="messagesRef">
    <MessageList :messages="messages"/>
    <div class="input">
      <input
        v-model="newMessage"
        type="text"
        placeholder="Write a message..."
        @keyup.enter="sendMessage"
      />
      <button @click="sendMessage">Send</button>
    </div>
  </div>
</template>

<style>
.chat-window-inner {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.input {
  display: flex;
  gap: 8px;
  padding: 10px;
  border-top: 1px solid #ccc;
}

.input input {
  flex: 1;
  padding: 8px;
  border-radius: 6px;
  border: 1px solid #ccc;
}

.input button {
  padding: 8px 12px;
  border: none;
  background: #4caf50;
  color: white;
  border-radius: 6px;
  cursor: pointer;
}

.input button:hover {
  background: #43a047;
}
</style>
