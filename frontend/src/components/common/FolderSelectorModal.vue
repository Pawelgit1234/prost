<script setup lang="ts">
import { ref, watch } from 'vue';
import type { FolderI } from '../../store/folders';

const props = defineProps<{
  visible: boolean
  title: string
  folders: FolderI[]
  filterFn: (folder: FolderI) => boolean // true -> in matched
}>()

const emit = defineEmits<{
  (e: 'submit', value: FolderI[]): void
  (e: 'close'): void
}>()

const matched = ref(props.folders.filter(f => props.filterFn(f)))
watch(() => props.visible, (v) => {
  if (v) {
    matched.value = props.folders.filter(f => props.filterFn(f));
  }
});

function toggleFolder(folder: FolderI) {
  if (matched.value.includes(folder)) {
    matched.value = matched.value.filter(i => i !== folder)
  } else {
    matched.value = [...matched.value, folder]
  }
}

</script>

<template>
    <div v-if="visible" class="modal-overlay" @click.self="emit('close')">
            <div class="modal-content">
                <h3>{{ title }}</h3>

                <div class="scroll-box">
                    <div v-for="f in props.folders" :key="f.uuid" @click="toggleFolder(f)" class="scroll-box-item">
                        <span v-if="matched.includes(f)" class="check">✔</span>
                        {{ f.name }}
                    </div>
                </div>

                <div class="modal-actions">
                    <button class="btn btn-primary" @click="emit('submit', matched)">Submit</button>
                    <button class="btn btn-danger" @click="emit('close')">Cancel</button>
                </div>
            </div>
        </div>
</template>
