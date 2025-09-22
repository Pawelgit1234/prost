<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useAuthStore } from "../store/auth";
import { BAlert, BSpinner, BButton } from 'bootstrap-vue-next'

const userStore = useAuthStore();

const loading = ref(true);
const success = ref(false);
const error = ref<string | null>(null);

const authenticateViaBackend = async () => {
  try {
    const queryParams = new URLSearchParams(window.location.search);
    const code = queryParams.get("code");
    const state = queryParams.get("state");

    if (code && state) {
      await userStore.loginWithGoogle(code, state);
      success.value = true;
    } else {
      error.value = "Authorization code was not found.";
    }
  } catch (e: any) {
    error.value = "Failed to sign in with Google.";
  } finally {
    loading.value = false;
  }
};

onMounted(async () => {
  await authenticateViaBackend();
})

</script>

<template>
  <div class="d-flex justify-content-center align-items-center vh-100">
    <div class="w-50 text-center">
      <!-- Loading -->
      <div v-if="loading" class="p-5">
        <BSpinner label="Loading..." variant="primary" class="mb-3" />
        <h4>Signing in with Google...</h4>
      </div>

      <!-- Error -->
      <BAlert v-else-if="error" show variant="danger" class="p-4">
        <h5 class="alert-heading">Authentication Error</h5>
        <p>{{ error }}</p>
      </BAlert>

      <!-- Success -->
      <BAlert v-else-if="success" show variant="success" class="p-4">
        <h4 class="alert-heading">Welcome {{ userStore.currentUser?.username }}!</h4>
        <p>You have successfully signed in with Google 🎉</p>
        <BButton variant="primary" href="/messenger" class="mt-3">Go to Messenger</BButton>
      </BAlert>
    </div>
  </div>
</template>

<style>
</style>
