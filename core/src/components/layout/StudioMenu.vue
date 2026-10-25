<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const open = ref(false)
const close = () => { open.value = false }
onMounted(() => window.addEventListener('click', close))
onUnmounted(() => window.removeEventListener('click', close))

const items = [
  { href: '/character-studio.html', label: 'Character Studio', hint: 'Внешность, скелет и липсинк' },
  { href: '/object-studio.html', label: 'Object Studio', hint: 'Создание и редактирование объектов' },
  { href: '/rig-studio.html', label: 'Rig Studio', hint: 'Скелет, морфы, манифест персонажа' },
  { href: '/clip-editor.html', label: 'Clip Editor', hint: 'Ключи анимации и *.sclip.json' },
]
</script>

<template>
  <div class="relative" @click.stop>
    <button
      @click="open = !open"
      class="inline-flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-xl text-sm font-medium text-gray-700 hover:bg-gray-100 transition-colors shadow-sm"
    >
      Студии
    </button>
    <div
      v-if="open"
      class="absolute right-0 mt-2 w-72 bg-white border border-gray-200 rounded-xl shadow-xl py-1 z-50"
    >
      <a
        v-for="item in items"
        :key="item.href"
        :href="item.href"
        target="_blank"
        rel="noopener"
        @click="close"
        class="block px-3 py-2.5 hover:bg-gray-50"
      >
        <div class="text-sm font-semibold text-gray-900">{{ item.label }}</div>
        <div class="text-[11px] text-gray-400">{{ item.hint }}</div>
      </a>
      <div class="px-3 py-2 text-[10px] text-gray-400 border-t border-gray-100">
        Откроется в новой вкладке
      </div>
    </div>
  </div>
</template>
