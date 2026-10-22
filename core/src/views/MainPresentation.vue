<template>
  <div class="presentation-root">
    <PageSkeleton v-if="loading" variant="player" />
    <SlidePresentation
      v-else-if="activeFolderData"
      :totalSlides="totalSlides"
      :thumbnails="thumbnailsList"
      :initialSlide="startSlide"
      :timeline="computedTimeline"
      :audioTimeline="activeFolderData.audio_timeline"
      :slidesData="activeFolderData.slides"
      :isEditorOpen="showEditorModal"
      :renderWidth="renderWidth"
      :renderHeight="renderHeight"
      @edit-slide="handleEditSlide"
      @add-slide="handleAddSlide"
      @rename-slide="handleRenameSlide"
      @duplicate-slide="handleDuplicateSlide"
      @delete-slide="handleDeleteSlideIndex"
      @set-slide-variant="handleSlideVariant"
      @open-ai="showAiModal = true"
      @open-settings="handleOpenSettings"
      @close-editor="handleCloseEditor"
      @update-timing="handleUpdateTiming"
      @update-local-timing="handleUpdateLocalTiming"
      @dragging-local-timing="handleDraggingLocalTiming"
      @update-audio-timeline="handleUpdateAudioTimeline"
      @request-add-audio="handleRequestAddAudio"
      @toggle-record="toggleRecording"
      @request-generate-voice="handleRequestGenerateVoice"
      @edit-clip="handleEditClip"
      :recordingTrackId="recordingTrackId"
      @open-media-library="openMediaLibrary('manage')"
      @open-render-manager="handleOpenRenderManager"
      @fullscreen-change="isFullscreen = $event"
    >
      <Slide
        v-for="(slide, index) in activeFolderData.slides"
        :key="slide.id"
        :index="index"
        :folder="currentFolder"
        :title="slide.title"
        :subtitle="slide.subtitle"
        :layout="slide.layout"
        :clicks="slide.clicks"
        :startTime="slide.start_time || slide.startTime || 0"
      >
        <template #default="{ clicks }">
          <!-- We use a dynamic component based on componentsMap -->
          <component
            :is="componentsMap[slide.component]"
            :mobile="isMobile"
            :clicks="clicks"
            :slide-start-time="slide.start_time || slide.startTime || 0"
            v-bind="resolvedPayload(slide)"
          />
        </template>
      </Slide>
    </SlidePresentation>

    <div
      v-else-if="!activeFolderData && !loading"
      class="viewport-h viewport-w flex flex-col items-center justify-center bg-bg-base text-text-primary"
    >
      <div class="text-2xl font-bold mb-4 text-[#EF4444]">
        Error: Presentation not found
      </div>
      <p class="text-text-secondary">
        Please ensure the backend is running and the database is seeded.
      </p>
    </div>

    <SlideEditorModal
      ref="editorModalRef"
      :isOpen="showEditorModal"
      :isFullscreen="isFullscreen"
      :slide="editingSlide"
      :previousSlide="editingSlidePrevious"
      :nextSlide="editingSlideNext"
      :save-warnings="saveWarnings"
      :preset-info="editorPreset"
      :project-defaults="editingSlide ? defaultsFor(editingSlide.component) : {}"
      @close="handleCloseEditor"
      @update-style="handleUpdateStyle"
      @save="handleSaveSlide"
      @delete="handleDeleteSlide"
      @live-update="handleLiveUpdate"
      @open-media-library="openMediaLibrary('select')"
    />

    <ComponentSelectModal
      :isOpen="showComponentSelectModal"
      @close="showComponentSelectModal = false"
      @select="handleComponentSelect"
    />

    <MediaLibraryModal
      :isOpen="showMediaLibraryModal"
      :mode="mediaLibraryMode"
      :presentationId="activeFolderData?.id || 0"
      :mediaFiles="activeFolderData?.media_files || []"
      @close="showMediaLibraryModal = false"
      @select="handleMediaSelect"
      @select-batch="handleBatchMediaSelect"
      @uploaded="handleMediaUpload"
      @deleted="handleMediaDeleted"
      @edit-ai-voice="handleEditAIVoice"
    />

    <AIVoiceModal
      :isOpen="showAIVoiceModal"
      :presentationId="activeFolderData?.id || 0"
      :initialData="aiVoiceInitialData"
      :defaults="projectConfig?.voice || null"
      @close="showAIVoiceModal = false"
      @generated="handleAIVoiceGenerated"
    />

    <RenderManagerModal
      :isOpen="showRenderManagerModal"
      :presentationId="activeFolderData?.id || 0"
      :presentationTitle="activeFolderData?.title || ''"
      :slidesData="activeFolderData?.slides || []"
      @close="showRenderManagerModal = false"
    />

    <PresentationSettingsModal
      :show="showSettingsModal"
      :presentation-id="activeFolderData?.id"
      :preset-info="editorPreset"
      :presentation-variant="activeFolderData?.variant || ''"
      :chessboard="!!activeFolderData?.chessboard"
      :visibility="activeFolderData?.visibility || 'public'"
      @close="showSettingsModal = false"
      @update-style="handleUpdateStyle"
      @update-variant="handleSettingsVariant"
      @update-chessboard="handleSettingsChessboard"
      @update-visibility="handleSettingsVisibility"
      @palette-changed="handlePaletteChanged"
      @open-ai="showAiModal = true"
    />

    <AiAssistantModal
      :show="showAiModal"
      :presentation-id="activeFolderData?.id"
      @close="showAiModal = false"
      @applied="handleAiApplied"
    />

    <!-- Toast вместо alert() -->
    <div
      v-if="toast.msg"
      class="fixed left-1/2 -translate-x-1/2 z-[500] px-5 py-3 rounded-xl shadow-2xl text-sm font-medium flex items-center gap-3 w-[92vw] max-w-md"
      :class="toast.type === 'error' ? 'bg-red-600 text-white' : 'bg-gray-900 text-white'"
      :style="isMobile
        ? { top: 'calc(env(safe-area-inset-top, 0px) + 12px)' }
        : { bottom: 'calc(env(safe-area-inset-bottom, 0px) + 1.5rem)' }"
    >
      <span class="flex-1">{{ toast.msg }}</span>
      <button @click="toast.msg = ''" class="opacity-70 hover:opacity-100 font-bold">✕</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, provide, onMounted, onUnmounted, watch } from "vue";
import { useDirector } from "../composables/useDirector.js";
import { useScreenRecorder } from "../composables/useScreenRecorder.js";
import { loadThemeForPresentation } from "../composables/useTheme.js";
import { loadVariants } from "../composables/useVariant.js";
import { Icon } from "@iconify/vue";

import SlidePresentation from "../components/engine/SlidePresentation.vue";
import Slide from "../components/engine/Slide.vue";
import SlideEditorModal from "../components/ui/SlideEditorModal.vue";
import ComponentSelectModal from "../components/ui/ComponentSelectModal.vue";
import MediaLibraryModal from "../components/ui/MediaLibraryModal.vue";
import AIVoiceModal from "../components/ui/AIVoiceModal.vue";
import RenderManagerModal from "../components/ui/RenderManagerModal.vue";
import PresentationSettingsModal from "../components/ui/PresentationSettingsModal.vue";
import PageSkeleton from "../components/ui/PageSkeleton.vue";
import AiAssistantModal from "../components/ui/AiAssistantModal.vue";

import {
  fetchPresentations,
  updateSlide,
  createSlide,
  deleteSlide,
  updatePresentation,
  uploadMedia,
  fetchPresets,
  fetchPresentationStyle,
  updatePresentationStyle,
  fetchPresentationAccess,
  fetchPresentationConfig,
  fetchPresentation,
} from "../services/api";
import { useAudioRecorder } from "../composables/useAudioRecorder.js";
import { useAuth } from "../composables/useAuth";

import { componentsMap } from "../config/componentsRegistry.js";
import { useMobile } from "../composables/useMobile";

const { isMobile } = useMobile();
const { startRecording } = useScreenRecorder();

import { useRoute } from "vue-router";

const route = useRoute();
const currentFolder = ref(route.params.slug || "1"); // default to ID 1
provide("currentFolder", currentFolder);

const urlParams = new URLSearchParams(window.location.search);
const startSlide = parseInt(urlParams.get("slide") || "0", 10);
const renderWidth = urlParams.get("w") ? parseInt(urlParams.get("w"), 10) : null;
const renderHeight = urlParams.get("h") ? parseInt(urlParams.get("h"), 10) : null;

const activeFolderData = ref(null);

// AUTH_PLAN Ф2: режим просмотра. При AUTH_MODE=on редактор доступен только
// owner/editor презентации; иначе (off) — как раньше, всем.
const { authMode } = useAuth();
const accessInfo = ref({ can_edit: false, can_style: false, role: null });

// BRAND KIT проекта: дефолты компонентов (лого/QR/контакты), чтобы не дублировать
// их в payload каждого слайда. payload слайда всегда перекрывает дефолт.
const projectConfig = ref({});
const projectConfigId = ref(null);
provide("projectConfig", projectConfig);

const defaultsFor = (component) => {
  const cfg = projectConfig.value || {};
  const out = { ...(cfg.defaults?.[component] || {}) };
  if (component === "OutroSlide") {
    out.logo = out.logo || cfg.brand?.logo;
    out.qr_code = out.qr_code || cfg.brand?.qr_code;
    // Авто-QR проекта, если QR-файл не задан, но есть данные (qr_data/telegram/site)
    if (!out.qr_code && projectConfigId.value) {
      const hasData = cfg.brand?.qr_data || cfg.contacts?.telegram || cfg.contacts?.site;
      if (hasData) out.qr_code = `/api/projects/${projectConfigId.value}/qr.svg`;
    }
    out.handle = out.handle || cfg.contacts?.telegram;
  }
  return Object.fromEntries(
    Object.entries(out).filter(([, v]) => v !== undefined && v !== null && v !== ""),
  );
};

// payload слайда перекрывает дефолты проекта, НО пустые значения (''/null) —
// не перекрывают: иначе старое пустое поле глушило бы брендовый дефолт.
// BRAND_CLEAR: явный "не подставлять бренд" для конкретного поля слайда.
const BRAND_CLEAR = "__none__";

const resolvedPayload = (slide) => {
  const out = { ...defaultsFor(slide.component) };
  const payload = slide.data?.payload || slide.data || {};
  for (const [k, v] of Object.entries(payload)) {
    if (v === BRAND_CLEAR) {
      // принудительно пусто — только для скалярных дефолтов (иначе не подменяем тип)
      const def = out[k];
      if (def === undefined || typeof def !== "object") out[k] = "";
      continue;
    }
    if (v === "" || v === null || v === undefined) continue; // пусто → дефолт бренда
    out[k] = v;
  }
  return out;
};
provide(
  "canEdit",
  computed(() => (authMode.value !== "on" ? true : !!accessInfo.value.can_edit)),
);
watch(
  () => activeFolderData.value?.id,
  async (id) => {
    if (!id) return;
    try {
      accessInfo.value = await fetchPresentationAccess(id);
    } catch {
      accessInfo.value = { can_edit: authMode.value !== "on" };
    }
    try {
      const d = await fetchPresentationConfig(id);
      projectConfig.value = d.config || {};
      projectConfigId.value = d.project_id || null;
    } catch {
      projectConfig.value = {};
      projectConfigId.value = null;
    }
  },
  { immediate: true },
);
const loading = ref(true);

// Toast вместо alert() — не блокирует UI, сам гаснет
const toast = ref({ msg: "", type: "error" });
let toastTimer = null;
const showToast = (msg, type = "error", ms = 4500) => {
  toast.value = { msg, type };
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toast.value.msg = "";
  }, ms);
};
const showRenderManagerModal = ref(false);

const prepareForCapture = () => {
  window.dispatchEvent(new CustomEvent("presentation:close-all-modals"));
  if (typeof handleCloseEditor === "function") {
    handleCloseEditor();
  }
  showRenderManagerModal.value = false;
  showEditorModal.value = false;
  showComponentSelectModal.value = false;
  showMediaLibraryModal.value = false;
  showAIVoiceModal.value = false;
  editingSlide.value = null;
  originalEditingSlideData.value = null;
};

const startLiveCapture = async (preset = "landscape") => {
  if (!activeFolderData.value?.id) return;

  prepareForCapture();

  try {
    if (!navigator.mediaDevices?.getDisplayMedia) {
      showToast("Браузер не поддерживает захват экрана. Используйте Chromium/Chrome.");
      return;
    }

    const dimensions =
      preset === "portrait"
        ? { width: 1280, height: 1920 }
        : { width: 1920, height: 1280 };
    const dpr = window.devicePixelRatio || 1;
    const captureWidth = Math.round(dimensions.width * dpr);
    const captureHeight = Math.round(dimensions.height * dpr);

    const slides = activeFolderData.value.slides || [];
    const endMarker = slides.find(
      (slide) => slide.component === "EndMarkerSlide",
    );
    const presentationEndMs = endMarker
      ? Number(endMarker.start_time || endMarker.startTime || 0)
      : slides.reduce((max, slide) => {
          const start = Number(slide.start_time || slide.startTime || 0);
          return Math.max(max, start + 5000);
        }, 6000);

    await startRecording(null, {
      width: captureWidth,
      height: captureHeight,
      fps: 60,
      quality: "premium",
      autoPlay: true,
      endTimeMs: presentationEndMs,
      title: activeFolderData.value?.title || "",
      format: preset,
    });

      } catch (err) {
    console.error("Live capture failed:", err);
    showToast("Не удалось запустить live capture. Разрешите доступ к экрану.");
  }
};


const handleOpenRenderManager = () => {
  showRenderManagerModal.value = true;
};

// Дефолтный вариант отрисовки презентации (слайд может переопределить через payload.variant).
const defaultVariant = computed(() => activeFolderData.value?.variant || null);
provide("defaultVariant", defaultVariant);

// Шахматка фона слайдов (UX-5, opt-in): Slide.vue читает через inject.
const slideChessboard = computed(() => !!activeFolderData.value?.chessboard);
provide("slideChessboard", slideChessboard);

const handleAudioClipError = async (e) => {
  // Never run Timeline Cleaner during headless render mode since audio requests are intentionally blocked by Playwright
  if (route.query.render === "true" || urlParams.get("render") === "true") {
    return;
  }

  const { clipId, src } = e.detail;
  if (!activeFolderData.value || !activeFolderData.value.audio_timeline) return;

  // Удаляем клип ТОЛЬКО если файл реально отсутствует (404).
  // Транзиентные сетевые ошибки (перезапуск backend, обрыв) не должны стирать озвучку/музыку.
  try {
    const resp = await fetch(src, { method: "HEAD" });
    if (resp.status !== 404) return;
  } catch {
    return;
  }

  let timelineChanged = false;
  const timeline = JSON.parse(
    JSON.stringify(activeFolderData.value.audio_timeline),
  );

  timeline.tracks.forEach((track) => {
    if (track.clips) {
      const originalLength = track.clips.length;
      // Keep clips that aren't the broken one
      track.clips = track.clips.filter(
        (clip) => !(clip.id === clipId || clip.src === src),
      );
      if (track.clips.length !== originalLength) {
        timelineChanged = true;
      }
    }
  });

  if (timelineChanged) {
    console.warn(
      `[Timeline Cleaner] Removing broken clip ${clipId} (${src}) from timeline`,
    );
    handleUpdateAudioTimeline(timeline);
  }
};

const handleAIVoiceUpdated = (updatedData) => {
  showAIVoiceModal.value = false;
  if (!activeFolderData.value || !activeFolderData.value.audio_timeline) return;

  const timeline = JSON.parse(
    JSON.stringify(activeFolderData.value.audio_timeline),
  );
  const track = timeline.tracks.find(
    (t) => t.id === aiVoiceTargetTrackId.value,
  );
  if (track) {
    const clipIndex = track.clips.findIndex((c) => c.id === updatedData.clipId);
    if (clipIndex !== -1) {
      track.clips[clipIndex].playbackRate = updatedData.playbackRate;
      track.clips[clipIndex].ai_settings = updatedData.settings;
      handleUpdateAudioTimeline(timeline);
    }
  }
};

const closeAllModals = () => {
  showRenderManagerModal.value = false;
  showEditorModal.value = false;
  showComponentSelectModal.value = false;
  showMediaLibraryModal.value = false;
  showAIVoiceModal.value = false;
  editingSlide.value = null;
  originalEditingSlideData.value = null;
};

const loadCurrent = async (slug) => {
  currentFolder.value = slug || currentFolder.value;
  loading.value = true;
  try {
    // Публичный просмотр по ссылке: тянем презентацию НАПРЯМУЮ по id.
    // Список GET /presentations/ при AUTH_MODE=on скоупится и может не содержать
    // презентацию чужого проекта — тогда страница падала на presentations[0]
    // (чужой стиль + застывший первый слайд, в т.ч. в рендере).
    let found = null;
    const numericId = /^\d+$/.test(String(currentFolder.value));
    if (numericId) {
      // числовой slug = id презентации: тянем напрямую. Если недоступна/нет —
      // НЕ подменяем первой презентацией из списка (иначе чужой контент/стиль).
      found = await fetchPresentation(Number(currentFolder.value)).catch(() => null);
    } else {
      // legacy: slug не число — ищем по списку
      const presentations = await fetchPresentations();
      found = presentations.find(
        (p) => p.id.toString() === currentFolder.value,
      ) || presentations[0] || null;
    }

    // Авто-добавление EndMarkerSlide — это ЗАПИСЬ. Для анонима/наблюдателя
    // (AUTH_MODE=on, нет прав editor) её быть не должно: раньше 401 прерывал
    // загрузку, и публичный просмотр по ссылке показывал «не найдено».
    const checkAndAddEndMarker = async (folder) => {
      try {
        if (!folder || !folder.slides) return;
        if (folder.slides.some((s) => s.component === "EndMarkerSlide")) return;
        if (authMode.value === "on") {
          const acc = await fetchPresentationAccess(folder.id);
          if (!acc.can_edit) return;
        }
        const lastSlide = folder.slides[folder.slides.length - 1];
        const endTime = lastSlide ? (lastSlide.start_time || 0) + 5000 : 5000;
        const endMarker = await createSlide(folder.id, {
          slide_id: `slide_${Date.now()}_end`,
          component: "EndMarkerSlide",
          title: "Конец презентации",
          start_time: endTime,
          order_index: folder.slides.length,
        });
        folder.slides.push(endMarker);
      } catch (e) {
        console.warn("EndMarker auto-add skipped:", e?.message || e);
      }
    };

    // Сброс прежней презентации ДО присвоения новой: аудио-движок и плеер
    // не должны сохранять таймлайн/клипы предыдущей презентации.
    activeFolderData.value = null;

    if (found) {
      found.slides = found.slides || [];
      found.slides.sort((a, b) => (a.start_time || 0) - (b.start_time || 0));
      activeFolderData.value = found; // сначала показываем, досоздание — фоном
      await checkAndAddEndMarker(found);
    }

    // Фаза 2: применяем тему проекта, к которому относится презентация
    if (activeFolderData.value) {
      await loadThemeForPresentation(activeFolderData.value.id);
    }
  } catch (err) {
    console.error("Failed to load presentations from API:", err);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  window.addEventListener("audio-clip-error", handleAudioClipError);
  window.addEventListener("presentation:close-all-modals", closeAllModals);
  // Варианты отрисовки грузим сразу (не лениво): иначе первый кадр рисуется
  // по FALLBACK без блюра, и стекло «вщёлкивается» с запозданием.
  loadVariants();
  loadCurrent(route.params.slug || currentFolder.value);
});

// Переход между презентациями (/p/8 -> /p/9) переиспользует компонент без
// повторного mount — перезагружаем данные и сбрасываем аудио предыдущей.
watch(
  () => route.params.slug,
  (slug) => {
    if (slug) loadCurrent(slug);
  },
);

onUnmounted(() => {
  window.removeEventListener("audio-clip-error", handleAudioClipError);
  window.removeEventListener("presentation:close-all-modals", closeAllModals);
  // Покидая презентацию — глушим озвучку и чистим таймлайн/слушатели,
  // чтобы аудио не «протекало» в следующую презентацию.
  try {
    const director = useDirector();
    director.stop();
    director.loadAudioTimeline({ tracks: [] });
    director.clearListeners();
  } catch (e) {
    /* noop */
  }
});

const { loadAudioTimeline } = useDirector();

const computedVirtualSfx = computed(() => {
  if (!activeFolderData.value) return [];
  const virtualClips = [];

  for (let i = 0; i < activeFolderData.value.slides.length; i++) {
    const slide = activeFolderData.value.slides[i];
    // Get current slide time, supporting both snake_case and camelCase
    let slideTime = Number(slide.start_time ?? slide.startTime);
    if (isNaN(slideTime)) slideTime = 0;

    const payload = slide.data?.payload || slide.data || {};

    // Find next slide time to cap the audio
    const nextSlide = activeFolderData.value.slides[i + 1];
    let nextSlideTime = Infinity;
    if (nextSlide) {
      nextSlideTime = Number(nextSlide.start_time ?? nextSlide.startTime);
      if (isNaN(nextSlideTime)) nextSlideTime = slideTime + 15000;
    }

    const extractSfx = (obj) => {
      if (!obj || typeof obj !== "object") return;

      const nodeSfx = obj.sfx && obj.sfx.src ? obj.sfx : null;
      const parentSfx =
        obj !== payload &&
        payload.item_sfx &&
        payload.item_sfx.src &&
        obj.start_time !== undefined
          ? payload.item_sfx
          : null;
      const sfxToUse = nodeSfx || parentSfx;

      if (
        (obj.start_time !== undefined || obj.time !== undefined) &&
        sfxToUse &&
        !sfxToUse.muted &&
        sfxToUse.src
      ) {
        const itemTime = Number(
          obj.start_time !== undefined ? obj.start_time : obj.time,
        );
        if (!isNaN(itemTime)) {
          const timeOffset = Number(sfxToUse.time_offset) || 0;
          const calcStartTime = slideTime + itemTime + timeOffset;
          // Cap end time so it doesn't bleed into the next slide, but only if nextSlideTime is valid and in the future
          let maxEndTime = calcStartTime + (sfxToUse.duration || 5000);
          if (nextSlideTime > calcStartTime) {
            maxEndTime = Math.min(maxEndTime, nextSlideTime);
          }

          virtualClips.push({
            id: `vsfx_${slide.id}_${calcStartTime}_${sfxToUse.src.replace(/[^a-zA-Z0-9]/g, "")}`,
            src: sfxToUse.src,
            start_time: calcStartTime,
            end_time: maxEndTime,
            media_offset: sfxToUse.media_offset || 0,
            volume: sfxToUse.volume !== undefined ? sfxToUse.volume : 1.0,
            muted: false,
            isVirtual: true,
          });
        }
      }

      if (Array.isArray(obj)) {
        obj.forEach((item) => extractSfx(item));
      } else {
        Object.values(obj).forEach((val) => extractSfx(val));
      }
    };
    extractSfx(payload);
  }

  // Deduplicate clips with the exact same start_time and src
  const uniqueClips = [];
  const seen = new Set();
  for (const clip of virtualClips) {
    const key = clip.src + "_" + clip.start_time;
    if (!seen.has(key)) {
      seen.add(key);
      uniqueClips.push(clip);
    }
  }

  return uniqueClips;
});

watch(
  () => [activeFolderData.value?.audio_timeline, computedVirtualSfx.value],
  ([newTimeline, virtualSfx]) => {
    const timelineToLoad = newTimeline || { tracks: [] };
    loadAudioTimeline(timelineToLoad, virtualSfx);
  },
  { immediate: true, deep: true },
);

const computedTimeline = computed(() => {
  if (!activeFolderData.value) return [];
  const events = [];
  activeFolderData.value.slides.forEach((slide, index) => {
    const slideTime = Number(slide.start_time) || 0;
    events.push({
      time: slideTime,
      type: "SLIDE_CHANGE",
      payload: { slideIndex: index },
    });

    // Add old director events if they exist
    if (slide.events) {
      slide.events.forEach((event) => {
        events.push({
          time: slideTime + (Number(event.time) || 0),
          type: event.event_type || event.action,
          action: event.action || event.event_type,
          target: event.payload?.target,
          payload: event.payload,
        });
      });
    }

    // Dynamically extract start_time keys from payload arrays for the new relativeTime engine
    const payload = slide.data?.payload || slide.data || {};
    const extractStartTimes = (obj) => {
      if (!obj || typeof obj !== "object") return;

      if (obj.start_time !== undefined) {
        const itemTime = Number(obj.start_time);
        if (!isNaN(itemTime)) {
          events.push({
            time: slideTime + itemTime,
            type: "INTERNAL_ANIMATION",
            payload: obj,
          });
        }
      }

      if (Array.isArray(obj)) {
        obj.forEach((item) => extractStartTimes(item));
      } else {
        Object.values(obj).forEach((val) => extractStartTimes(val));
      }
    };
    extractStartTimes(payload);
  });
  return events.sort((a, b) => (Number(a.time) || 0) - (Number(b.time) || 0));
});

const totalSlides = computed(() => {
  return activeFolderData.value ? activeFolderData.value.slides.length : 0;
});

const thumbnailsList = computed(() => {
  return activeFolderData.value
    ? activeFolderData.value.slides.map((s) => s.title || s.slide_id)
    : [];
});

// Editor Modal State & Handlers
const showEditorModal = ref(false);
const editingSlide = ref(null);
const saveWarnings = ref([]);
const editingSlidePrevious = computed(() => {
  if (!activeFolderData.value || !editingSlide.value) return null;
  const index = activeFolderData.value.slides.findIndex(
    (s) => s.id === editingSlide.value.id,
  );
  return index > 0 ? activeFolderData.value.slides[index - 1] : null;
});
const editingSlideNext = computed(() => {
  if (!activeFolderData.value || !editingSlide.value) return null;
  const index = activeFolderData.value.slides.findIndex(
    (s) => s.id === editingSlide.value.id,
  );
  return index >= 0 && index < activeFolderData.value.slides.length - 1
    ? activeFolderData.value.slides[index + 1]
    : null;
});

// Component Selector
const showComponentSelectModal = ref(false);

// Media Library
const showMediaLibraryModal = ref(false);
const mediaLibraryMode = ref("manage");

const handleMediaDeleted = (mediaId) => {
  if (activeFolderData.value && activeFolderData.value.media_files) {
    activeFolderData.value.media_files =
      activeFolderData.value.media_files.filter((m) => m.id !== mediaId);
  }
};

watch(
  () => activeFolderData.value?.slides,
  (newSlides) => {
    if (editingSlide.value && newSlides) {
      const updatedSlide = newSlides.find(
        (s) => s.id === editingSlide.value.id,
      );
      if (
        updatedSlide &&
        updatedSlide.start_time !== editingSlide.value.start_time
      ) {
        editingSlide.value.start_time = updatedSlide.start_time;
      }
    }
  },
  { deep: true },
);

// Media Library
const activeAudioTrack = ref(null);

const openMediaLibrary = (mode = "manage") => {
  activeAudioTrack.value = null;
  mediaLibraryMode.value = mode;
  showMediaLibraryModal.value = true;
};

const handleRequestAddAudio = (trackId) => {
  activeAudioTrack.value = trackId;
  mediaLibraryMode.value = "select";
  showMediaLibraryModal.value = true;
};

const originalEditingSlideData = ref(null);

const handleEditSlide = (index) => {
  // If we are switching from another slide without saving, revert it first
  if (
    editingSlide.value &&
    originalEditingSlideData.value &&
    activeFolderData.value
  ) {
    const targetId = activeFolderData.value.slides[index]?.id;
    if (editingSlide.value.id !== targetId) {
      const prevIdx = activeFolderData.value.slides.findIndex(
        (s) => s.id === editingSlide.value.id,
      );
      if (prevIdx !== -1) {
        activeFolderData.value.slides[prevIdx] = originalEditingSlideData.value;
      }
    }
  }

  editingSlide.value = activeFolderData.value.slides[index];
  originalEditingSlideData.value = JSON.parse(
    JSON.stringify(editingSlide.value),
  );
  showEditorModal.value = true;
  // Вектор стилей презентации для бейджа/пикера в редакторе
  editorPreset.value = null;
  if (activeFolderData.value?.id) {
    fetchPresentationStyle(activeFolderData.value.id)
      .then((st) => {
        editorPreset.value = st;
      })
      .catch(() => {
        editorPreset.value = null;
      });
  }
};

const editorPreset = ref(null);

const handleUpdateStyle = async ({ style_preset, style_lock }) => {
  if (!activeFolderData.value?.id) return;
  try {
    const st = await updatePresentationStyle(activeFolderData.value.id, {
      style_preset,
      style_lock,
    });
    const presetList = await fetchPresets().catch(() => []);
    const preset = (presetList || []).find((p) => p.slug === st.style_preset) || null;
    editorPreset.value = { ...st, preset };
  } catch (err) {
    console.error("Failed to update style:", err);
    showToast("Не удалось обновить вектор стилей.");
  }
};

const handleCloseEditor = () => {
  if (
    originalEditingSlideData.value &&
    editingSlide.value &&
    activeFolderData.value
  ) {
    // Revert local changes
    const idx = activeFolderData.value.slides.findIndex(
      (s) => s.id === editingSlide.value.id,
    );
    if (idx !== -1) {
      activeFolderData.value.slides[idx] = originalEditingSlideData.value;
    }
  }
  showEditorModal.value = false;
  editingSlide.value = null;
  originalEditingSlideData.value = null;
  saveWarnings.value = [];
};

const handleLiveUpdate = (payload) => {
  if (!editingSlide.value) return;
  // Find in activeFolderData and mutate locally
  const index = activeFolderData.value.slides.findIndex(
    (s) => s.id === editingSlide.value.id,
  );
  if (index !== -1) {
    const originalId = activeFolderData.value.slides[index].id;

    const oldTime = activeFolderData.value.slides[index].start_time || 0;
    const newTime =
      payload.start_time !== undefined ? payload.start_time : oldTime;
    const delta = newTime - oldTime;

    activeFolderData.value.slides[index] = {
      ...activeFolderData.value.slides[index],
      ...payload,
      id: originalId,
    };

    if (delta !== 0) {
      for (let i = index + 1; i < activeFolderData.value.slides.length; i++) {
        activeFolderData.value.slides[i].start_time =
          (activeFolderData.value.slides[i].start_time || 0) + delta;
      }
    }

    // Sort to maintain strict chronological order
    activeFolderData.value.slides.sort(
      (a, b) => (a.start_time || 0) - (b.start_time || 0),
    );
  }
};

const handleUpdateTiming = async (slideIndex, newTime) => {
  if (!activeFolderData.value) return;
  // newTime is the final time of the dragged slide.
  // Note: the local activeFolderData has ALREADY been mutated by DirectorDebugPanel,
  // so we just need to save all slides from slideIndex onwards to the backend.

  const promises = [];

  for (let i = slideIndex; i < activeFolderData.value.slides.length; i++) {
    const s = activeFolderData.value.slides[i];

    if (
      originalEditingSlideData.value &&
      originalEditingSlideData.value.id === s.id
    ) {
      originalEditingSlideData.value.start_time = s.start_time;
    }

    const payload = {
      slide_id: s.slide_id || `slide_${Date.now()}_${i}`,
      component: s.component || "Slide",
      start_time: s.start_time || 0,
      title: s.title || null,
      subtitle: s.subtitle || null,
      layout: s.layout || null,
      order_index: s.order_index !== undefined ? s.order_index : i,
      data: s.data ? { payload: s.data.payload || {} } : { payload: {} },
      events: s.events || [],
    };
    promises.push(updateSlide(s.id, payload));
  }

  try {
    await Promise.all(promises);
  } catch (err) {
    console.error("Failed to update slide timings", err);
  }
};

const handleUpdateLocalTiming = async (slideIndex) => {
  if (!activeFolderData.value) return;

  const s = activeFolderData.value.slides[slideIndex];
  if (!s) return;

  const payload = {
    slide_id: s.slide_id,
    component: s.component || "Slide",
    start_time: s.start_time || 0,
    title: s.title || null,
    subtitle: s.subtitle || null,
    layout: s.layout || null,
    order_index: s.order_index,
    data: s.data ? { payload: s.data.payload || {} } : { payload: {} },
    events: s.events || [],
  };

  // No need to sync editor here, it's synced during drag
  try {
    await updateSlide(s.id, payload);
  } catch (err) {
    console.error("Failed to update local slide timing", err);
  }
};

const handleDraggingLocalTiming = (slideIndex, newSlideData) => {
  if (activeFolderData.value && activeFolderData.value.slides[slideIndex]) {
    activeFolderData.value.slides[slideIndex].data = { ...newSlideData };
  }
  if (
    editingSlide.value &&
    activeFolderData.value &&
    activeFolderData.value.slides[slideIndex]
  ) {
    const s = activeFolderData.value.slides[slideIndex];
    if (editingSlide.value.id === s.id && editorModalRef.value) {
      if (typeof editorModalRef.value.syncData === "function") {
        editorModalRef.value.syncData(newSlideData.payload || newSlideData);
      }
    }
  }
};

const handleUpdateAudioTimeline = async (newAudioTimeline) => {
  if (!activeFolderData.value) return;

  // Clean virtual clips before saving
  const cleanedTimeline = JSON.parse(JSON.stringify(newAudioTimeline));
  if (cleanedTimeline.tracks) {
    cleanedTimeline.tracks.forEach((track) => {
      if (track.clips) {
        track.clips = track.clips.filter((clip) => !clip.isVirtual);
      }
    });
  }

  activeFolderData.value.audio_timeline = cleanedTimeline;
  try {
    await updatePresentation(activeFolderData.value.id, {
      title: activeFolderData.value.title,
      audio_src: activeFolderData.value.audio_src,
      audio_timeline: cleanedTimeline,
    });
  } catch (err) {
    console.error("Failed to save audio timeline:", err);
  }
};

const findNextAvailableSlot = (track, startTime, durationMs) => {
  if (!track || !track.clips) return startTime;
  let currentStart = startTime;

  const sortedClips = [...track.clips].sort(
    (a, b) => a.start_time - b.start_time,
  );

  for (const clip of sortedClips) {
    const clipEnd = clip.end_time || clip.start_time + 5000;
    if (currentStart < clipEnd && currentStart + durationMs > clip.start_time) {
      currentStart = clipEnd + 100;
    }
  }
  return currentStart;
};

const handleAudioRecorded = async ({ trackId, file, startTime }) => {
  if (!activeFolderData.value) return;
  try {
    const uploaded = await uploadMedia(
      activeFolderData.value.id,
      file,
      "voice",
    );

    const timeline = JSON.parse(
      JSON.stringify(activeFolderData.value.audio_timeline),
    );
    const track = timeline.tracks.find((t) => t.id === trackId);
    if (track) {
      // Относительный URL (/media, /uploads) резолвится через vite-proxy
      const audioUrl = uploaded.file_path;

      const getDuration = () =>
        new Promise((resolve) => {
          const audio = new Audio(audioUrl);
          const timer = setTimeout(() => resolve(5000), 4000); // 4s timeout fallback
          audio.addEventListener("loadedmetadata", () => {
            clearTimeout(timer);
            resolve(audio.duration * 1000);
          });
          audio.addEventListener("error", () => {
            clearTimeout(timer);
            resolve(5000);
          });
          audio.load();
        });

      const durationMs = await getDuration();

      const finishPush = (dur) => {
        const slotStart = findNextAvailableSlot(track, startTime, dur);
        track.clips.push({
          id: "clip_" + Date.now(),
          name: file.name || "Запись " + new Date().toLocaleTimeString(),
          src: uploaded.file_path,
          start_time: slotStart,
          end_time: slotStart + dur,
          media_offset: 0,
        });

        if (!timeline.visibleTrackIds) timeline.visibleTrackIds = ["main"];
        if (!timeline.visibleTrackIds.includes(trackId)) {
          timeline.visibleTrackIds.push(trackId);
        }

        handleUpdateAudioTimeline(timeline);

        if (!activeFolderData.value.media_files)
          activeFolderData.value.media_files = [];
        activeFolderData.value.media_files.unshift(uploaded);
      };

      finishPush(durationMs);
    }
  } catch (err) {
    console.error("Failed to upload recording", err);
    showToast("Ошибка загрузки записи!");
  }
};

const { isRecording, recordingTrackId, toggleRecording } =
  useAudioRecorder(handleAudioRecorded);

const handleAddSlide = () => {
  showComponentSelectModal.value = true;
};

const handleComponentSelect = async (componentSchema) => {
  if (!activeFolderData.value) return;
  const presentationId = activeFolderData.value.id;

  const endMarkerIndex = activeFolderData.value.slides.findIndex(
    (s) => s.component === "EndMarkerSlide",
  );
  let newStartTime = 0;
  let orderIndex = activeFolderData.value.slides.length;

  if (endMarkerIndex !== -1) {
    const endMarker = activeFolderData.value.slides[endMarkerIndex];
    const lastRealSlide = activeFolderData.value.slides[endMarkerIndex - 1];
    newStartTime = lastRealSlide ? (lastRealSlide.start_time || 0) + 2000 : 0;
    orderIndex =
      endMarker.order_index !== undefined && endMarker.order_index !== null
        ? endMarker.order_index
        : activeFolderData.value.slides.length;

    // Push end marker forward
    endMarker.start_time = Math.max(
      endMarker.start_time || 0,
      newStartTime + 3000,
    );
    endMarker.order_index = orderIndex + 1;

    const endMarkerPayload = {
      slide_id: endMarker.slide_id || `slide_${Date.now()}_end`,
      component: endMarker.component || "EndMarkerSlide",
      start_time: endMarker.start_time,
      title: endMarker.title || "Конец презентации",
      subtitle: endMarker.subtitle || null,
      layout: endMarker.layout || null,
      order_index: endMarker.order_index,
      data: endMarker.data
        ? { payload: endMarker.data.payload || {} }
        : { payload: {} },
      events: endMarker.events || [],
    };
    await updateSlide(endMarker.id, endMarkerPayload);
  } else if (activeFolderData.value.slides.length > 0) {
    const lastSlide =
      activeFolderData.value.slides[activeFolderData.value.slides.length - 1];
    newStartTime = (lastSlide.start_time || 0) + 2000;
  }

  const newSlidePayload = {
    slide_id: `slide-${Date.now()}`,
    title: componentSchema.title || "Новый Слайд",
    subtitle: "",
    start_time: newStartTime,
    component: componentSchema.slug,
    layout: "col",
    order_index: orderIndex,
    data: {
      payload: componentSchema.default_payload || {},
    },
  };

  try {
    const newSlide = await createSlide(presentationId, newSlidePayload);
    showComponentSelectModal.value = false;

    // Refresh to get proper DB IDs and order (напрямую по id — список скоупится)
    const found = await fetchPresentation(Number(currentFolder.value)).catch(() => null);
    if (found) {
      found.slides = found.slides || [];
      // Sort by start_time just to be safe
      found.slides.sort((a, b) => a.start_time - b.start_time);
      activeFolderData.value = found;

      // Open editor for the newly created slide
      const newIdx = found.slides.findIndex((s) => s.id === newSlide.id);
      if (newIdx !== -1) {
        handleEditSlide(newIdx);
      }
    }
  } catch (err) {
    console.error("Failed to create slide", err);
  }
};

const editorModalRef = ref(null);
const isFullscreen = ref(false);

const { currentTime } = useDirector();

const handleBatchMediaSelect = (mediaFiles) => {
  showMediaLibraryModal.value = false;
  aiVoiceTargetTrackId.value = activeAudioTrack.value;
  handleAIVoiceGenerated(mediaFiles);
};

const handleMediaSelect = (url) => {
  if (activeAudioTrack.value) {
    let timeline = activeFolderData.value.audio_timeline;
    if (!timeline || !Array.isArray(timeline.tracks)) {
      timeline = {
        tracks: [
          { id: "main", type: "voiceover", clips: [] },
          { id: "overlay", type: "voiceover", clips: [] },
          { id: "bgm", type: "bgm", clips: [] },
          { id: "sfx", type: "sfx", clips: [] },
        ],
      };
    }

    let track = timeline.tracks.find((t) => t.id === activeAudioTrack.value);
    if (!track) {
      track = { id: activeAudioTrack.value, type: "audio", clips: [] };
      timeline.tracks.push(track);
    }

    const t = currentTime.value || 0;

    const finishPush = (dur) => {
      track.clips.push({
        id: Math.random().toString(36).substr(2, 9),
        name: url.split("/").pop().split("?")[0] || "Audio",
        src: url,
        start_time: t,
        end_time: t + (dur || 5000),
        media_offset: 0,
        volume: 1,
        muted: false,
      });

      handleUpdateAudioTimeline(timeline);
      showMediaLibraryModal.value = false;
      activeAudioTrack.value = null;
    };

    const audio = new Audio(url);
    audio.addEventListener("loadedmetadata", () => {
      finishPush(audio.duration * 1000);
    });
    audio.addEventListener("error", () => {
      finishPush(5000);
    });
  } else if (editorModalRef.value) {
    editorModalRef.value.insertMediaUrl(url);
    showMediaLibraryModal.value = false;
  }
};

const handleMediaUpload = async (uploadedMedia) => {
  await reloadPresentation();
  if (activeAudioTrack.value && uploadedMedia && uploadedMedia.url) {
    handleMediaSelect(uploadedMedia.url);
  }
};

const showSettingsModal = ref(false);
const showAiModal = ref(false);

const handleAiApplied = async () => {
  try {
    await reloadPresentation();
    if (activeFolderData.value?.id) await loadThemeForPresentation(activeFolderData.value.id);
  } catch (e) {
    console.error("AI apply refresh failed:", e);
  }
};

const handleOpenSettings = async () => {
  showSettingsModal.value = true;
  // подтянуть вектор для модалки (переиспользуем editorPreset)
  if (activeFolderData.value?.id) {
    try {
      editorPreset.value = await fetchPresentationStyle(activeFolderData.value.id);
    } catch {
      editorPreset.value = null;
    }
  }
};

const handleSettingsVisibility = async (value) => {
  if (!activeFolderData.value?.id) return;
  try {
    const updated = await updatePresentation(activeFolderData.value.id, {
      visibility: value,
    });
    activeFolderData.value.visibility = updated.visibility;
  } catch (err) {
    console.error("Failed to update visibility:", err);
    showToast(err?.message || "Не удалось изменить доступ");
  }
};

const handleSettingsChessboard = async (value) => {
  if (!activeFolderData.value?.id) return;
  try {
    const updated = await updatePresentation(activeFolderData.value.id, {
      chessboard: !!value,
    });
    activeFolderData.value.chessboard = updated.chessboard;
  } catch (err) {
    console.error("Failed to update chessboard:", err);
  }
};

const handlePaletteChanged = async () => {
  if (!activeFolderData.value?.id) return;
  try {
    await loadThemeForPresentation(activeFolderData.value.id);
  } catch (e) {
    console.error("Failed to reload theme after palette change:", e);
  }
};

const handleSettingsVariant = async (variant) => {
  if (!activeFolderData.value?.id) return;
  try {
    const updated = await updatePresentation(activeFolderData.value.id, {
      variant: variant || null,
    });
    activeFolderData.value.variant = updated.variant;
  } catch (err) {
    console.error("Failed to update variant:", err);
  }
};

const handleSaveSlide = async (payload) => {
  if (!editingSlide.value || !activeFolderData.value) return;
  try {
    const index = activeFolderData.value.slides.findIndex(
      (s) => s.id === editingSlide.value.id,
    );
    if (index === -1) return;

    // Если пользователь ввёл число и сразу нажал Save, live-update мог не успеть отработать (из-за blur).
    // Проверим, есть ли разница между временем в payload и тем, что сейчас локально в памяти.
    const localTime = activeFolderData.value.slides[index].start_time || 0;
    const newTime =
      payload.start_time !== undefined ? payload.start_time : localTime;
    const missingDelta = newTime - localTime;

    // Применяем недостающую дельту ко всем слайдам, начиная с редактируемого
    if (missingDelta !== 0) {
      for (let i = index; i < activeFolderData.value.slides.length; i++) {
        activeFolderData.value.slides[i].start_time =
          (activeFolderData.value.slides[i].start_time || 0) + missingDelta;
      }
    }

    const promises = [];

    for (let i = index; i < activeFolderData.value.slides.length; i++) {
      const s = activeFolderData.value.slides[i];

      const slidePayload =
        i === index
          ? payload
          : {
              slide_id: s.slide_id,
              component: s.component,
              start_time: s.start_time,
              title: s.title || null,
              subtitle: s.subtitle || null,
              layout: s.layout || null,
              order_index: s.order_index,
              data: s.data
                ? { payload: s.data.payload || {} }
                : { payload: {} },
              events: (s.events || []).map((ev) => ({
                time: ev.time,
                action: ev.action || ev.event_type || null,
                event_type: ev.event_type || ev.action || null,
                payload: ev.payload || {},
              })),
            };

      promises.push(updateSlide(s.id, slidePayload));
    }

    const results = await Promise.all(promises);

    // Style-lint warnings (не блокируют): показать в редакторе, модалку не закрывать
    const seen = new Set();
    saveWarnings.value = [];
    for (const r of results) {
      for (const w of r?.warnings || []) {
        const k = `${w.type}|${w.path}|${w.message}`;
        if (!seen.has(k)) {
          seen.add(k);
          saveWarnings.value.push(w);
        }
      }
    }

    originalEditingSlideData.value = null;
    await reloadPresentation();
    if (saveWarnings.value.length === 0) {
      showEditorModal.value = false;
      editingSlide.value = null;
    }
  } catch (err) {
    console.error("Failed to update slide:", err);
    // Бэкенд возвращает детали 422 ({message, errors}) — показываем их в модалке,
    // а не глухой тост: иначе непонятно, какое поле слайда сломано.
    const inner = err?.detail?.detail;
    const rawErrors = Array.isArray(inner)
      ? inner.map((e) => ({
          type: "validation",
          path: Array.isArray(e.loc) ? e.loc.join(".") : "",
          message: e.msg || "",
        }))
      : inner?.errors || [];
    if (rawErrors.length) {
      saveWarnings.value = rawErrors.map((w) => ({
        type: w.type || "validation",
        path: w.path || "",
        message: w.message || "",
      }));
      showToast(inner?.message || `Ошибка валидации (${rawErrors.length})`);
    } else {
      showToast("Не удалось сохранить слайд.");
    }
  }
};

const slideToPayload = (s) => ({
  slide_id: s.slide_id,
  component: s.component,
  start_time: s.start_time,
  title: s.title || null,
  subtitle: s.subtitle || null,
  layout: s.layout || null,
  order_index: s.order_index,
  data: s.data ? { payload: s.data.payload || {} } : { payload: {} },
  events: (s.events || []).map((ev) => ({
    time: ev.time,
    action: ev.action || ev.event_type || null,
    event_type: ev.event_type || ev.action || null,
    payload: ev.payload || {},
  })),
});

const handleRenameSlide = async ({ index, title }) => {
  const s = activeFolderData.value?.slides?.[index];
  if (!s) return;
  try {
    await updateSlide(s.id, { ...slideToPayload(s), title });
    await reloadPresentation();
  } catch (err) {
    console.error("Failed to rename slide:", err);
  }
};

const handleDuplicateSlide = async (index) => {
  const slides = activeFolderData.value?.slides;
  if (!slides?.[index] || !activeFolderData.value) return;
  const src = slides[index];
  if (src.component === "EndMarkerSlide") return;
  try {
    const GAP = 2500;
    const promises = [];
    for (let i = index + 1; i < slides.length; i++) {
      const s = slides[i];
      promises.push(updateSlide(s.id, {
        ...slideToPayload(s),
        start_time: (s.start_time || 0) + GAP,
        order_index: (s.order_index ?? i) + 1,
      }));
    }
    const payload = JSON.parse(JSON.stringify(src.data?.payload || {}));
    const copy = {
      ...slideToPayload(src),
      slide_id: `slide-${Date.now()}`,
      title: src.title ? `${src.title.replace(/<[^>]*>/g, "")} (копия)` : "Копия слайда",
      start_time: (src.start_time || 0) + GAP,
      order_index: (src.order_index ?? index) + 1,
      data: { payload },
    };
    promises.push(createSlide(activeFolderData.value.id, copy));
    await Promise.all(promises);
    await reloadPresentation();
  } catch (err) {
    console.error("Failed to duplicate slide:", err);
  }
};

const handleDeleteSlideIndex = async (index) => {
  const s = activeFolderData.value?.slides?.[index];
  if (!s || !confirm(`Удалить слайд «${(s.title || "").replace(/<[^>]*>/g, "") || s.component}»?`)) return;
  try {
    await deleteSlide(s.id);
    await reloadPresentation();
  } catch (err) {
    console.error("Failed to delete slide:", err);
  }
};

const handleSlideVariant = async ({ index, variant }) => {
  const s = activeFolderData.value?.slides?.[index];
  if (!s) return;
  try {
    const payload = JSON.parse(JSON.stringify(s.data?.payload || {}));
    if (variant) payload.variant = variant;
    else delete payload.variant;
    await updateSlide(s.id, { ...slideToPayload(s), data: { payload } });
    await reloadPresentation();
  } catch (err) {
    console.error("Failed to set slide variant:", err);
  }
};

const handleDeleteSlide = async () => {
  if (!editingSlide.value) return;

  try {
    await deleteSlide(editingSlide.value.id);
    originalEditingSlideData.value = null; // clear so it doesn't revert
    await reloadPresentation();
    showEditorModal.value = false;
    editingSlide.value = null;
  } catch (err) {
    console.error("Failed to delete slide:", err);
    showToast("Не удалось удалить слайд.");
  }
};

const reloadPresentation = async () => {
  try {
    // напрямую по id: список GET /presentations/ скоупится и может не содержать
    // презентацию чужого проекта (публичный просмотр/рендер).
    const found = await fetchPresentation(Number(currentFolder.value)).catch(() => null);
    if (found) {
      found.slides = found.slides || [];
      found.slides.sort((a, b) => (a.start_time || 0) - (b.start_time || 0));
      activeFolderData.value = found;
    }
  } catch (err) {
    console.error("Failed to reload presentations:", err);
  }
};

// AI Voice Generation
const showAIVoiceModal = ref(false);
const aiVoiceTargetTrackId = ref("main");
const aiVoiceInitialData = ref(null);

const handleRequestGenerateVoice = (trackId) => {
  aiVoiceTargetTrackId.value = trackId || "main";
  aiVoiceInitialData.value = null;
  showAIVoiceModal.value = true;
};

const handleEditAIVoice = (file) => {
  aiVoiceTargetTrackId.value = "main"; // default for editing from library
  aiVoiceInitialData.value = {
    text: file.ai_text || "",
    settings: file.ai_settings || null,
  };
  showAIVoiceModal.value = true;
};

const handleEditClip = (payload) => {
  const { trackId, clip } = payload;
  if (clip.type === "ai_voice") {
    aiVoiceTargetTrackId.value = trackId;
    aiVoiceInitialData.value = {
      isEditing: true,
      clipId: clip.id,
      text: clip.ai_settings?.text || clip.name || "",
      settings: clip.ai_settings || {},
      playbackRate: clip.playbackRate || 1.0,
    };
    showAIVoiceModal.value = true;
  }
};

const handleAIVoiceGenerated = async (mediaFiles) => {
  showAIVoiceModal.value = false;
  if (!activeFolderData.value) return;

  const timeline = activeFolderData.value.audio_timeline
    ? JSON.parse(JSON.stringify(activeFolderData.value.audio_timeline))
    : {
        tracks: [
          { id: "main", clips: [] },
          { id: "overlay", clips: [] },
          { id: "bgm", clips: [] },
          { id: "sfx", clips: [] },
        ],
      };

  const track = timeline.tracks.find(
    (t) => t.id === aiVoiceTargetTrackId.value,
  );
  if (track) {
    let playheadTime = currentTime.value || 0;
    const filesArray = Array.isArray(mediaFiles) ? mediaFiles : [mediaFiles];

    for (let i = 0; i < filesArray.length; i++) {
      const mediaFile = filesArray[i];
      const audioUrl = mediaFile.file_path;

      const durationMs = await new Promise((resolve) => {
        const audio = new Audio(audioUrl);
        audio.addEventListener("loadedmetadata", () =>
          resolve(audio.duration * 1000),
        );
        audio.addEventListener("error", () => resolve(5000));
      });

      const slotStart = findNextAvailableSlot(track, playheadTime, durationMs);

      track.clips.push({
        id: `ai_${Date.now()}_${i}`,
        name: mediaFile.filename,
        src: mediaFile.file_path,
        start_time: slotStart,
        end_time: slotStart + durationMs,
        media_offset: 0,
        type: "ai_voice",
        ai_settings: {
          ...(mediaFile.ai_settings || {}),
          text: mediaFile.ai_text,
        },
      });

      playheadTime = slotStart + durationMs + 200; // Advance playhead for next fragment with 200ms gap

      if (!activeFolderData.value.media_files) {
        activeFolderData.value.media_files = [];
      }
      activeFolderData.value.media_files.unshift(mediaFile);
    }

    handleUpdateAudioTimeline(timeline);
  }
};
</script>
