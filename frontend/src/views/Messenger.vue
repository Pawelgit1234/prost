<script setup lang="ts">
import { useFolderStore } from '../store/folders';
import { useChatStore } from '../store/chats';

import ChatWindow from '../components/Chat/ChatWindow.vue';
import { onMounted, ref } from 'vue';
import FolderList from '../components/Sidebar/FolderList.vue';
import ChatList from '../components/Sidebar/ChatList.vue';
import { useUserStore } from '../store/users';
import { useSearchStore } from '../store/search';
import { useWebSocketStore } from '../store/websocket';

const folderStore = useFolderStore()
const chatStore = useChatStore()
const userStore = useUserStore()
const searchStore = useSearchStore()
const ws = useWebSocketStore()

onMounted(async () => {
  await Promise.all([
    folderStore.fetchFolders(),
    chatStore.fetchChats(),
    userStore.fetchUsers(),
    searchStore.loadHistory(),
  ])
  ws.connect()
})

const messageToScroll = ref<string | null>(null)

function handleChooseMessage(messageUuid: string) {
  messageToScroll.value = messageUuid
}

</script>

<template>
  <div class="messenger">
    <div class="folders">
      <FolderList
        :folders="folderStore.folders"
        :selectFolderUuid="folderStore.selectedFolderUuid"
        @update:selectedFolder="folderStore.selectFolder"
      />
    </div>

    <div class="chats">
      <ChatList
        :chats="chatStore.chatsOfSelectedFolder"
        :selectedChatUuid="chatStore.selectedChatUuid"
        @update:selectedChat="chatStore.selectChat"
        @choosedMessage="handleChooseMessage"
      />
    </div>

    <div class="chat-window">
      <ChatWindow
        :selectedChatUuid="chatStore.selectedChatUuid"
        :messageToScroll="messageToScroll"
      />
    </div>
  </div>
</template>

<style>
.messenger {
  display: flex;
  height: 100vh;
  gap: 10px;
}

.folders {
  width: 150px;
  border-right: 1px solid #ccc;
  overflow-y: auto;
}

.chats {
  width: 250px;
  border-right: 1px solid #ccc;
  overflow-y: auto;
}

.chat-window {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  background-color: #f9f9f9;
}
</style>
