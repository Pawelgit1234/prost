<script setup lang="ts">
import { onMounted } from 'vue';
import { useUserStore } from "../store/user";

const userStore = useUserStore();

const authenticateViaBackend = async () => {
  const queryParams = new URLSearchParams(window.location.search);
  const code = queryParams.get("code");
  const state = queryParams.get("state");

  if (code && state) {
    await userStore.loginWithGoogle(code, state);
  }
};

onMounted(async () => {
  await authenticateViaBackend();
})

</script>

<template>
</template>

<style>
</style>