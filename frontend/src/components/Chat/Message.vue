<script setup lang="ts">
import type { Message } from '../types';

const props = defineProps<Message>();
</script>

<template>
    <div class="message" :class="{mine: isMine}">
        <div class="author">{{ author }}</div>
        <div class="text">{{ text }}</div>
        <div class="time">
            {{ datetime }}
            <span v-if="wasUpdated" class="edited">(upd)</span>
        </div>
    </div>
</template>

<style>
.message {
  background: #f1f1f1;
  padding: 8px 12px;
  border-radius: 8px;
  margin: 5px 0;
  max-width: 60vw;       
  width: fit-content;    
  word-wrap: break-word; 
}


.mine {
  background: #d1f5d3;
  margin-left: auto;
}

.author {
  font-size: 0.8rem;
  font-weight: bold;
  margin-bottom: 2px;
}

.text {
  font-size: 1rem;
}

.time {
  font-size: 0.7rem;
  text-align: right;
  color: gray;
  display: inline-flex;     
  gap: 4px;                 
  align-items: center;
  white-space: nowrap;      
}


.edited {
  font-size: 0.7rem;
  font-style: italic;
  margin-left: 4px;
}
</style>
