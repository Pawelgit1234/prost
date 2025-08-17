<script setup lang="ts">
import { ref } from 'vue';
import type { Message } from '../types';
import MessageList from './MessageList.vue'

const messages = ref<Message[]>([
  {
    uuid: crypto.randomUUID(),
    text: "Hello",
    author: "Andry",
    datetime: "12:34",
    isMine: false,
    wasUpdated: false
  }
])

const newMessage = ref(""); // input

function sendMessage() {
  if (!newMessage.value.trim()) return

  messages.value.push({
    uuid: crypto.randomUUID(),
    text: newMessage.value,
    author: "Me",
    datetime: new Date().toLocaleTimeString().slice(0, 5),
    isMine: true,
    wasUpdated: false
  })

  newMessage.value = ""
}

</script>

<template>
    <div class="chat-window">
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
.chat-window {
  display: flex;
  flex-direction: column;
  height: 100vh; /* во всю высоту экрана */
  border: 1px solid #ccc;
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
