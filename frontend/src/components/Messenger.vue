<script setup lang="ts">
import { ref } from 'vue';
import type { ChatType, MessageType, FolderType } from './types';
import ChatList from './Sidebar/ChatList.vue';
import FolderList from './Sidebar/FolderList.vue';
import ChatWindow from './Chat/ChatWindow.vue';

// Test folders
const folders = ref<FolderType[]>([
  { uuid: 'f1', name: 'General', pos: 1},
  { uuid: 'f2', name: 'Work', pos: 2},
  { uuid: 'f3', name: 'Personal', pos: 3},
]);

// Test chats
const chats = ref<ChatType[]>([
  { uuid: 'c1', folderUuid: 'f1', name: 'General Chat', is_pinned: false},
  { uuid: 'c2', folderUuid: 'f2', name: 'Project Alpha', is_pinned: true},
  { uuid: 'c3', folderUuid: 'f2', name: 'Project Beta', is_pinned: false },
  { uuid: 'c4', folderUuid: 'f3', name: 'Family', is_pinned: false},
]);

// Test messages
const messages = ref<MessageType[]>([
  { uuid: 'm1', chatUuid: 'c1', author: 'Alice', text: 'Hello!', datetime: '10:00', wasUpdated: false, isMine: true },
  { uuid: 'm2', chatUuid: 'c1', author: 'Bob', text: 'Hi, Alice!', datetime: '10:01', wasUpdated: false, isMine: false },
  { uuid: 'm3', chatUuid: 'c2', author: 'Carol', text: 'Docs are ready', datetime: '11:00', wasUpdated: true, isMine: true },
  { uuid: 'm4', chatUuid: 'c4', author: 'Dave', text: 'When is dinner?', datetime: '18:30', wasUpdated: false, isMine: false },
]);

// Current selected folder and chat
const selectedFolderUuid = ref('f1');
const selectedChatUuid = ref('c1');
</script>

<template>
  <div class="messenger">
    <div class="folders">
        <FolderList
            :folders="folders"
            :selectFolderUuid="selectedFolderUuid"
            @update:selectedFolder="selectedFolderUuid = $event"
        />
    </div>
    <div class="chats">
        <ChatList
            :chats="chats.filter(c => c.folderUuid === selectedFolderUuid)"
            :selectedChatUuid="selectedChatUuid"
            @update:selectedChat="selectedChatUuid = $event"
        />
    </div>
    <div class="chat-window">
        <ChatWindow/>
    </div>
  </div>
</template>

<style>
</style>
