<script setup>
import { ref, onMounted, onUnmounted, watch } from "vue";
import { useScreenRecorder } from "../../composables/useScreenRecorder.js";
import { apiFetch } from "../../services/api.js";
import { useMobile } from "../../composables/useMobile.ts";

const { startRecording } = useScreenRecorder();
const { forceMobile } = useMobile();

const props = defineProps({
  isOpen: Boolean,
  presentationId: [Number, String],
  presentationTitle: {
    type: String,
    default: '',
  },
  slidesData: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(["close"]);

const renderJobs = ref([]);
const loading = ref(false);
const submitting = ref(false);
const startedMsg = ref(""); // статус после запуска Playwright-рендера (модалку не закрываем)
const previewJob = ref(null); // задача, открытая в плеере-предпросмотре (без скачивания)
let pollingInterval = null;

// Form state (по умолчанию — серверный Playwright-рендер)
// Качество и FPS зафиксированы на максимуме (селекторы убраны из UI):
// сервер — ultrafast crf 18 + 60 fps, live — 60 Мбит/с VP9 + 60 fps.
const renderType = ref("realtime");
const format = ref("desktop");
const fps = ref(60);
const quality = ref("premium");

const API_BASE = "/api";

const fetchJobs = async () => {
  if (!props.isOpen || !props.presentationId) return;
  try {
    const res = await fetch(
      `${API_BASE}/renders/presentation/${props.presentationId}`,
    );
    if (res.ok) {
      renderJobs.value = await res.json();
    }
  } catch (err) {
    console.error("Failed to fetch render jobs:", err);
  }
};

const getPresentationEndTime = () => {
  const slides = Array.isArray(props.slidesData) ? props.slidesData : [];
  if (!slides.length) return null;

  const endMarker = slides.find(
    (slide) => slide?.component === "EndMarkerSlide",
  );
  if (endMarker) {
    const value = Number(endMarker.start_time ?? endMarker.startTime ?? 0);
    if (Number.isFinite(value) && value > 0) return value;
  }

  return slides.reduce((max, slide) => {
    const start = Number(slide?.start_time ?? slide?.startTime ?? 0);
    return Math.max(max, start + 5000);
  }, 0);
};

// Формат кнопками (как клавиша M): сразу перестраивает вид через forceMobile
const setFormat = (mode) => {
  format.value = mode === "portrait" ? "portrait" : "desktop";
  forceMobile.value = mode === "portrait";
};

// При открытии модалки подхватить текущий вид
watch(
  () => props.isOpen,
  (open) => {
    if (open) {
      format.value = forceMobile.value ? "portrait" : "desktop";
      fetchJobs();
    }
  },
);

const startRender = async () => {
  submitting.value = true;
  startedMsg.value = "";
  try {
    if (renderType.value === "realtime") {
      const payload = {
        presentation_id: Number(props.presentationId),
        settings: {
          format: format.value,
          fps: Number(fps.value) || 30,
          quality: quality.value || "standard",
        },
      };

      // apiFetch: cookie-сессия + CSRF-заголовок (иначе 403 csrf_invalid).
      const response = await apiFetch(`${API_BASE}/renders/realtime`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error("Realtime render job creation failed");
      }

      // Playwright-рендер идёт на сервере — модалку НЕ закрываем, чтобы пользователь
      // наблюдал прогресс (опрос каждую секунду + список задач справа).
      await fetchJobs();
      startedMsg.value = "Рендер запущен — прогресс отображается справа.";
      return;
    }

    // Live capture — только из этого пути
    emit("close");

    if (!navigator.mediaDevices?.getDisplayMedia) {
      alert(
        "Браузер не поддерживает live capture. Используйте Chrome/Chromium.",
      );
      return;
    }

    window.dispatchEvent(new CustomEvent("presentation:close-all-modals"));

    const dimensions =
      format.value === "portrait"
        ? { width: 1280, height: 1920 }
        : { width: 1920, height: 1280 };
    const dpr = window.devicePixelRatio || 1;
    const captureWidth = Math.round(dimensions.width * dpr);
    const captureHeight = Math.round(dimensions.height * dpr);
    const targetFps = Number(fps.value) || 60;
    const endTimeMs = getPresentationEndTime();

    await startRecording(null, {
      width: captureWidth,
      height: captureHeight,
      fps: targetFps,
      quality: quality.value || "premium",
      autoPlay: true,
      endTimeMs,
      title: props.presentationTitle || "",
      format: format.value === "portrait" ? "portrait" : "landscape",
    });

      } catch (err) {
    console.error("Failed to start render:", err);
    alert(
      renderType.value === "realtime"
        ? "Не удалось запустить Playwright рендер."
        : "Не удалось запустить capture. Разрешите доступ к экрану.",
    );
  } finally {
    submitting.value = false;
  }
};

const deleteJob = async (jobId) => {
  try {
    const res = await apiFetch(`${API_BASE}/renders/${jobId}`, {
      method: "DELETE",
    });
    if (res.ok) {
      await fetchJobs();
    }
  } catch (err) {
    console.error("Failed to delete job:", err);
  }
};

const reRenderJob = (job) => {
  if (job.settings) {
    renderType.value = job.settings.engine === "realtime" ? "realtime" : "live";
    const f = job.settings.format || "desktop";
    setFormat(f === "portrait" || f === "mobile" ? "portrait" : "desktop");
  }
  // FPS и качество всегда максимальные (60 / premium), из джобы не тянем.
  fps.value = 60;
  quality.value = "premium";
  startRender();
};

const formatETA = (seconds) => {
  if (seconds === undefined || seconds === null || isNaN(seconds))
    return "Вычисляем...";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  if (m > 0) return `~ ${m} мин ${s} сек`;
  return `~ ${s} сек`;
};

onMounted(() => {
  pollingInterval = setInterval(() => {
    if (props.isOpen) fetchJobs();
  }, 1000);
});

onUnmounted(() => {
  if (pollingInterval) clearInterval(pollingInterval);
});

const formatDate = (ds) => {
  if (!ds) return "";
  const d = new Date(ds + "Z");
  return d.toLocaleString();
};
</script>

<template>
  <div
    v-if="isOpen"
    class="fixed inset-0 bg-black/80 backdrop-blur-sm z-[9999] flex items-center justify-center p-2 md:p-6"
  >
    <div
      class="bg-bg-base border border-text-muted rounded-2xl w-full max-w-4xl max-h-[90dvh] flex flex-col shadow-2xl relative overflow-hidden font-sans text-text-primary"
    >
      <div
        class="flex items-center justify-between p-6 border-b border-text-muted bg-bg-surface"
      >
        <h2 class="text-2xl font-bold font-heading flex items-center gap-2">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="22"
            height="22"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="text-brand-green"
          >
            <polygon points="5 3 19 12 5 21 5 3"></polygon>
          </svg>
          Экспорт видео
        </h2>
        <button
          @click="$emit('close')"
          class="text-text-secondary hover:text-text-primary transition-colors"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>

      <div class="flex-1 overflow-y-auto p-3 md:p-6 flex flex-col lg:flex-row gap-5 md:gap-8">
        <!-- Left: Form -->
        <div class="w-full lg:w-1/3 space-y-6">
          <div>
            <h3 class="text-lg font-bold mb-4 border-b border-text-muted pb-2">
              Новый экспорт
            </h3>

            <div class="space-y-4">
              <div>
                <label class="block text-sm text-text-secondary mb-1"
                  >Способ рендера</label
                >
                <div class="grid grid-cols-1 gap-2">
                  <button
                    type="button"
                    @click="renderType = 'realtime'"
                    class="rounded-lg px-3 py-2.5 font-bold border transition-colors flex items-center justify-center gap-2 whitespace-nowrap"
                    :class="
                      renderType === 'realtime'
                        ? 'bg-brand-blue border-brand-blue text-white'
                        : 'bg-bg-base border-text-muted text-text-secondary hover:text-text-primary'
                    "
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="shrink-0"><rect x="2" y="2" width="20" height="20" rx="5"/><path d="M10 17l5-3-5-3z"/></svg>
                    Playwright + ffmpeg
                  </button>
                  <button
                    type="button"
                    @click="renderType = 'live'"
                    class="rounded-lg px-3 py-2.5 font-bold border transition-colors flex items-center justify-center gap-2 whitespace-nowrap"
                    :class="
                      renderType === 'live'
                        ? 'bg-brand-green border-brand-green text-white'
                        : 'bg-bg-base border-text-muted text-text-secondary hover:text-text-primary'
                    "
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="shrink-0"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8"/><path d="M12 17v4"/></svg>
                    Live capture
                  </button>
                </div>
                <p class="text-xs text-text-muted mt-1.5">
                  {{ renderType === 'live' ? 'Запись из браузера (WebM). Нужно разрешить доступ к вкладке.' : 'Headless Chromium в фоне (MP4). Не требует доступа к экрану.' }}
                </p>
              </div>

              <div>
                <label class="block text-sm text-text-secondary mb-1"
                  >Формат capture</label
                >
                <div class="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    @click="setFormat('desktop')"
                    class="rounded-lg px-3 py-2 font-bold border transition-colors flex items-center justify-center gap-2"
                    :class="
                      format !== 'portrait'
                        ? 'bg-brand-blue border-brand-blue text-white'
                        : 'bg-bg-base border-text-muted text-text-secondary hover:text-text-primary'
                    "
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    >
                      <rect x="2" y="5" width="20" height="13" rx="2"></rect>
                      <path d="M8 21h8"></path>
                    </svg>
                    Широкий
                  </button>
                  <button
                    type="button"
                    @click="setFormat('portrait')"
                    class="rounded-lg px-3 py-2 font-bold border transition-colors flex items-center justify-center gap-2"
                    :class="
                      format === 'portrait'
                        ? 'bg-brand-blue border-brand-blue text-white'
                        : 'bg-bg-base border-text-muted text-text-secondary hover:text-text-primary'
                    "
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    >
                      <rect x="7" y="2" width="10" height="20" rx="2"></rect>
                    </svg>
                    Шортс
                  </button>
                </div>
              </div>

              <p class="text-xs text-text-muted">
                Максимум по умолчанию: 60 FPS, студийное качество.
              </p>

              <p v-if="startedMsg" class="mt-3 text-sm text-brand-green flex items-center gap-2">
                <span class="w-2 h-2 rounded-full bg-brand-green animate-pulse"></span>
                {{ startedMsg }}
              </p>

              <button
                @click="startRender"
                :disabled="submitting"
                class="w-full mt-4 bg-brand-green hover:bg-brand-green/90 disabled:opacity-50 text-white rounded-lg py-3 font-bold transition-colors flex items-center justify-center gap-2"
              >
                <svg
                  v-if="!submitting"
                  xmlns="http://www.w3.org/2000/svg"
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <polygon points="5 3 19 12 5 21 5 3"></polygon>
                </svg>
                <svg
                  v-else
                  class="animate-spin"
                  xmlns="http://www.w3.org/2000/svg"
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path d="M21 12a9 9 0 1 1-6.219-8.56"></path>
                </svg>
                {{
                  submitting
                    ? "Запуск..."
                    : renderType === 'realtime'
                      ? "Запустить рендер"
                      : "Начать запись"
                }}
              </button>
            </div>
          </div>
        </div>

        <!-- Right: Queue and History -->
        <div class="w-full lg:w-2/3">
          <h3 class="text-lg font-bold mb-4 border-b border-text-muted pb-2">
            Очередь и готовые файлы
          </h3>

          <div
            v-if="renderJobs.length === 0"
            class="text-center py-12 text-text-muted"
          >
            Нет истории рендеров для этой презентации.
          </div>

          <div v-else class="space-y-4">
            <div
              v-for="job in renderJobs"
              :key="job.id"
              class="bg-bg-surface border border-text-muted rounded-xl p-4 flex flex-col gap-3"
            >
              <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div class="flex items-center gap-3 min-w-0 flex-1">
                  <div
                    class="shrink-0 w-10 h-10 rounded-lg flex items-center justify-center"
                    :class="{
                      'bg-brand-blue/10 text-brand-blue':
                        job.status === 'pending',
                      'bg-brand-amber/10 text-brand-amber':
                        job.status === 'rendering',
                      'bg-brand-green/10 text-brand-green':
                        job.status === 'completed',
                      'bg-red-500/20 text-red-500':
                        job.status === 'error' || job.status === 'failed',
                    }"
                  >
                    <svg
                      v-if="job.status === 'completed'"
                      xmlns="http://www.w3.org/2000/svg"
                      width="20"
                      height="20"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    >
                      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                      <polyline points="22 4 12 14.01 9 11.01"></polyline>
                    </svg>
                    <svg
                      v-else-if="job.status === 'rendering'"
                      class="animate-spin"
                      xmlns="http://www.w3.org/2000/svg"
                      width="20"
                      height="20"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    >
                      <path d="M21 12a9 9 0 1 1-6.219-8.56"></path>
                    </svg>
                    <svg
                      v-else-if="
                        job.status === 'error' || job.status === 'failed'
                      "
                      xmlns="http://www.w3.org/2000/svg"
                      width="20"
                      height="20"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    >
                      <circle cx="12" cy="12" r="10"></circle>
                      <line x1="15" y1="9" x2="9" y2="15"></line>
                      <line x1="9" y1="9" x2="15" y2="15"></line>
                    </svg>
                    <svg
                      v-else
                      xmlns="http://www.w3.org/2000/svg"
                      width="20"
                      height="20"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    >
                      <circle cx="12" cy="12" r="10"></circle>
                      <polyline points="12 6 12 12 16 14"></polyline>
                    </svg>
                  </div>

                  <div class="min-w-0 flex-1 pr-2">
                    <div
                      class="font-bold truncate max-w-full"
                      :title="job.file_url ? job.file_url.split('/').pop() : ''"
                    >
                      {{
                        job.file_url
                          ? job.file_url.split("/").pop()
                          : `ID #${job.id} - ${job.settings?.format?.toUpperCase()}`
                      }}
                    </div>
                    <div class="text-xs text-text-secondary flex flex-wrap gap-x-2 gap-y-0.5">
                      <span>{{ formatDate(job.created_at) }}</span>
                      <span class="opacity-50">•</span>
                      <span>{{ job.settings?.fps }} FPS</span>
                      <span class="opacity-50 hidden sm:inline">•</span>
                      <span>{{ job.settings?.quality }}</span>
                    </div>
                  </div>
                </div>

                <div class="flex items-center gap-2 shrink-0 flex-wrap justify-end">
                  <div v-if="job.status === 'completed' && job.file_url">
                    <button
                      @click="previewJob = job"
                      class="px-4 py-2 bg-brand-blue/20 hover:bg-brand-blue/30 text-brand-blue rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                      >
                        <polygon points="5 3 19 12 5 21 5 3"></polygon>
                      </svg>
                      Смотреть
                    </button>
                    <a
                      :href="job.file_url"
                      download
                      class="px-4 py-2 bg-brand-green/20 hover:bg-brand-green/30 text-brand-green rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                      >
                        <path
                          d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"
                        ></path>
                        <polyline points="7 10 12 15 17 10"></polyline>
                        <line x1="12" y1="15" x2="12" y2="3"></line>
                      </svg>
                      Скачать
                    </a>
                  </div>

                  <button
                    @click="reRenderJob(job)"
                    class="p-2 bg-bg-surface hover:bg-bg-surface text-text-secondary hover:text-text-primary rounded-lg transition-colors"
                    title="Рендерить заново с такими же настройками"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    >
                      <polyline points="23 4 23 10 17 10"></polyline>
                      <polyline points="1 20 1 14 7 14"></polyline>
                      <path
                        d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"
                      ></path>
                    </svg>
                  </button>
                  <button
                    @click="deleteJob(job.id)"
                    class="p-2 bg-red-500/10 hover:bg-red-500/20 text-red-500/70 hover:text-red-500 rounded-lg transition-colors"
                    title="Удалить рендер"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    >
                      <polyline points="3 6 5 6 21 6"></polyline>
                      <path
                        d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"
                      ></path>
                    </svg>
                  </button>
                </div>

                <div
                  v-if="job.status === 'rendering' || job.status === 'pending'"
                  class="text-brand-amber text-right flex flex-col items-end justify-center min-w-[60px]"
                >
                  <span class="font-bold whitespace-nowrap"
                    >{{ job.progress?.toFixed(1) || 0 }}%</span
                  >
                  <span
                    v-if="job.settings?.eta !== undefined"
                    class="text-[10px] opacity-70 whitespace-nowrap mt-0.5"
                  >
                    {{ formatETA(job.settings.eta) }}
                  </span>
                </div>
              </div>

              <!-- Progress Bar -->
              <div
                v-if="job.status === 'rendering' || job.status === 'pending'"
                class="w-full h-1.5 bg-black/50 rounded-full overflow-hidden mt-1"
              >
                <div
                  class="h-full bg-brand-amber transition-all duration-1000 ease-linear"
                  :style="{ width: `${job.progress || 0}%` }"
                ></div>
              </div>

              <!-- Error message -->
              <div
                v-if="
                  (job.status === 'error' || job.status === 'failed') &&
                  job.error_log
                "
                class="text-xs text-red-400 bg-red-500/10 p-2 rounded border border-red-500/20 break-all"
              >
                {{ job.error_log }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Плеер-предпросмотр отрендеренного видео (без скачивания) -->
    <div
      v-if="isOpen && previewJob && previewJob.file_url"
      class="fixed inset-0 z-[10000] bg-black/95 flex flex-col items-center justify-center p-3 md:p-6"
      @click.self="previewJob = null"
    >
      <div
        class="w-full max-w-5xl flex items-center justify-between gap-3 mb-3 text-text-primary"
      >
        <div class="font-bold truncate min-w-0">
          {{ previewJob.file_url.split("/").pop() }}
        </div>
        <div class="flex items-center gap-2 shrink-0">
          <a
            :href="previewJob.file_url"
            download
            class="px-3 py-1.5 bg-brand-green/20 hover:bg-brand-green/30 text-brand-green rounded-lg text-sm font-medium transition-colors"
            >Скачать</a
          >
          <button
            @click="previewJob = null"
            class="p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-bg-surface transition-colors"
            title="Закрыть"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="22"
              height="22"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
      </div>
      <video
        :src="previewJob.file_url"
        controls
        autoplay
        playsinline
        class="w-full max-w-5xl max-h-[78vh] rounded-xl bg-black shadow-2xl"
      ></video>
    </div>
  </div>
</template>
