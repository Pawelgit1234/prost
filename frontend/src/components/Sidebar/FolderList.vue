<script setup lang="ts">
import { defineProps, defineEmits, ref } from 'vue';
import { useFolderStore, type FolderI } from '../../store/folders';
import ModalTextInput from '../../common/ModalTextInput.vue';
import ContextMenu from '../../common/ContextMenu.vue';

const folderStore = useFolderStore()

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

const isModalOpen = ref(false)

async function handleSubmit(name: string) {
  await folderStore.createFolder(name)
  isModalOpen.value = false
}

const isMenuVisible = ref(false)
const menuX = ref(0)
const menuY = ref(0)
const selectedFolder = ref<FolderI | null>(null)

function openMenu(e: MouseEvent, folder: FolderI) {
  e.stopPropagation()

  const protectedTypes = ['all', 'chats', 'groups', 'new']
  if (protectedTypes.includes(folder.folder_type)) return

  selectedFolder.value = folder
  menuX.value = e.clientX
  menuY.value = e.clientY
  isMenuVisible.value = true
}

function closeMenu() {
  isMenuVisible.value = false
}

// context menu actions
async function handleDelete() {
  if (selectedFolder.value) await folderStore.deleteFolder(selectedFolder.value.uuid)
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

    <button @click="isModalOpen = true" class="add-folder-btn">
      <i class="bi bi-plus-circle"></i>
    </button>

    <ModalTextInput
      v-if="isModalOpen"
      :visible="isModalOpen"
      title="Create new folder"
      placeholder="Enter folder name"
      @submit="handleSubmit"
      @close="isModalOpen = false"
    />

    <!-- Context Menu -->
    <ContextMenu
      :visible="isMenuVisible"
      :x="menuX"
      :y="menuY"
      :items="[
        { label: 'Delete', action: handleDelete }
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
