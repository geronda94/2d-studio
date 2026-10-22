<script setup>
import { ref, watch } from "vue";
import {
  fetchPresets, fetchVariants, fetchPresentationTokens,
  fetchProjectsSummary, copyPaletteToPresentation, clearPresentationPalette,
} from "../../services/api";

const props = defineProps({
  show: Boolean,
  presentationId: {
    type: [Number, String],
    default: null,
  },
  presetInfo: {
    type: Object,
    default: null,
  },
  presentationVariant: {
    type: String,
    default: "",
  },
  chessboard: {
    type: Boolean,
    default: false,
  },
  visibility: {
    type: String,
    default: "public",
  },
});

const emit = defineEmits(["close", "update-style", "update-variant", "update-chessboard", "update-visibility", "palette-changed", "open-ai"]);

const paletteSource = ref(null);
const paletteCount = ref(0);
const palettes = ref([]);
const palSel = ref("");
const palBusy = ref(false);
const palMsg = ref("");

const loadPaletteInfo = async () => {
  if (!props.presentationId) return;
  try {
    const data = await fetchPresentationTokens(Number(props.presentationId));
    paletteSource.value = data.palette_source || null;
    paletteCount.value = data.presentation_tokens || 0;
  } catch {
    paletteSource.value = null;
    paletteCount.value = 0;
  }
};

const applyPalette = async () => {
  if (!props.presentationId || !palSel.value || palBusy.value) return;
  if (!confirm(`Взять палитру «${palSel.value}» только для этой презентации? Проект не изменится.`)) return;
  palBusy.value = true;
  palMsg.value = "";
  try {
    const res = await copyPaletteToPresentation(Number(props.presentationId), palSel.value);
    palMsg.value = `Взято токенов: ${res.copied}`;
    await loadPaletteInfo();
    emit("palette-changed");
  } catch (e) {
    palMsg.value = e.message;
  } finally {
    palBusy.value = false;
  }
};

const resetPalette = async () => {
  if (!props.presentationId || palBusy.value) return;
  if (!confirm("Сбросить палитру презентации? Она снова начнёт наследовать палитру проекта.")) return;
  palBusy.value = true;
  try {
    await clearPresentationPalette(Number(props.presentationId));
    palMsg.value = "Палитра сброшена к проекту";
    await loadPaletteInfo();
    emit("palette-changed");
  } catch (e) {
    palMsg.value = e.message;
  } finally {
    palBusy.value = false;
  }
};

const presetsList = ref([]);
const variantsList = ref([]);
const selPreset = ref("");
const selLock = ref(false);
const selVariant = ref("");
const selChess = ref(false);
const tab = ref("style"); // style | theme | view | ai

const syncAll = () => {
  selPreset.value = props.presetInfo?.style_preset || "";
  selLock.value = !!props.presetInfo?.style_lock;
  selVariant.value = props.presentationVariant || "";
  selChess.value = !!props.chessboard;
};

watch(
  () => props.show,
  (open) => {
    if (!open) return;
    syncAll();
    loadPaletteInfo();
    fetchPresets()
      .then((list) => {
        presetsList.value = list || [];
      })
      .catch(() => {
        presetsList.value = [];
      });
    fetchVariants()
      .then((list) => {
        variantsList.value = list || [];
      })
      .catch(() => {
        variantsList.value = [];
      });
    fetchProjectsSummary()
      .then((all) => {
        palettes.value = (all || []).filter((p) => p.is_template || p.slug === 'it2b' || p.slug === 'history' || p.slug === 'derevnya');
      })
      .catch(() => {
        palettes.value = [];
      });
  },
  { immediate: true },
);
watch(() => props.presetInfo, syncAll, { deep: true });
</script>

<template>
  <div
    v-if="show"
    class="fixed inset-0 z-[300] flex items-center justify-center p-4"
  >
    <div
      class="absolute inset-0 bg-black/70 backdrop-blur-sm"
      @click="emit('close')"
    ></div>
    <div
      class="relative bg-bg-surface border border-text-muted rounded-2xl w-full max-w-md shadow-2xl overflow-hidden"
    >
      <div class="flex items-center justify-between p-5 border-b border-text-muted">
        <h2 class="text-lg font-bold text-text-primary">⚙️ Настройки презентации</h2>
        <button
          @click="emit('close')"
          class="text-text-secondary hover:text-text-primary transition-colors text-xl leading-none px-1"
        >
          ✕
        </button>
      </div>

      <!-- Табы -->
      <div class="flex gap-1 px-4 pt-3 border-b border-text-muted">
        <button
          v-for="t in [{id:'style',n:'Стиль'},{id:'theme',n:'Тема'},{id:'view',n:'Вид'},{id:'ai',n:'AI'}]"
          :key="t.id"
          @click="tab = t.id"
          class="px-3 py-2 text-sm font-bold border-b-2 -mb-px transition-colors"
          :class="tab === t.id ? 'border-color-secondary text-color-secondary' : 'border-transparent text-text-secondary hover:text-text-primary'"
        >
          {{ t.n }}
        </button>
      </div>

      <div class="p-5 flex flex-col gap-5">
        <!-- Вектор стилей -->
        <section v-if="tab === 'style'">
          <h3 class="text-xs font-bold uppercase tracking-wider text-text-secondary mb-2">
            Вектор стилей
          </h3>
          <div class="flex gap-2">
            <select
              v-model="selPreset"
              class="flex-1 min-w-0 bg-bg-base border border-text-muted rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none"
            >
              <option value="">Без пресета</option>
              <option v-for="p in presetsList" :key="p.slug" :value="p.slug">
                {{ p.title }}
              </option>
            </select>
            <label
              class="flex items-center gap-1.5 text-sm text-text-secondary whitespace-nowrap"
              title="Лок: save вне вектора — 422"
            >
              <input type="checkbox" v-model="selLock" class="accent-blue-600" />
              🔒
            </label>
            <button
              @click="emit('update-style', { style_preset: selPreset || null, style_lock: !!selLock })"
              class="px-3 py-2 bg-color-primary hover:opacity-90 text-white text-sm font-bold rounded-lg transition-all"
            >
              OK
            </button>
          </div>
          <p v-if="presetInfo?.preset" class="text-xs text-text-muted mt-1.5">
            Сейчас: {{ presetInfo.preset.title }}
          </p>
        </section>

        <!-- Вариант по умолчанию -->
        <section v-if="tab === 'style'">
          <h3 class="text-xs font-bold uppercase tracking-wider text-text-secondary mb-2">
            Вариант слайдов по умолчанию
          </h3>
          <div class="flex gap-2">
            <select
              v-model="selVariant"
              class="flex-1 min-w-0 bg-bg-base border border-text-muted rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none"
            >
              <option value="">— tech —</option>
              <option v-for="v in variantsList" :key="v.slug" :value="v.slug">
                {{ v.name || v.slug }}
              </option>
            </select>
            <button
              @click="emit('update-variant', selVariant || null)"
              class="px-3 py-2 bg-color-primary hover:opacity-90 text-white text-sm font-bold rounded-lg transition-all"
            >
              OK
            </button>
          </div>
        </section>

        <!-- Палитра презентации -->
        <section v-if="tab === 'theme'">
          <h3 class="text-xs font-bold uppercase tracking-wider text-text-secondary mb-2">
            Палитра презентации
          </h3>
          <p class="text-xs text-text-muted mb-2">
            <template v-if="paletteSource">своя: {{ paletteSource }} ({{ paletteCount }} токенов)</template>
            <template v-else>наследует палитру проекта</template>
          </p>
          <div class="flex gap-2">
            <select
              v-model="palSel"
              class="flex-1 min-w-0 bg-bg-base border border-text-muted rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none"
            >
              <option value="" disabled>Взять палитру…</option>
              <option v-for="p in palettes" :key="p.slug" :value="p.slug">{{ p.title }}</option>
            </select>
            <button
              @click="applyPalette"
              :disabled="!palSel || palBusy"
              class="px-3 py-2 bg-color-primary hover:opacity-90 disabled:opacity-50 text-white text-sm font-bold rounded-lg transition-all"
            >
              {{ palBusy ? '…' : 'Взять' }}
            </button>
            <button
              v-if="paletteSource"
              @click="resetPalette"
              :disabled="palBusy"
              class="px-3 py-2 bg-bg-base hover:bg-bg-surface-hover text-text-secondary border border-text-muted text-sm rounded-lg disabled:opacity-50"
              title="Сбросить к палитре проекта"
            >
              ↩
            </button>
          </div>
          <p v-if="palMsg" class="text-xs text-text-muted mt-1.5">{{ palMsg }}</p>
        </section>

        <!-- AI-ассистент -->
        <section v-if="tab === 'ai'">
          <button
            @click="emit('open-ai')"
            class="w-full py-2.5 rounded-lg text-sm font-bold text-white transition-all"
            style="background: linear-gradient(90deg, var(--color-secondary), var(--color-accent))"
          >
            ✨ AI-ассистент: сгенерировать слайды
          </button>
          <p class="text-xs text-text-muted mt-1.5">Предложит правки по брифу проекта; применяется только после твоего подтверждения.</p>
        </section>

        <!-- Шахматка -->
        <section v-if="tab === 'view'" class="flex items-center justify-between">
          <div>
            <h3 class="text-xs font-bold uppercase tracking-wider text-text-secondary">
              Шахматка фонов
            </h3>
            <p class="text-xs text-text-muted mt-0.5">slide-bg-1..4 циклично (по дефолту выкл)</p>
          </div>
          <button
            @click="emit('update-chessboard', !chessboard)"
            class="w-11 h-6 rounded-full transition-colors relative shrink-0"
            :class="chessboard ? 'bg-color-success' : 'bg-text-muted/40'"
            :title="chessboard ? 'Выключить' : 'Включить'"
          >
            <span
              class="absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-all"
              :class="chessboard ? 'left-[22px]' : 'left-0.5'"
            ></span>
          </button>
        </section>

        <!-- Доступ (AUTH_PLAN Ф4) -->
        <section v-if="tab === 'view'" class="flex items-center justify-between">
          <div>
            <h3 class="text-xs font-bold uppercase tracking-wider text-text-secondary">
              Приватная презентация
            </h3>
            <p class="text-xs text-text-muted mt-0.5">
              Вкл — по ссылке видят только владелец и участники. Выкл — просмотр открыт всем.
            </p>
          </div>
          <button
            @click="emit('update-visibility', visibility === 'private' ? 'public' : 'private')"
            class="w-11 h-6 rounded-full transition-colors relative shrink-0"
            :class="visibility === 'private' ? 'bg-color-success' : 'bg-text-muted/40'"
            :title="visibility === 'private' ? 'Сделать публичной' : 'Сделать приватной'"
          >
            <span
              class="absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-all"
              :class="visibility === 'private' ? 'left-[22px]' : 'left-0.5'"
            ></span>
          </button>
        </section>
      </div>
    </div>
  </div>
</template>
