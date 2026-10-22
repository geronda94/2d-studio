<script setup>
import { computed } from 'vue'
import { Icon } from '@iconify/vue'
import HeatmapMatrix from './HeatmapMatrix.vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  worldviews: { type: Array, default: () => [] },
  criteria: { type: Array, default: () => [] },
  map: { type: Array, default: () => [] },
  source_note: { type: String, default: '' },
})

const { itemVars } = useVariant(computed(() => props.variant), 'WorldviewMatrix')

const accent = getHexColor('var(--color-secondary)')
const hasData = computed(() => (props.worldviews || []).length > 0 && (props.criteria || []).length > 0)
</script>

<template>
  <div
    class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col gap-2"
    :style="{ ...itemVars }"
  >
    <div class="shrink-0 flex items-center gap-2">
      <Icon icon="lucide:compass" class="w-4 h-4" :style="{ color: accent }" />
      <span class="text-[10px] font-mono uppercase tracking-widest text-text-secondary">Мировоззрения и критерии</span>
    </div>

    <div
      v-if="!hasData"
      class="flex-1 flex items-center justify-center text-text-muted text-sm"
    >Нет данных</div>

    <div v-else class="flex-1 min-h-0 overflow-hidden flex items-center justify-center">
      <HeatmapMatrix
        class="w-full"
        :mobile="mobile"
        :variant="variant"
        :rows="worldviews"
        :cols="criteria"
        :cells="map"
        scale="bloom"
        row_label="Мировоззрение"
        col_label="Критерий"
      />
    </div>

    <p
      v-if="source_note"
      class="shrink-0 text-[11px] font-mono text-text-secondary opacity-90"
    >{{ source_note }}</p>
  </div>
</template>
