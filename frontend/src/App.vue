<script setup lang="ts">
    import Message from './components/Message.vue';
</script>

<template>
    <Message
  text="Привет!"
  author="Андрей"
  datetime="12:34"
  :isMine="true"
  :wasUpdated="true"
/>
</template>

<style>
</style>
