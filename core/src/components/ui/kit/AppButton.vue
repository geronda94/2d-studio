<script setup>
// Единая кнопка (UX kit). theme: 'dark' (креатив, по умолчанию) | 'light' (админка).
const props = defineProps({
  variant: { type: String, default: 'primary' }, // primary|secondary|ghost|danger|success
  size: { type: String, default: 'md' }, // sm|md|lg
  theme: { type: String, default: 'dark' },
  disabled: Boolean,
  loading: Boolean,
  block: Boolean,
  type: { type: String, default: 'button' },
})

const sizes = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-4 py-2 text-sm',
  lg: 'px-5 py-2.5 text-base',
}

const variants = {
  primary: 'bg-color-primary hover:opacity-90 text-white',
  secondary: 'border bg-transparent',
  ghost: 'bg-transparent',
  danger: 'bg-red-500 hover:bg-red-600 text-white',
  success: 'bg-color-success hover:opacity-90 text-white',
}

const themeCls = {
  dark: {
    secondary: 'bg-bg-surface border-text-muted text-text-primary hover:bg-bg-surface-hover',
    ghost: 'text-text-secondary hover:text-text-primary hover:bg-bg-surface',
  },
  light: {
    secondary: 'bg-white border-gray-200 text-gray-700 hover:bg-gray-100',
    ghost: 'text-gray-500 hover:text-gray-900 hover:bg-gray-100',
  },
}

const cls = () => {
  const base = 'inline-flex items-center justify-center gap-2 rounded-lg font-bold transition-colors disabled:opacity-50 disabled:cursor-not-allowed'
  const v = variants[props.variant] || variants.primary
  const themed = (props.variant === 'secondary' || props.variant === 'ghost')
    ? (themeCls[props.theme] || themeCls.dark)[props.variant]
    : ''
  return [base, sizes[props.size] || sizes.md, v, themed, props.block ? 'w-full' : '']
}
</script>

<template>
  <button :type="type" :disabled="disabled || loading" :class="cls()">
    <span v-if="loading" class="animate-spin w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full"></span>
    <slot />
  </button>
</template>
