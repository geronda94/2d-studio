<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  mode: { type: String, default: 'auto' }, // auto | single | group
  characters: { type: Array, default: () => [] },
  max_stat: { type: Number, default: 10 },
  show_values: { type: Boolean, default: true },
  source_note: { type: String, default: '' },
})

const { itemVars, itemPrimaryVars, motion } = useVariant(computed(() => props.variant), 'CharacterStats')
const relativeTime = inject('relativeTime', ref(0))

const list = computed(() => props.characters || [])
const isGroup = computed(() => props.mode === 'group' || (props.mode === 'auto' && list.value.length > 1))

const accent = (c, i) => getHexColor(c?.color || `var(--item-accent-${(i % 4) + 1})`)
const statColor = (s, c, i) => getHexColor(s?.color || c?.color || `var(--item-accent-${(i % 4) + 1})`)

// Инициалы вместо битой/отсутствующей фотографии — панель не выглядит пустой.
const initials = (name) => String(name || '')
  .split(/\s+/)
  .filter(Boolean)
  .slice(0, 2)
  .map((w) => w.replace(/[^\p{L}\p{N}]/gu, '').charAt(0))
  .join('')
  .toUpperCase()

const reveal = (item, i, y = 14) => {
  const start = item?.start_time ?? i * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - start) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * y).toFixed(2)}px)` }
}

const grow = (charIdx, statIdx, value, max) => {
  const start = (charIdx * motion.value.stagger_ms) + (statIdx + 1) * 140
  const p = Math.max(0, Math.min(1, (relativeTime.value - start) / motion.value.count_ms))
  const e = 1 - Math.pow(1 - p, 3)
  const pct = Math.max(0, Math.min(1, (Number(value) || 0) / (Number(max) || props.max_stat || 1)))
  return {
    transform: `scaleX(${(pct * e).toFixed(4)})`,
    transformOrigin: 'left center',
  }
}

const cardStyle = {
  background: 'var(--item-bg)',
  backdropFilter: 'var(--item-backdrop)',
  borderRadius: 'var(--item-radius)',
  boxShadow: 'var(--item-shadow)',
  padding: 'var(--item-padding)',
  borderWidth: 'var(--item-border-width)',
  borderStyle: 'var(--item-border-style)',
  borderColor: 'var(--item-border)',
}
const panelStyle = {
  background: 'var(--item-primary-bg)',
  backdropFilter: 'var(--item-primary-backdrop)',
  borderRadius: 'var(--item-primary-radius)',
  boxShadow: 'var(--item-primary-shadow)',
  padding: 'var(--item-primary-padding)',
  borderWidth: 'var(--item-primary-border-width)',
  borderStyle: 'var(--item-primary-border-style)',
  borderColor: 'var(--item-primary-border)',
}
const imgFail = ref({})
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars, ...itemPrimaryVars }">
    <div v-if="!list.length" class="flex-1 min-h-0 flex items-center justify-center text-text-muted text-sm">Нет данных</div>

    <!-- SINGLE -->
    <div
      v-else-if="!isGroup"
      class="flex-1 min-h-0 grid grid-cols-1 md:grid-cols-[minmax(0,34%)_minmax(0,1fr)] gap-4 md:gap-6 items-stretch"
    >
      <div
        class="relative min-h-0 overflow-hidden flex items-end justify-center"
        :style="[panelStyle, reveal(list[0], 0)]"
      >
        <div
          class="absolute inset-0 pointer-events-none"
          :style="{ background: `radial-gradient(60% 55% at 50% 42%, ${getColorAlpha(accent(list[0], 0), 0.22)} 0%, transparent 70%)` }"
        ></div>
        <img
          v-if="list[0].image && !imgFail[list[0].id || 0]"
          :src="list[0].image"
          :alt="list[0].name"
          class="absolute inset-0 w-full h-full object-contain object-bottom"
          @error="imgFail[list[0].id || 0] = true"
        />
        <div v-else class="absolute inset-0 flex items-center justify-center">
          <div
            class="w-28 h-28 md:w-32 md:h-32 rounded-full flex items-center justify-center font-heading font-bold text-3xl md:text-4xl"
            :style="{
              background: getColorAlpha(accent(list[0], 0), 0.14),
              border: '2px solid ' + getColorAlpha(accent(list[0], 0), 0.45),
              color: accent(list[0], 0),
            }"
          >{{ initials(list[0].name) || '?' }}</div>
        </div>
        <div class="relative z-10 w-full px-4 pb-4 pt-10 text-center">
          <h3 class="font-heading font-bold text-2xl md:text-3xl text-text-primary leading-tight">{{ list[0].name }}</h3>
          <p v-if="list[0].subtitle" class="mt-1 text-sm" :style="{ color: accent(list[0], 0) }">{{ list[0].subtitle }}</p>
        </div>
      </div>

      <div class="min-h-0 overflow-y-auto flex flex-col justify-center gap-3 md:gap-4 pr-1">
        <div
          v-for="(s, si) in (list[0].stats || [])"
          :key="s.label + si"
          class="flex flex-col gap-1.5"
          :style="reveal(s, si + 1)"
        >
          <div class="flex items-center gap-2">
            <Icon v-if="s.icon" :icon="s.icon" class="w-4 h-4 shrink-0" :style="{ color: statColor(s, list[0], si) }" />
            <span class="text-sm md:text-base text-text-secondary">{{ s.label }}</span>
            <span v-if="show_values" class="ml-auto font-mono font-bold text-text-primary">
              {{ s.value }}<span class="text-text-muted text-xs">/{{ s.max || max_stat }}</span>
            </span>
          </div>
          <div class="h-2.5 rounded-full overflow-hidden" :style="{ background: getColorAlpha('var(--color-primary)', 0.12) }">
            <div
              class="h-full rounded-full origin-left"
              :style="[{ background: statColor(s, list[0], si) }, grow(0, si, s.value, s.max)]"
            ></div>
          </div>
        </div>

        <div v-if="(list[0].traits || []).length" class="flex flex-wrap gap-2 pt-1">
          <span
            v-for="(t, ti) in list[0].traits"
            :key="t.label + ti"
            class="flex items-center gap-1.5 px-2.5 py-1 text-[11px] font-mono"
            :style="[{ background: getColorAlpha(accent(list[0], 0), 0.12), color: accent(list[0], 0), borderRadius: '999px', border: '1px solid ' + getColorAlpha(accent(list[0], 0), 0.35) }, reveal(t, ti + 2)]"
          >
            <Icon v-if="t.icon" :icon="t.icon" class="w-3 h-3" />{{ t.label }}
          </span>
        </div>
      </div>
    </div>

    <!-- GROUP -->
    <div
      v-else
      class="flex-1 min-h-0 overflow-y-auto grid gap-3 pr-1"
      :class="mobile ? 'grid-cols-1' : 'grid-cols-2 lg:grid-cols-3'"
    >
      <div
        v-for="(c, i) in list"
        :key="c.id || i"
        class="flex flex-col overflow-hidden"
        :style="[cardStyle, reveal(c, i)]"
      >
        <div class="relative h-32 md:h-36 shrink-0 flex items-end justify-center overflow-hidden">
          <div
            class="absolute inset-0 pointer-events-none"
            :style="{ background: `radial-gradient(60% 60% at 50% 55%, ${getColorAlpha(accent(c, i), 0.2)} 0%, transparent 72%)` }"
          ></div>
          <img
            v-if="c.image && !imgFail[c.id || i]"
            :src="c.image"
            :alt="c.name"
            class="absolute inset-0 w-full h-full object-contain object-bottom"
            @error="imgFail[c.id || i] = true"
          />
          <div v-else class="absolute inset-0 flex items-center justify-center">
            <div
              class="w-16 h-16 rounded-full flex items-center justify-center font-heading font-bold text-xl"
              :style="{
                background: getColorAlpha(accent(c, i), 0.14),
                border: '2px solid ' + getColorAlpha(accent(c, i), 0.45),
                color: accent(c, i),
              }"
            >{{ initials(c.name) || '?' }}</div>
          </div>
        </div>

        <div class="flex flex-col gap-2 p-3">
          <div class="min-w-0">
            <p class="font-heading font-bold text-base text-text-primary leading-tight truncate">{{ c.name }}</p>
            <p v-if="c.subtitle" class="text-[11px] truncate" :style="{ color: accent(c, i) }">{{ c.subtitle }}</p>
          </div>

          <div v-for="(s, si) in (c.stats || [])" :key="s.label + si" class="flex flex-col gap-1">
            <div class="flex items-center gap-1.5">
              <Icon v-if="s.icon" :icon="s.icon" class="w-3.5 h-3.5 shrink-0" :style="{ color: statColor(s, c, i) }" />
              <span class="text-[11px] text-text-secondary truncate">{{ s.label }}</span>
              <span v-if="show_values" class="ml-auto font-mono text-[11px] font-bold text-text-primary">{{ s.value }}</span>
            </div>
            <div class="h-1.5 rounded-full overflow-hidden" :style="{ background: getColorAlpha('var(--color-primary)', 0.12) }">
              <div
                class="h-full rounded-full origin-left"
                :style="[{ background: statColor(s, c, i) }, grow(i, si, s.value, s.max)]"
              ></div>
            </div>
          </div>

          <div v-if="(c.traits || []).length" class="flex flex-wrap gap-1.5 pt-0.5">
            <span
              v-for="(t, ti) in c.traits"
              :key="t.label + ti"
              class="flex items-center gap-1 px-1.5 py-0.5 text-[10px] font-mono"
              :style="{ background: getColorAlpha(accent(c, i), 0.1), color: accent(c, i), borderRadius: '6px' }"
            >
              <Icon v-if="t.icon" :icon="t.icon" class="w-2.5 h-2.5" />{{ t.label }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <p v-if="source_note" class="shrink-0 mt-2 text-center text-[11px] font-mono text-text-muted opacity-70">{{ source_note }}</p>
  </div>
</template>
