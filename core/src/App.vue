<template>
  <router-view />
  <!-- Глобальные оверлеи UX kit: тосты и promise-confirm доступны на любом экране -->
  <AppToast />
  <AppConfirm />
</template>

<script setup>
import { RouterView } from 'vue-router'
import AppToast from './components/ui/kit/AppToast.vue'
import AppConfirm from './components/ui/kit/AppConfirm.vue'
</script>
