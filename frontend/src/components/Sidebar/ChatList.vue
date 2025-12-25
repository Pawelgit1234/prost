<script setup lang="ts">
import type { ChatI } from '../../store/chats';
import type FolderSelectorModal from '../common/FolderSelectorModal.vue';
import { useFolderStore, type FolderI } from '../../store/folders';
import { computed, ref } from 'vue';

const props = defineProps<{
  chats: ChatI[];
  selectedChatUuid: string;
}>();

const emit = defineEmits<{
  (e: 'update:selectedChat', chatUuid: string): void;
}>();

function selectChat(chatUuid: string) {
  emit('update:selectedChat', chatUuid);
}

const folderStore = useFolderStore()

// ---- ADD CHAT TO FOLDER ----
const isAddToFolderModalOpen = ref(false)
const chatToAddInFolder = ref<ChatI | null>(null)

async function handleAddChatToFolderSubmit(folders: FolderI[]) {
  if (!chatToAddInFolder.value) return
  await folderStore.addChatToFolders(chatToAddInFolder.value, folders)
  isAddToFolderModalOpen.value = false
}

// ---- CONTEXT MENU ----
const isMenuVisible = ref(false)
const menuX = ref(0)
const menuY = ref(0)
const selectedChat = ref<ChatI | null>(null)

function openMenu(e: MouseEvent, chat: ChatI) {
  e.stopPropagation()
  e.preventDefault()

  selectedChat.value = chat
  menuX.value = e.clientX
  menuY.value = e.clientY
  isMenuVisible.value = true
}

function closeMenu() {
  isMenuVisible.value = false
}

async function handleAddChatToFolder() {
  if (!selectedChat.value) return;

  chatToAddInFolder.value = selectedChat.value
  isAddToFolderModalOpen.value = true
}

async function handlePinChat() {
  if (!selectedChat.value) return
  if (!folderStore.selectedFolder) return
  await folderStore.handlePin(folderStore.selectedFolder.uuid, selectedChat.value.uuid)
}

const pinned_chats = computed(() => 
  props.chats.filter(chat => folderStore.isChatPinned(chat.uuid))
)
const unpinned_chats = computed(() => 
  props.chats.filter(chat => !folderStore.isChatPinned(chat.uuid))
)

async function handleDeleteChat() {

}

async function handleQuitGroup() {

}

async function handleAddUserToGroup() {
  
}
</script>

<template>
  
  <div class="chat-list">
    <div
      v-for="chat in pinned_chats"
      :key="chat.uuid"
      :class="['chat-item', { selected: chat.uuid === selectedChatUuid }]"
      @click.left.prevent="selectChat(chat.uuid)"
      @click.right.prevent="openMenu($event, chat)"
    >
      <i class="bi bi-pin-angle-fill pin-icon"></i>
      <div class="chat-name">{{ chat.name }}</div>
      <div class="chat-last-message">{{ chat.last_message }}</div>
    </div>

    <div
      v-for="chat in unpinned_chats"
      :key="chat.uuid"
      :class="['chat-item', { selected: chat.uuid === selectedChatUuid }]"
      @click.left.prevent="selectChat(chat.uuid)"
      @click.right.prevent="openMenu($event, chat)"
    >
      <div class="chat-name">{{ chat.name }}</div>
      <div class="chat-last-message">{{ chat.last_message }}</div>
    </div>
  </div>

  <!-- Context Menu -->
  <ContextMenu
    :visible="isMenuVisible"
    :x="menuX"
    :y="menuY"
    :items="[
      { label: 'Add to Folder', action: handleAddChatToFolder },
      {label: 'Pin', action: handlePinChat },
      { label: 'Delete Chat', action: handleDeleteChat },
      { label: 'Add User to Group', action: handleAddUserToGroup },
      { label: 'Quit', action: handleQuitGroup },
    ]"
    @close="closeMenu"
  />

  <!-- Add Chat to Folder Modal -->
  <FolderSelectorModal
    :visible="isAddToFolderModalOpen"
    title="Choose Folders"
    :folders="folderStore.folders.filter(f => f.folder_type === 'custom')"
    :filterFn="(folder: FolderI) => {
      if (!chatToAddInFolder) return false;
      return folder.chat_uuids.includes(chatToAddInFolder.uuid);
    }" 
    @close="isAddToFolderModalOpen = false"
    @submit="handleAddChatToFolderSubmit"
  />
</template>

<style scoped>
.chat-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px;
}

.chat-item {
  position: relative;
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

.pin-icon {
  position: absolute;
  top: 6px;
  right: 6px;
  font-size: 0.9rem;
  color: #665;
}

.chat-name {
  font-weight: bold;
}

.chat-last-message {
  font-size: 0.85rem;
  color: gray;
}

.chat-name,
.chat-last-message {
  padding-right: 20px;
}

.chat-item:hover .pin-icon {
  transform: rotate(-20deg);
  transition: transform 0.2s ease;
}

</style>
