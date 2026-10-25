<script setup>
// Единая админ-рамка (UX_REDESIGN Ф1): хлебные крошки + заголовок + слот действий.
// Светлая, контент-центричная. Креатив/плеер эту рамку не использует.
import AuthMenu from './AuthMenu.vue'
import StudioMenu from './StudioMenu.vue'

defineProps({
  crumbs: { type: Array, default: () => [] }, // [{ label, to? }]
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  maxWidth: { type: String, default: 'max-w-6xl' },
})
</script>

<template>
  <div class="relative min-h-dvh bg-[#f5f5f7] text-gray-900 p-4 md:p-12 font-sans pt-[max(1rem,env(safe-area-inset-top))] md:pt-[max(3rem,env(safe-area-inset-top))] pb-[max(1rem,env(safe-area-inset-bottom))]">
    <div class="absolute top-[max(1rem,env(safe-area-inset-top))] right-4 md:top-[max(3rem,env(safe-area-inset-top))] md:right-12 z-40 flex items-center gap-2">
      <StudioMenu />
      <AuthMenu />
    </div>
    <div :class="maxWidth" class="mx-auto">
      <!-- Хлебные крошки -->
      <nav v-if="crumbs.length" class="flex items-center gap-1.5 text-sm text-gray-400 mb-4 flex-wrap">
        <template v-for="(c, i) in crumbs" :key="i">
          <router-link v-if="c.to" :to="c.to" class="hover:text-gray-700 transition-colors">{{ c.label }}</router-link>
          <span v-else class="text-gray-600 font-medium">{{ c.label }}</span>
          <span v-if="i < crumbs.length - 1" class="opacity-50">/</span>
        </template>
      </nav>

      <!-- Шапка -->
      <header class="flex justify-between items-end gap-4 flex-wrap mb-8">
        <div class="min-w-0">
          <h1 class="text-2xl md:text-4xl font-bold tracking-tight break-words">
            <slot name="title">{{ title }}</slot>
          </h1>
          <p v-if="subtitle || $slots.subtitle" class="text-gray-500 font-light mt-1 text-sm md:text-base">
            <slot name="subtitle">{{ subtitle }}</slot>
          </p>
        </div>
        <div v-if="$slots.actions" class="flex gap-3 items-center flex-wrap justify-end">
          <slot name="actions" />
        </div>
      </header>

      <slot />
    </div>
  </div>
</template>
