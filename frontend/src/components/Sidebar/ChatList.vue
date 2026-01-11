<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useDebounceFn } from '@vueuse/core'
import { useChatStore, type ChatI } from '../../store/chats';
import type FolderSelectorModal from '../common/FolderSelectorModal.vue';
import { useFolderStore, type FolderI } from '../../store/folders';
import { useMessageStore } from '../../store/messages';
import type { UserI } from '../../store/auth';
import { useUserStore } from '../../store/users';
import { useSearchStore, type SearchItem } from '../../store/search';
import JoinRequestModal from '../common/JoinRequestModal.vue';

const props = defineProps<{
  chats: ChatI[];
  selectedChatUuid: string;
}>();

const emit = defineEmits<{
  (e: 'update:selectedChat', chatUuid: string): void;
  (e: 'choosedMessage', messageUuid: string): void;
}>();

function selectChat(chatUuid: string) {
  emit('update:selectedChat', chatUuid);
}

function chooseMessage(messageUuid: string) {
  emit('choosedMessage', messageUuid);
}

const folderStore = useFolderStore()
const chatStore = useChatStore()
const messageStore = useMessageStore()
const userStore = useUserStore()

// ---- ADD CHAT TO FOLDER ----
const isAddToFolderModalOpen = ref(false)
const chatToAddInFolder = ref<ChatI | null>(null)

async function handleAddChatToFolderSubmit(folders: FolderI[]) {
  if (!chatToAddInFolder.value) return
  await folderStore.addChatToFolders(chatToAddInFolder.value, folders)
  isAddToFolderModalOpen.value = false
}

// ---- ADD USER TO GROUP ----
const isAddUserToGroupModalOpen = ref(false)
const groupToAddUser = ref<ChatI | null>(null)

async function handleAddUserToGroupSubmit(users: UserI[]) {
  if (!groupToAddUser.value) return
  const userUuids = users.map(user => user.uuid)
  await chatStore.addUserToGroup(groupToAddUser.value, userUuids)
  isAddUserToGroupModalOpen.value = false
}

// ---- JOIN REQUEST ----
const isJoinRequestModalOpen = ref(false)
const searchItem = ref<SearchItem | null>(null) // group or user

function handleJoinRequest(item: SearchItem) {
  searchItem.value = item
  isJoinRequestModalOpen.value = true
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

function handleAddChatToFolder() {
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
  if (!selectedChat.value) return
  await chatStore.deleteChat(selectedChat.value.uuid)
  folderStore.deleteChat(selectedChat.value.uuid)
  messageStore.deleteChatMessages(selectedChat.value.uuid)
}

const menuItems = computed(() => {
  if (!selectedChat.value) return []

  const items = [
    { label: 'Add to Folder', action: handleAddChatToFolder },
    { label: 'Pin', action: handlePinChat },
    { label: 'Delete Chat', action: handleDeleteChat },
  ]

  // Only for groups
  if (selectedChat.value.chat_type === 'group') {
    items.push(
      { label: 'Add User to Group', action: handleAddUserToGroup },
      { label: 'Quit', action: handleQuitGroup },
    )
  }

  return items
})

async function handleQuitGroup() {
  if (!selectedChat.value) return
  await chatStore.quitChat(selectedChat.value.uuid)
  folderStore.deleteChat(selectedChat.value.uuid)
  messageStore.deleteChatMessages(selectedChat.value.uuid)
}

async function handleAddUserToGroup() {
  if (!selectedChat.value) return;
  groupToAddUser.value = selectedChat.value
  isAddUserToGroupModalOpen.value = true
}

// Global Search
const searchStore = useSearchStore()
const isSearchActive = ref(false)
const search = ref('')
const autocompleteWord = ref('')

const runSearch = useDebounceFn(async (value: string) => {
  if (value.length < 2) return

  searchStore.reset(value)
  await searchStore.fetchSearchPage()
  await searchStore.loadHistory()
}, 400)

function autocomplete(value: string) {
  autocompleteWord.value = ''

  if (!value) return

  const match = searchStore.queries.find(q =>
    q.startsWith(value) && q !== value
  )

  if (match) {
    autocompleteWord.value = match
  }
}

function applyAutocomplete() {
  if (!autocompleteWord.value) return
  search.value = autocompleteWord.value
  autocompleteWord.value = ''
}

watch(search, (value) => {
  isSearchActive.value = value.length > 0
  autocomplete(value)
  runSearch(value)
})

async function createChatOrJoinRequest(item: SearchItem) {
  if (item.is_open_for_messages) {
    if (item.chat_type === 'group') { // add to group
      await chatStore.joinGroup(item.uuid)
    } else if (item.type === 'users') { // create chat

    }
  } else {

  }

  
  // ...
  // selectChat()
  isJoinRequestModalOpen.value = false
}

async function selectChatOrChooseMessage(item: SearchItem) {
  if (item.type === "chats") selectChat(item.uuid)
  else if (item.type === "messages") chooseMessage(item.uuid)
}
</script>

<template>
  <div class="p-2">
    <div class="search-wrapper">
      <!-- AUTOCOMPLETE BACKGROUND -->
      <input
        type="text"
        class="form-control form-control-sm search-ghost"
        :value="autocompleteWord"
        disabled
      />

      <!-- REAL INPUT -->
      <input
        v-model="search"
        type="text"
        class="form-control form-control-sm search-input"
        placeholder="Search"
        @keydown.tab.prevent="applyAutocomplete"
      />
    </div>
  </div>

  <div class="search-results" v-if="isSearchActive">
    <h5>Global results</h5>
    <div
      v-for="item in searchStore.globalItems"
      :key="item.uuid"
      class="chat-item"
      @click.left.prevent="handleJoinRequest(item)"
    >
      <div class="chat-name">{{ item.name || item.username }}</div>
    </div>

    <h5>Local results</h5>
    <div
      v-for="item in searchStore.localItems"
      :key="item.uuid"
      :class="['chat-item', { selected: item.uuid === selectedChatUuid }]"
      @click.left.prevent="selectChatOrChooseMessage(item)"
    >
      <div class="chat-name">{{ userStore.getUserFromOneOfTheMembers(item.members || [])?.username }}</div>
    </div>
  </div>

  <div class="chat-list" v-if="!isSearchActive">
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
    :items="menuItems"
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

  <!-- Add User to Group -->
  <SearchSelectModal
    :visible="isAddUserToGroupModalOpen"
    title="Choose Users"
    placeholder="Search for users"
    :items="userStore.users"
    :filterFn="(item: UserI) => groupToAddUser?.user_uuids.includes(item.uuid)"
    :getKey="(item: UserI) => item.uuid"
    :getLabel="(item: UserI) => item.username"
    @submit="handleAddUserToGroupSubmit"
    @close="isAddUserToGroupModalOpen = false"
  />

  <!-- Join Request -->
  <JoinRequestModal
    v-if="searchItem"
    :visible="isJoinRequestModalOpen"
    :item="searchItem"
    @submit="createChatOrJoinRequest"
    @close="isJoinRequestModalOpen = false"
  />
</template>

<style scoped>
.chat-list, .search-results {
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

.search-wrapper {
  position: relative;
}

.search-ghost {
  position: absolute;
  inset: 0;
  z-index: 1;
  color: #aaa;
  background-color: white;
  pointer-events: none;
}

.search-input {
  position: relative;
  z-index: 2;
  background: transparent !important;

  caret-color: black;
}
</style>
