<script setup lang="ts">
import { ref } from 'vue';
import { useUserStore } from '../store/user';
import pinia from '../store';

const emailOrUsername = ref("");
const password = ref("");
const error = ref("");

async function submit() {
  error.value = ""; 

  if (!emailOrUsername.value.trim() || !password.value.trim()) {
    error.value = "Please fill in all fields.";
    return;
  }

  console.log("Login: ", emailOrUsername.value, password.value);

  const userStore = useUserStore(pinia);
  await userStore.login(emailOrUsername.value, password.value);
}

async function loginWithGoogle() {
  console.log("Login with Google clicked");
}

</script>

<template>
  <div class="container d-flex justify-content-center align-items-center vh-100">
    <div class="card p-4 shadow-sm" style="width: 100%; max-width: 400px;">
      <h3 class="card-title text-center mb-3">Login</h3>

      <!-- Google Login -->
      <button
        type="button"
        class="btn google-btn w-100 mb-3 d-flex align-items-center justify-content-center"
        @click="loginWithGoogle"
      >
        <img src="https://www.svgrepo.com/show/380993/google-logo-search-new.svg" alt="G" />
        <span>Login with Google</span>
      </button>

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
        <div class="mb-3">
          <label for="password" class="form-label">Password</label>
          <input
            v-model="password"
            type="password"
            class="form-control"
            id="password"
            placeholder="Enter your password"
            required
          />
        </div>

        <div v-if="error" class="alert alert-danger py-1 px-2 mb-3" role="alert">
          {{ error }}
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
