<script setup lang="ts">
import { useFolderStore } from '../store/folders';
import { useChatStore } from '../store/chats';
import { useMessageStore, type MessageI } from '../store/messages';

import FolderList from '../components/Sidebar/FolderList.vue';
import ChatList from '../components/Sidebar/ChatList.vue';
import ChatWindow from '../components/Chat/ChatWindow.vue';

const folderStore = useFolderStore();
const chatStore = useChatStore();
const messageStore = useMessageStore();

function handleSendMessage(msg: MessageI) {
  messageStore.addMessage(msg);
}

async function fetchData() {
  // await folderStore.fetchFolders();
  await chatStore.fetchChats();
}
</script>

<template>
  <div class="messenger">
    <div class="folders">
    </div>

    <div class="chats">
    </div>

    <button v-on:click="fetchData"></button>

    <div class="chat-window">
      <ChatWindow
        :chatUuid="chatStore.selectedChatUuid"
        :messages="messageStore.getMessagesByChat(chatStore.selectedChatUuid)"
        @sendMessage="handleSendMessage"
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
  width: 200px;
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
