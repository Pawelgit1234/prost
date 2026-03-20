<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue';
import { useMessageStore, type MessageI } from '../../store/messages';
import { useWebSocketStore } from '../../store/websocket';
import { useAuthStore } from '../../store/auth';
import Message from './Message.vue';
import { useUserStore } from '../../store/users';
import { useChatStore, type GroupConfigI } from '../../store/chats';
import { useS3Store } from '../../store/s3';

const props = defineProps<{
  selectedChatUuid: string
  messageToScroll: string | null
}>();

const websocketStore = useWebSocketStore()
const chatStore = useChatStore()
const messageStore = useMessageStore()
const userStore = useUserStore()
const authStore = useAuthStore()
const s3Store = useS3Store()

watch(
  () => props.selectedChatUuid,
  async (chatUuid) => {
    if (!chatUuid) return

    await messageStore.fetchMessages(chatUuid)
    websocketStore.readMessage(chatUuid)

    scrollToBottom()
  },
  { immediate: true }
)

watch(
  () => props.messageToScroll,
  async (messageUuid) => {
    if (!messageUuid) return

    const message = messageStore.getMessageByUuid(messageUuid)
    if (message) {
      chatStore.selectChat(message.chat_uuid)
      await messageStore.fetchMessages(message?.chat_uuid)
      websocketStore.readMessage(message?.chat_uuid)
    }

    await nextTick()

    const el = document.getElementById(`message-${messageUuid}`)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }
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
const messagesRef = ref<HTMLElement | null>(null)

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

function openStatuses(msg: MessageI) {
  selectedMessage.value = msg
  showStatuses.value = true
}

const chat = computed(() =>
  chatStore.getChatByUuid(props.selectedChatUuid)
)

const isNormal = computed(() =>
  chat.value?.chat_type === 'normal'
)

// Config
const showGroupSettings = ref(false);
async function onSaveGroup(config: GroupConfigI) {
  await chatStore.saveConfig(config)
  showGroupSettings.value = false
}

async function onUploadAvatar(file: File) {
  if (!chat.value) return
  await s3Store.saveGroupAvatar(file, chat.value)
  showGroupSettings.value = false
}
</script>

<template>
  <div class="chat-window-header">
    <b>{{ chat?.name }}</b>
    <button v-if="!isNormal" @click="" class="icon-btn">
      <i class="bi bi-qr-code"></i>
    </button>
    <button v-if="!isNormal" @click="" class="icon-btn">
      <i class="bi bi-envelope"></i>
    </button>
    <button v-if="!isNormal" @click="showGroupSettings=true" class="icon-btn">
      <i class="bi bi-list"></i>
    </button>
    <button @click="" class="icon-btn">
      <i class="bi bi-download"></i>
    </button>
  </div>
  <div class="chat-window-inner">
    <div class="message-list" ref="messagesRef">
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

  <GroupConfigModal
    :visible="showGroupSettings"
    :group="chat"
    @save="onSaveGroup"
    @avatar="onUploadAvatar"
    @close="showGroupSettings = false"
  />

  <ReadStatusesModal
    :visible="showStatuses"
    :read-statuses="selectedMessage?.read_statuses ?? []"
    :users="[...(userStore.getChatUsers(selectedChatUuid) || []), authStore.currentUser]"
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

.chat-window-header {
  margin-left: 20px;
}
</style>
