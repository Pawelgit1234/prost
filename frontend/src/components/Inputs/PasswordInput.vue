<script setup lang="ts">
import { ref, defineProps, defineEmits } from 'vue';

const props = defineProps<{
  id?: string;
  label?: string;
  modelValue: string;
  placeholder?: string;
  required?: boolean;
}>();

const emit = defineEmits(['update:modelValue']);
const showPassword = ref(false);

const togglePassword = () => {
  showPassword.value = !showPassword.value;
};
</script>

<template>
  <div class="mb-3">
    <label v-if="label" :for="id" class="form-label">{{ label }}</label>
    <div class="input-group">
      <input
        :id="id"
        :type="showPassword ? 'text' : 'password'"
        class="form-control"
        :placeholder="placeholder"
        :required="required"
        :value="modelValue"
        @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)"
      />
      <button
        class="btn btn-outline-secondary"
        type="button"
        @click="togglePassword"
      >
        <i v-if="showPassword" class="bi bi-eye-slash"></i>
        <i v-else class="bi bi-eye"></i>
      </button>
    </div>
  </div>
</template>
