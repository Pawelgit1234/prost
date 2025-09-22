<script setup lang="ts">
async function continueWithGoogle() {
    window.location.href = import.meta.env.VITE_API_ENDPOINT + '/auth/google/uri'
}
</script>

<template>
    <button
    type="button"
    class="btn google-btn w-100 mb-3 d-flex align-items-center justify-content-center"
    @click="continueWithGoogle"
    >
    <img src="https://www.svgrepo.com/show/380993/google-logo-search-new.svg" alt="G" />
    <span>Continue with Google</span>
    </button>
</template>
