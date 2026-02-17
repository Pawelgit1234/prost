<script setup lang="ts">
import { ref, watch } from 'vue';
import { useMessageStore, type MessageI } from '../../store/messages';
import { useWebSocketStore } from '../../store/websocket';
import { useAuthStore } from '../../store/auth';
import Message from './Message.vue';
import { useUserStore } from '../../store/users';

const props = defineProps<{
  selectedChatUuid: string;
}>();

const websocketStore = useWebSocketStore()
const messageStore = useMessageStore()
const userStore = useUserStore()
const authStore = useAuthStore()

watch(
  () => props.selectedChatUuid,
  async (chatUuid) => {
    if (!chatUuid) return

    await messageStore.fetchMessages(chatUuid)
  },
  { immediate: true }
)

const newMessage = ref('');

async function sendMessage() {
  if (!authStore.currentUser?.uuid) return
  if (newMessage.value.length == 0) return

  websocketStore.sendMessage(
    props.selectedChatUuid, authStore.currentUser.uuid, newMessage.value
  )

  newMessage.value = ''
}

const showStatuses = ref(false)
const selectedMessage = ref<MessageI | null>(null)

function openStatuses(msg: MessageI) {
  selectedMessage.value = msg
  showStatuses.value = true
}

</script>

<template>
  <div class="chat-window-inner" ref="messagesRef">

    <div class="message-list">
      <Message
        v-for="msg in messageStore.getMessagesByChat(selectedChatUuid)"
        :key="msg.uuid"
        :message="msg"
        @click.right.prevent="openStatuses(msg)"
      />
    </div>

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

  <ReadStatusesModal
    :visible="showStatuses"
    :read-statuses="selectedMessage?.read_statuses ?? []"
    :users="userStore.getChatUsers(selectedChatUuid)"
    @close="showStatuses = false"
  />
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

.message-list {
  flex: 1;
  padding: 10px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}
</style>
