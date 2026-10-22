<script setup>
// ─────────────────────────────────────────────────────────────────────────────
// Lampada — подвесная лампадка (кандило). ВНУТРЕННИЙ building block:
// используется внутри PortraitLampSlide, в componentsRegistry НЕ входит
// (как RoiCalculator / Ecosystem / BeforeAfter).
//
// Анимации строго детерминированы от `relativeTime` (AGENTS §11): качание
// маятника, мерцание пламени и пульс свечения — математика от времени слайда.
// Никаких rAF / CSS infinite / <animate> — иначе рендер mp4 «угорает».
//
// Цвета — только токены палитры (getHexColor/getColorAlpha), чтобы лампадка
// адаптировалась под тему (золото/лес/…).
// ─────────────────────────────────────────────────────────────────────────────
import { computed, inject, ref } from 'vue'
import { getColorAlpha, getHexColor } from '../../utils/colors'

const props = defineProps({
  color: { type: String, default: 'color-primary' },       // металл (цепочки/чаша/основание)
  flame_color: { type: String, default: 'color-warning' }, // пламя и свечение
  scale: { type: Number, default: 1 },
})

const relativeTime = inject('relativeTime', ref(0))
const t = computed(() => relativeTime.value || 0)

// Качание маятника: период 7.2с, амплитуда 6°.
const swing = computed(() => Math.sin((t.value / 7200) * Math.PI * 2) * 6)
// Мерцание пламени (две частоты) и пульс свечения — 0..1.
const flick = computed(() => (Math.sin((t.value / 2000) * Math.PI * 2) + 1) / 2)
const flick2 = computed(() => (Math.sin((t.value / 1300) * Math.PI * 2 + 1.1) + 1) / 2)

const metal = computed(() => getHexColor(props.color))
const glass = computed(() => getHexColor('color-secondary'))
const flame = computed(() => getHexColor(props.flame_color))
const glow = computed(() => getColorAlpha(props.flame_color, 0.3))
const glowSoft = computed(() => getColorAlpha(props.flame_color, 0.03))
</script>

<template>
  <div class="lampada" :style="{ transform: `scale(${scale})` }">
    <div class="lampada-swing" :style="{ transform: `rotate(${swing}deg)` }">
      <!-- Тёплое свечение вокруг огонька (качается вместе с лампадкой) -->
      <div
        class="lampada-aura"
        :style="{
          background: `radial-gradient(50% 60% at 50% 100%, ${glow} 0%, ${glowSoft} 75%)`,
          opacity: (0.5 + flick * 0.12).toFixed(3),
          transform: `translateX(-50%) scale(${(0.96 + flick * 0.08).toFixed(3)})`,
        }"
      ></div>

      <svg width="80" height="150" viewBox="0 0 80 150" fill="none" style="overflow: visible">
        <defs>
          <linearGradient id="lampMetal" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" :stop-color="metal" stop-opacity="0.95" />
            <stop offset="45%" stop-color="#FFFFFF" stop-opacity="1" />
            <stop offset="55%" :stop-color="metal" stop-opacity="1" />
            <stop offset="100%" :stop-color="metal" stop-opacity="0.95" />
          </linearGradient>
          <linearGradient id="lampGlass" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" :stop-color="glass" stop-opacity="0.9" />
            <stop offset="100%" :stop-color="glass" stop-opacity="0.6" />
          </linearGradient>
          <radialGradient id="lampFlameGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" :stop-color="flame" stop-opacity="0.9" />
            <stop offset="100%" :stop-color="flame" stop-opacity="0" />
          </radialGradient>
          <filter id="lampFlameBlur">
            <feGaussianBlur stdDeviation="1.2" />
          </filter>
        </defs>

        <!-- Цепочки -->
        <g>
          <g transform="rotate(18, 17, 85)">
            <ellipse v-for="i in 6" :key="'l' + i" cx="17" :cy="12 + (i - 1) * 12" rx="1.2" ry="3.2"
              stroke="url(#lampMetal)" stroke-width="1" fill="none" />
          </g>
          <g transform="rotate(-18, 63, 85)">
            <ellipse v-for="i in 6" :key="'r' + i" cx="63" :cy="12 + (i - 1) * 12" rx="1.2" ry="3.2"
              stroke="url(#lampMetal)" stroke-width="1" fill="none" />
          </g>
          <g>
            <ellipse v-for="i in 6" :key="'c' + i" cx="40" :cy="12 + (i - 1) * 12" rx="1.2" ry="3.2"
              stroke="url(#lampMetal)" stroke-width="1" fill="none" />
          </g>
        </g>

        <!-- Стеклянная гранёная чаша -->
        <g>
          <path d="M 22 85 L 58 85 L 54 105 C 54 112, 26 112, 26 105 Z"
            fill="url(#lampGlass)" :stroke="glass" stroke-width="0.5" />
          <path d="M 33 85 L 35 108" stroke="#FFFFFF" stroke-opacity="0.2" stroke-width="0.5" />
          <path d="M 47 85 L 45 108" stroke="#FFFFFF" stroke-opacity="0.2" stroke-width="0.5" />
          <path d="M 40 85 L 40 110" stroke="#FFFFFF" stroke-opacity="0.15" stroke-width="0.5" />
          <path d="M 25 88 Q 40 84 55 88" stroke="#FFFFFF" stroke-opacity="0.2" fill="none" />
        </g>

        <!-- Мерцающее свечение вокруг огонька -->
        <circle class="lampada-glow" cx="40" cy="80" r="18" fill="url(#lampFlameGlow)"
          :style="{ opacity: (0.4 + flick * 0.22).toFixed(3), transform: `scale(${(0.9 + flick * 0.25).toFixed(3)})` }" />

        <!-- Пламя -->
        <g :style="{ transform: `translateX(${((flick2 - 0.5) * 0.6).toFixed(2)}px)` }">
          <path class="lampada-flame-outer" d="M 40 68 Q 44 78 40 84 Q 36 78 40 68 Z"
            :fill="flame" filter="url(#lampFlameBlur)"
            :style="{ opacity: (0.8 + flick * 0.2).toFixed(3) }" />
          <path class="lampada-flame-inner" d="M 40 73 Q 42 78 40 82 Q 38 78 40 73 Z"
            fill="#FFFBE6" fill-opacity="0.95"
            :style="{ opacity: (0.7 + flick2 * 0.3).toFixed(3) }" />
        </g>

        <!-- Крепления и основание -->
        <circle cx="17" cy="85" r="1.5" :fill="metal" />
        <circle cx="63" cy="85" r="1.5" :fill="metal" />
        <circle cx="40" cy="85" r="1.5" :fill="metal" />
        <path d="M 17 85 C 17 90, 63 90, 63 85 L 61 88 L 19 88 Z" fill="url(#lampMetal)" />
        <path d="M 35 110 L 45 110 L 42 115 L 38 115 Z" :fill="metal" />
      </svg>
    </div>
  </div>
</template>

<style scoped>
.lampada {
  width: 80px;
  height: 150px;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  position: relative;
  transform-origin: 50% 0%;
}
.lampada-swing {
  position: relative;
  width: 80px;
  height: 150px;
  transform-origin: 50% 0%;
  will-change: transform;
}
.lampada-aura {
  position: absolute;
  left: 50%;
  bottom: 20px;
  width: 280px;
  height: 320px;
  transform: translateX(-50%);
  border-radius: 50%;
  filter: blur(50px);
  pointer-events: none;
  will-change: transform, opacity;
}
.lampada-glow {
  transform-origin: 40px 80px;
  will-change: transform, opacity;
}
.lampada-flame-outer {
  transform-origin: 40px 84px;
}
.lampada-flame-inner {
  transform-origin: 40px 82px;
}
</style>
