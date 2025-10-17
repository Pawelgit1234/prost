<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRouter } from 'vue-router';
import type { AxiosError } from 'axios';
import { useForm, useField } from "vee-validate";
import * as yup from "yup";

import pinia from '../store';
import { useAuthStore } from '../store/auth';

const schema = yup.object({
  firstName: yup.string().required("First name is required"),
  lastName: yup.string().required("Last name is required"),
  username: yup.string().required("Username is required"),
  email: yup.string().email("Invalid email").required("Email is required"),
  password: yup
    .string()
    .required("Password is required")
    .min(8, "Minimum 8 characters")
    .matches(/[A-Z]/, "At least one uppercase letter")
    .matches(/[a-z]/, "At least one lowercase letter")
    .matches(/\d/, "At least one number")
    .matches(/[!@#$%^&*(),.?\":{}|<>]/, "At least one special character"),
  confirmPassword: yup
    .string()
    .required("Confirm Password is required")
    .oneOf([yup.ref("password")], "Passwords do not match"),
});

// vee-validate form
const { handleSubmit, errors } = useForm({
  validationSchema: schema,
});

const { value: firstName } = useField<string>("firstName");
const { value: lastName } = useField<string>("lastName");
const { value: description } = useField<string | null>("description");
const { value: username } = useField<string>("username");
const { value: email } = useField<string>("email");
const { value: password } = useField<string>("password");
const { value: confirmPassword } = useField<string>("confirmPassword");

const errorMessage = ref("");
const userStore = useAuthStore(pinia);
const router = useRouter();

// computed checks for password rules
const passwordChecks = computed(() => {
  const val = password.value || "";
  return {
    minLength: val.length >= 8,
    upper: /[A-Z]/.test(val),
    lower: /[a-z]/.test(val),
    number: /\d/.test(val),
    special: /[!@#$%^&*(),.?":{}|<>]/.test(val),
  };
});

const onSubmit = handleSubmit(async (values) => {
  try {
    await userStore.register(
      values.firstName,
      values.lastName,
      values.description || null,
      values.username,
      values.email,
      values.password
    );
    router.push("/messenger");
  } catch (err) {
    const axiosError = err as AxiosError;
    if (axiosError.response?.status === 409) {
      const data = axiosError.response.data as { detail: string };
      errorMessage.value = data.detail;
    } else if (axiosError.response?.status === 422) {
      errorMessage.value = "Validation failed";
    } else {
      errorMessage.value = "Something went wrong. Please try again later.";
    }
  }
});
</script>

<template>
  <div class="register container d-flex justify-content-center align-items-center vh-100">
    <div class="card p-4 shadow-sm" style="width: 100%; max-width: 450px;">
      <h3 class="card-title text-center mb-3">Register</h3>

      <ContinueWithGoogle/>

      <div class="text-center mb-3">or</div>

      <!-- Regular Register -->
      <form @submit.prevent="onSubmit">
        <div class="mb-3">
          <label for="firstName" class="form-label">First Name</label>
          <input v-model="firstName" type="text" class="form-control" id="firstName" />
          <div v-if="errors.firstName" class="text-danger small">{{ errors.firstName }}</div>
        </div>
        <div class="mb-3">
          <label for="lastName" class="form-label">Last Name</label>
          <input v-model="lastName" type="text" class="form-control" id="lastName" />
          <div v-if="errors.lastName" class="text-danger small">{{ errors.lastName }}</div>
        </div>
        <div class="mb-3">
          <label for="description" class="form-label">Description (optional)</label>
          <textarea v-model="description" class="form-control" id="description" rows="2" maxlength="100"></textarea>
        </div>
        <div class="mb-3">
          <label for="username" class="form-label">Username</label>
          <input v-model="username" type="text" class="form-control" id="username" />
          <div v-if="errors.username" class="text-danger small">{{ errors.username }}</div>
        </div>
        <div class="mb-3">
          <label for="email" class="form-label">Email</label>
          <input v-model="email" type="email" class="form-control" id="email" />
          <div v-if="errors.email" class="text-danger small">{{ errors.email }}</div>
        </div>
        <PasswordInput
          v-model="password"
          id="password"
          label="Password"
          placeholder="Enter your password"
        />
        <PasswordInput
          v-model="confirmPassword"
          id="confirmPassword"
          label="Confirm Password"
          placeholder="Re-enter your password"
        />
        <div v-if="errors.confirmPassword" class="text-danger small">
          {{ errors.confirmPassword }}
        </div>

        <!-- Checklist -->
        <ul class="list-unstyled small mt-2">
          <li :class="{ 'text-success': passwordChecks.minLength }">Minimum 8 characters</li>
          <li :class="{ 'text-success': passwordChecks.upper }">One uppercase letter</li>
          <li :class="{ 'text-success': passwordChecks.lower }">One lowercase letter</li>
          <li :class="{ 'text-success': passwordChecks.number }">One number</li>
          <li :class="{ 'text-success': passwordChecks.special }">One special character</li>
        </ul>

        <div v-if="errorMessage" class="alert alert-danger py-1 px-2 mb-3" role="alert">
          {{ errorMessage }}
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
.register {
  margin-top: 5%;
}
</style>