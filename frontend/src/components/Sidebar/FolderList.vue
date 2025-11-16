<script setup lang="ts">
import { defineProps, defineEmits, ref } from 'vue';
import { protectedTypes, useFolderStore, type FolderI } from '../../store/folders';
import { useChatStore, type ChatI } from '../../store/chats';
import ChatSelectorModal from '../common/ChatSelectorModal.vue';

const folderStore = useFolderStore()
const chatStore = useChatStore()

const props = defineProps<{
    folders: FolderI[];
    selectFolderUuid: string
}>();

const emit = defineEmits<{
  (e: 'update:selectedFolder', folderId: string): void;
}>();

function selectFolder(folderUuid: string) {
    emit('update:selectedFolder', folderUuid);
}

// ---- CREATE FOLDER ----
const isCreateModalOpen = ref(false)
async function handleCreateSubmit(name: string) {
  await folderStore.createFolder(name)
  isCreateModalOpen.value = false
}

// ---- RENAME FOLDER ----
const isRenameModalOpen = ref(false)
const folderToRename = ref<FolderI | null>(null)

async function handleRenameSubmit(newName: string) {
  if (folderToRename.value) {
    await folderStore.renameFolder(folderToRename.value.uuid, newName)
    isRenameModalOpen.value = false
  }
}

// ---- REPLACE CHATS ----
const isReplaceModalOpen = ref(false)
const folderToReplaceChats = ref<FolderI | null>(null)

async function handleReplaceSubmit(chats: ChatI[]) {
  if (!folderToReplaceChats.value) return
  await folderStore.replaceChats(folderToReplaceChats.value.uuid, chats.map(c => c.uuid))
  isReplaceModalOpen.value = false
}

// ---- CONTEXT MENU ----
const isMenuVisible = ref(false)
const menuX = ref(0)
const menuY = ref(0)
const selectedFolder = ref<FolderI | null>(null)

function openMenu(e: MouseEvent, folder: FolderI) {
  e.stopPropagation()
  e.preventDefault()

  if (protectedTypes.includes(folder.folder_type)) return

  selectedFolder.value = folder
  menuX.value = e.clientX
  menuY.value = e.clientY
  isMenuVisible.value = true
}

function closeMenu() {
  isMenuVisible.value = false
}

async function handleDelete() {
  if (selectedFolder.value) await folderStore.deleteFolder(selectedFolder.value.uuid)
  closeMenu()
}

function handleRename() {
  if (!selectedFolder.value) return
  folderToRename.value = selectedFolder.value
  isRenameModalOpen.value = true
  closeMenu()
}

function handleReplaceChats() {
  if (!selectedFolder.value) return
  folderToReplaceChats.value = selectedFolder.value
  isReplaceModalOpen.value = true
  closeMenu()
}
</script>

<template>
  <div class="folder-list">
    <div
      v-for="folder in folders"
      :key="folder.uuid"
      :class="['folder-item', {selected: folder.uuid === selectFolderUuid}]"
      @click.left.prevent="selectFolder(folder.uuid)"
      @click.right.prevent="openMenu($event, folder)"
    >
      {{ folder.name || folder.folder_type }}
    </div>
  </div>

  <button @click="isCreateModalOpen = true" class="add-folder-btn">
    <i class="bi bi-plus-circle"></i>
  </button>

  <!-- Creating Modal -->
  <ModalTextInput
    v-if="isCreateModalOpen"
    :visible="isCreateModalOpen"
    title="Create new folder"
    placeholder="Enter folder name"
    @submit="handleCreateSubmit"
    @close="isCreateModalOpen = false"
  />

  <!-- Renaming Modal -->
  <ModalTextInput
    v-if="isRenameModalOpen"
    :visible="isRenameModalOpen"
    title="Rename folder"
    :placeholder="folderToRename?.name || 'Enter new name'"
    @submit="handleRenameSubmit"
    @close="isRenameModalOpen = false"
  />

  <!-- Replacing Modal -->
  <ChatSelectorModal
    :visible="isReplaceModalOpen"
    title="Choose Chats"
    placeholder="Search for chats"
    :chats="chatStore.chats"
    :filterFn="(chat: ChatI) => folderToReplaceChats?.chat_uuids.includes(chat.uuid) ?? false"
    @submit="handleReplaceSubmit"
    @close="isReplaceModalOpen = false"
  />

  <!-- Context Menu -->
  <ContextMenu
    :visible="isMenuVisible"
    :x="menuX"
    :y="menuY"
    :items="[
      { label: 'Rename', action: handleRename },
      { label: 'Delete', action: handleDelete },
      { label: 'Replace Chats', action: handleReplaceChats },
    ]"
    @close="closeMenu"
  />
</template>

<style>
.folder-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px;
}

.folder-item {
  padding: 8px 12px;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.2s;
}

.folder-item:hover {
  background-color: #f0f0f0;
}

.folder-item.selected {
  background-color: #d1f5d3;
  font-weight: bold;
}

.add-folder-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 28px;
  color: black;
  transition: color 0.2s;
  margin: 0 auto;
  display: block;
}

.add-folder-btn:hover {
  color: gray;
}
</style>
