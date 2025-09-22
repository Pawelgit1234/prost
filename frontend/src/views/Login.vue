<script setup lang="ts">
import { ref } from 'vue';
import { useAuthStore } from '../store/auth';
import pinia from '../store';
import { useRouter } from 'vue-router';
import type { AxiosError } from 'axios';

const emailOrUsername = ref("");
const password = ref("");
const errorMessage = ref("");

const userStore = useAuthStore(pinia);
const router = useRouter();

async function submit() {
  errorMessage.value = ""; 

  if (!emailOrUsername.value.trim() || !password.value.trim()) {
    errorMessage.value = "Please fill in all fields.";
    return;
  }

  console.log("Login: ", emailOrUsername.value, password.value);

  try {
    await userStore.login(emailOrUsername.value, password.value);
    router.push("/messenger")
  } catch (err) {
    const axiosError = err as AxiosError;
    if (axiosError.response?.status === 404) {
      errorMessage.value = "User was not found";
    } else if (axiosError.response?.status === 401) {
      errorMessage.value = "Incorrect username or password";
    } else {
      errorMessage.value = "Something went wrong. Please try again later.";
    }
  }
}

</script>

<template>
  <div class="container d-flex justify-content-center align-items-center vh-100">
    <div class="card p-4 shadow-sm" style="width: 100%; max-width: 400px;">
      <h3 class="card-title text-center mb-3">Login</h3>

      <ContinueWithGoogle/>

      <div class="text-center mb-3">or</div>

      <!-- Regular Login -->
      <form @submit.prevent="submit">
        <div class="mb-3">
          <label for="emailOrUsername" class="form-label">Email or Username</label>
          <input
            v-model="emailOrUsername"
            type="text"
            class="form-control"
            id="emailOrUsername"
            placeholder="Enter your email or username"
            required
          />
        </div>

        <PasswordInput
          v-model="password"
          id="password"
          label="Password"
          placeholder="Enter your password"
          required
        />

        <div v-if="errorMessage" class="alert alert-danger py-1 px-2 mb-3" role="alert">
          {{ errorMessage }}
        </div>

        <button type="submit" class="btn btn-primary w-100">Login</button>
      </form>

      <p class="text-center mt-3">
        Don't have an account? <a href="/register">Register</a>
      </p>
    </div>
  </div>
</template>

<style>
.google-btn {
  border: 1px solid #dee2e6 !important;
  background-color: rgb(0, 0, 0);
  gap: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  font-weight: 500;
  transition: background 0.2s, box-shadow 0.2s;
}

.google-btn img {
  width: 20px;
  height: 20px;
}

.google-btn:hover {
  background-color: #f5f5f5;
  box-shadow: 0 0 5px rgba(0,0,0,0.2);
}
</style>
