<script setup lang="ts">
import { defineProps, defineEmits } from 'vue';
import type { Folder } from '../types';

const props = defineProps<{
    folders: Folder[];
    selectFolderUuid: string
}>();

const emit = defineEmits<{
  (e: 'update:selectedFolder', folderId: string): void;
}>();

function selectFolder(folderUuid: string) {
    emit('update:selectedFolder', folderUuid);
}

</script>

<template>
    <div class="folder-list">
        <div
            v-for="folder in folders"
            :key="folder.uuid"
            :class="['folder-item', {selected: folder.uuid === selectFolderUuid}]"
            @click="selectFolder(folder.uuid)"
        >
            {{ folder.name }}
        </div>
    </div>
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
</style>
