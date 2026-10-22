<script setup>
// Скелетоны/лоадеры загрузки (UX). Самодостаточны: не зависят от токенов темы
// (на экране плеера тема ещё не применена — иначе лоадер выглядел как голый текст).
defineProps({
  variant: { type: String, default: 'cards' }, // cards | folders | player
  count: { type: Number, default: 8 },
})
</script>

<template>
  <!-- Плеер: полноэкранный анимированный лоадер -->
  <div v-if="variant === 'player'" class="sk-player">
    <div class="sk-orb">
      <span class="sk-orb__ring"></span>
      <span class="sk-orb__ring sk-orb__ring--2"></span>
      <span class="sk-orb__core"></span>
    </div>
    <div class="sk-progress"><i></i></div>
  </div>

  <!-- Сетка карточек (папки/презентации/проекты) с бегущим бликом -->
  <div
    v-else
    class="grid gap-5"
    :class="variant === 'folders'
      ? 'grid-cols-1 md:grid-cols-3'
      : 'grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4'"
  >
    <div
      v-for="i in count"
      :key="i"
      class="sk-card"
      :style="{ animationDelay: `${(i % 6) * 90}ms` }"
    >
      <div class="sk-card__icon"></div>
      <div class="sk-card__lines">
        <div class="sk-card__line" style="width: 75%"></div>
        <div class="sk-card__line sk-card__line--short" style="width: 45%"></div>
      </div>
      <span class="sk-shine"></span>
    </div>
  </div>
</template>

<style scoped>
/* ============ Плеер ============ */
/* Оформление — в стиле интерфейса (светлая админка), НЕ темы презентации:
   лоадер виден до применения темы, поэтому палитра фиксированная. */
.sk-player {
  position: fixed;
  inset: 0;
  z-index: 60;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 28px;
  background: #f5f5f7;
}

.sk-orb {
  position: relative;
  width: 92px;
  height: 92px;
  display: grid;
  place-items: center;
}
.sk-orb__ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: conic-gradient(from 0deg, transparent 0deg, transparent 210deg, #6366f1 300deg, #2563eb 360deg);
  -webkit-mask: radial-gradient(farthest-side, transparent calc(100% - 4px), #000 calc(100% - 3px));
  mask: radial-gradient(farthest-side, transparent calc(100% - 4px), #000 calc(100% - 3px));
  animation: sk-spin 1.15s linear infinite;
}
.sk-orb__ring--2 {
  inset: 12px;
  background: conic-gradient(from 180deg, transparent 0deg, transparent 240deg, #93c5fd 330deg, transparent 360deg);
  -webkit-mask: radial-gradient(farthest-side, transparent calc(100% - 3px), #000 calc(100% - 2px));
  mask: radial-gradient(farthest-side, transparent calc(100% - 3px), #000 calc(100% - 2px));
  animation-duration: 0.85s;
  animation-direction: reverse;
  opacity: 0.9;
}
.sk-orb__core {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #2563eb);
  box-shadow: 0 6px 16px rgba(37, 99, 235, 0.28);
  animation: sk-breathe 1.6s ease-in-out infinite;
}

.sk-progress {
  width: 190px;
  height: 3px;
  border-radius: 999px;
  background: #e5e7eb;
  overflow: hidden;
}
.sk-progress i {
  display: block;
  width: 42%;
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #6366f1, #2563eb);
  animation: sk-slide 1.35s cubic-bezier(0.65, 0, 0.35, 1) infinite;
}

@keyframes sk-spin { to { transform: rotate(360deg); } }
@keyframes sk-breathe {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(0.82); opacity: 0.75; }
}
@keyframes sk-slide {
  0% { transform: translateX(-110%); }
  100% { transform: translateX(340%); }
}

/* ============ Карточки ============ */
.sk-card {
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 12rem;
  padding: 1.25rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.75rem;
  background: #fff;
  animation: sk-fade 1.1s ease-in-out infinite;
}
.sk-card__icon {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0.5rem;
  background: #eef1f5;
}
.sk-card__lines { display: flex; flex-direction: column; gap: 0.5rem; }
.sk-card__line {
  height: 0.75rem;
  border-radius: 999px;
  background: #eef1f5;
}
.sk-card__line--short { height: 0.6rem; }

.sk-shine {
  position: absolute;
  inset: 0;
  transform: translateX(-100%);
  background: linear-gradient(100deg, transparent 20%, rgba(255, 255, 255, 0.75) 50%, transparent 80%);
  animation: sk-shine 1.5s ease-in-out infinite;
}

@keyframes sk-fade {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.72; }
}
@keyframes sk-shine {
  0% { transform: translateX(-100%); }
  60%, 100% { transform: translateX(100%); }
}
</style>
