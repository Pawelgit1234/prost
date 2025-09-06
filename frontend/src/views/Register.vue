<script setup lang="ts">
import { ref } from 'vue';
import pinia from '../store';
import { useUserStore } from '../store/user';

const firstName = ref("");
const lastName = ref("");
const description = ref("");
const username = ref("");
const email = ref("");
const password = ref("");
const confirmPassword = ref("");
const error = ref("");

async function submit() {
  error.value = "";

  if (
    !firstName.value.trim() ||
    !lastName.value.trim() ||
    !username.value.trim() ||
    !email.value.trim() ||
    !password.value.trim() ||
    !confirmPassword.value.trim()
  ) {
    error.value = "Please fill in all required fields.";
    return;
  }

  if (password.value !== confirmPassword.value) {
    error.value = "Passwords do not match.";
    return;
  }

  console.log("Register: ", {
    first_name: firstName.value,
    last_name: lastName.value,
    description: description.value || null,
    username: username.value,
    email: email.value,
    password: password.value,
  });

  const userStore = useUserStore(pinia);
  await userStore.register(
    firstName.value, lastName.value, description.value || null,
    username.value, email.value, password.value
  );
}

async function registerWithGoogle() {
  console.log("Register with Google clicked");
}
</script>

<template>
  <div class="container d-flex justify-content-center align-items-center vh-100">
    <div class="card p-4 shadow-sm" style="width: 100%; max-width: 450px;">
      <h3 class="card-title text-center mb-3">Register</h3>

      <!-- Google Register -->
      <button
        type="button"
        class="btn google-btn w-100 mb-3 d-flex align-items-center justify-content-center"
        @click="registerWithGoogle"
      >
        <img src="https://www.svgrepo.com/show/380993/google-logo-search-new.svg" alt="G" />
        <span>Register with Google</span>
      </button>

      <div class="text-center mb-3">or</div>

      <!-- Regular Register -->
      <form @submit.prevent="submit">
        <div class="mb-3">
          <label for="firstName" class="form-label">First Name</label>
          <input v-model="firstName" type="text" class="form-control" id="firstName" required />
        </div>
        <div class="mb-3">
          <label for="lastName" class="form-label">Last Name</label>
          <input v-model="lastName" type="text" class="form-control" id="lastName" required />
        </div>
        <div class="mb-3">
          <label for="description" class="form-label">Description (optional)</label>
          <textarea v-model="description" class="form-control" id="description" rows="2" maxlength="100"></textarea>
        </div>
        <div class="mb-3">
          <label for="username" class="form-label">Username</label>
          <input v-model="username" type="text" class="form-control" id="username" required />
        </div>
        <div class="mb-3">
          <label for="email" class="form-label">Email</label>
          <input v-model="email" type="email" class="form-control" id="email" required />
        </div>
        <div class="mb-3">
          <label for="password" class="form-label">Password</label>
          <input v-model="password" type="password" class="form-control" id="password" required />
        </div>
        <div class="mb-3">
          <label for="confirmPassword" class="form-label">Confirm Password</label>
          <input v-model="confirmPassword" type="password" class="form-control" id="confirmPassword" required />
        </div>

        <div v-if="error" class="alert alert-danger py-1 px-2 mb-3" role="alert">
          {{ error }}
        </div>

        <button type="submit" class="btn btn-primary w-100">Register</button>
      </form>

      <p class="text-center mt-3">
        Already have an account? <a href="/login">Login</a>
      </p>
    </div>
  </div>
</template>

<style>
.google-btn {
  border: 1px solid #dee2e6 !important;
  background-color: white;
  color: #444;
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
