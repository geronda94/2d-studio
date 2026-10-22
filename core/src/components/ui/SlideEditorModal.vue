<template>
  <div
    v-if="isOpen"
    v-show="!isFullscreen"
    class="fixed right-0 top-0 w-[500px] max-w-full h-full bg-bg-base border-l border-gray-200 shadow-2xl z-[200] flex flex-col animate-in slide-in-from-right duration-200"
    :style="{ bottom: isMobile ? '0px' : 'var(--timeline-height, 0px)' }"
  >
    <!-- Header -->
    <div
      class="p-4 border-b border-gray-200 bg-bg-surface flex flex-col gap-3 shrink-0"
    >
      <div class="flex justify-between items-start">
        <div class="flex-1 min-w-0 pr-4">
          <h2 class="text-xl font-bold text-text-primary">Редактирование слайда</h2>
          <p class="text-text-secondary text-[10px] font-mono mt-0.5 break-all">
            ID: {{ editForm.slide_id }}
          </p>
        </div>

        <!-- Global Playback Controls -->
        <div
          class="flex items-center gap-1 bg-gray-50 rounded-lg p-1 border border-gray-200"
        >
          <button
            @click="testComponentPlayback"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-colors font-bold uppercase tracking-wide text-[10px] border"
            :class="
              director.isPlaying.value
                ? 'bg-white border-red-200 text-red-600 hover:bg-red-50'
                : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50'
            "
          >
            <Icon
              :icon="
                director.isPlaying.value ? 'heroicons:stop' : 'heroicons:play'
              "
              class="text-sm"
            />
            {{ director.isPlaying.value ? "Стоп" : "Тест" }}
          </button>
          <div class="w-px h-4 bg-gray-200 mx-1"></div>
          <div class="flex items-center gap-0.5">
            <button
              @click="playbackSpeed = 1"
              class="px-2 py-1 rounded text-[10px] font-bold transition-colors"
              :class="
                playbackSpeed === 1
                  ? 'bg-white text-text-primary shadow-sm'
                  : 'text-text-secondary hover:bg-white'
              "
            >
              x1
            </button>
            <button
              @click="playbackSpeed = 2"
              class="px-2 py-1 rounded text-[10px] font-bold transition-colors"
              :class="
                playbackSpeed === 2
                  ? 'bg-white text-text-primary shadow-sm'
                  : 'text-text-secondary hover:bg-white'
              "
            >
              x2
            </button>
            <button
              @click="playbackSpeed = 3"
              class="px-2 py-1 rounded text-[10px] font-bold transition-colors"
              :class="
                playbackSpeed === 3
                  ? 'bg-white text-text-primary shadow-sm'
                  : 'text-text-secondary hover:bg-white'
              "
            >
              x3
            </button>
            <button
              @click="playbackSpeed = 5"
              class="px-2 py-1 rounded text-[10px] font-bold transition-colors"
              :class="
                playbackSpeed === 5
                  ? 'bg-white text-text-primary shadow-sm'
                  : 'text-text-secondary hover:bg-white'
              "
            >
              x5
            </button>
          </div>
        </div>

        <button
          @click="$emit('close')"
          class="p-2 -mr-2 -mt-2 text-text-secondary hover:text-text-primary transition-colors shrink-0"
        >
          <Icon icon="heroicons:x-mark" class="text-xl" />
        </button>
      </div>

      <div class="flex gap-2">
        <button
          @click="$emit('open-media-library')"
          class="flex-1 px-3 py-1.5 text-sm bg-white hover:bg-gray-50 text-gray-700 font-bold rounded-lg transition-colors flex items-center justify-center gap-2 border border-gray-200"
          title="Медиа-библиотека"
        >
          <Icon icon="heroicons:photo" class="text-base" />
          Media
        </button>
        <button
          @click="handleDeleteClick"
          class="flex-1 px-3 py-1.5 text-sm font-bold rounded-lg transition-colors flex items-center justify-center gap-2 border"
          :class="
            confirmDelete
              ? 'bg-red-600 hover:bg-red-700 text-white border-red-600'
              : 'bg-white hover:bg-red-50 text-red-600 border-gray-200'
          "
        >
          <Icon icon="heroicons:trash" class="text-base" />
          {{ confirmDelete ? "Уверены?" : "Удалить" }}
        </button>
        <button
          @click="handleSave"
          class="flex-1 px-3 py-1.5 text-sm bg-color-primary hover:bg-blue-600 text-white font-bold rounded-lg transition-colors flex items-center justify-center gap-2 shadow-sm"
        >
          <Icon icon="heroicons:check-circle" class="text-base" />
          Save
        </button>
      </div>
    </div>

    <!-- Вектор стилей: только индикатор. Управление — в настройках презентации (⚙),
         чтобы не дублировать пикер в двух местах. -->
    <div
      v-if="presetInfo?.style_preset"
      class="mx-4 mt-3 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-xs text-gray-600 flex items-center gap-2"
      title="Вектор задаётся в настройках презентации (шестерёнка)"
    >
      🧭 {{ presetInfo?.preset?.title || presetInfo?.style_preset }}
      <span v-if="presetInfo?.style_lock" title="Вектор залочен">🔒</span>
    </div>

    <!-- Style-lint warnings (не блокируют сохранение) -->
    <div
      v-if="visibleWarnings.length"
      class="mx-4 mt-3 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900"
    >
      <div class="flex items-center justify-between mb-1.5">
        <p class="font-bold flex items-center gap-1.5">
          <Icon icon="heroicons:exclamation-triangle" class="text-base" />
          Стиль: {{ visibleWarnings.length }}
        </p>
        <button
          @click="dismissedWarnings = true"
          class="text-amber-500 hover:text-amber-800 font-bold px-1"
          title="Скрыть"
        >
          ✕
        </button>
      </div>
      <ul class="space-y-1 max-h-32 overflow-y-auto">
        <li
          v-for="(w, i) in visibleWarnings"
          :key="i"
          class="font-mono text-xs"
        >
          <span class="font-bold">[{{ w.type }}]</span>
          <span class="opacity-70">{{ w.path }} — </span>{{ w.message }}
        </li>
      </ul>
    </div>

    <!-- Scrollable Content -->
    <div class="flex-1 overflow-y-auto p-4 pb-64 space-y-4">
      <!-- Basic Info -->
      <div
        class="bg-gray-50/50 p-4 rounded-lg border border-gray-200 space-y-3"
      >
        <h3 class="text-base font-bold text-gray-700 flex items-center gap-2">
          <Icon icon="heroicons:information-circle" />
          Basic Settings
        </h3>

        <div class="grid grid-cols-1 gap-3">
          <!-- Start Time -->
          <div class="space-y-1 bg-white rounded-lg p-2 border border-gray-200">
            <div class="flex justify-between items-center mb-1">
              <label
                class="text-[10px] text-gray-500 font-bold uppercase tracking-wide flex items-center gap-1.5"
              >
                <Icon
                  icon="heroicons:clock"
                  class="text-color-primary text-sm"
                />
                Старт анимации
              </label>
              <span
                class="text-[10px] text-color-primary font-mono bg-blue-50 px-1.5 py-0.5 rounded-md"
                >{{ editForm.start_time }} ms</span
              >
            </div>
            <TimePicker
              v-model="editForm.start_time"
              :min="minLimit"
              :max="maxLimit"
            />
          </div>

          <div class="space-y-1">
            <label
              class="text-[10px] text-gray-500 font-bold uppercase tracking-wide"
              >Title</label
            >
            <input
              v-model="editForm.title"
              type="text"
              class="w-full bg-white border border-gray-200 rounded-md px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-color-primary transition-colors"
            />
          </div>

          <div class="space-y-1">
            <label
              class="text-[10px] text-gray-500 font-bold uppercase tracking-wide"
              >Subtitle</label
            >
            <input
              v-model="editForm.subtitle"
              type="text"
              class="w-full bg-white border border-gray-200 rounded-md px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-color-primary transition-colors"
            />
          </div>

          <div class="space-y-1">
            <label
              class="text-[10px] text-gray-500 font-bold uppercase tracking-wide"
              >Component</label
            >
            <div
              @click="showComponentSelectModal = true"
              class="w-full bg-white border border-gray-200 rounded-md px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-color-primary transition-colors font-mono cursor-pointer flex justify-between items-center hover:border-gray-300"
            >
              <span>{{ editForm.component || "Select Component..." }}</span>
              <Icon icon="heroicons:chevron-right" class="text-gray-400" />
            </div>
          </div>
        </div>
      </div>

      <!-- Custom MediaSlide Settings -->
      <div
        v-if="
          editForm.component === 'MediaSlide' ||
          editForm.component === 'AdvancedVideoSlide'
        "
        class="bg-gray-50/50 p-4 rounded-lg border border-gray-200 space-y-4 mb-4"
      >
        <h3 class="text-base font-bold text-gray-700 flex items-center gap-2">
          <Icon icon="heroicons:sparkles" />
          Настройки медиа и анимации
        </h3>

        <!-- Presets -->
        <div class="space-y-1.5">
          <div class="flex justify-between items-center mb-2">
            <label
              class="text-[10px] text-text-secondary font-bold uppercase tracking-wide"
              >Мои пресеты медиа</label
            >
            <button
              @click="saveCurrentPreset"
              class="text-[10px] bg-bg-surface hover:bg-color-secondary hover:text-black px-2 py-1 rounded text-text-primary font-bold transition-colors flex items-center gap-1"
              title="Сохранить текущие настройки"
            >
              <Icon icon="heroicons:bookmark" class="text-xs" />
              Сохранить
            </button>
          </div>

          <!-- Custom saved presets -->
          <div
            v-if="savedPresets.length > 0"
            class="flex flex-wrap gap-2 pt-2 mt-2 border-t border-gray-200"
          >
            <div
              v-for="p in savedPresets"
              :key="p.id"
              class="flex items-center bg-bg-surface rounded-md border border-gray-200 group"
            >
              <button
                @click="applySavedPreset(p)"
                class="px-2.5 py-1.5 text-xs text-text-primary hover:text-color-secondary transition-colors truncate max-w-[120px]"
                :title="p.name"
              >
                {{ p.name }}
              </button>
              <button
                @click.stop="deletePreset(p.id)"
                class="p-1.5 text-text-muted hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all border-l border-gray-200"
                title="Удалить"
              >
                <Icon icon="heroicons:x-mark" class="text-xs" />
              </button>
            </div>
          </div>
          <div v-else class="text-xs text-text-muted italic pb-2">
            У вас пока нет сохраненных пресетов.
          </div>
        </div>

        <!-- Pan Visualizer -->
        <div class="space-y-2 pt-3 border-t border-gray-200">
          <div class="flex flex-wrap items-center justify-between gap-2">
            <label
              class="text-[10px] text-text-secondary font-bold uppercase tracking-wide"
            >
              {{
                editForm.component === "AdvancedVideoSlide"
                  ? "Центр зума (Сетка)"
                  : "Траектория панорамирования (Радар)"
              }}
            </label>
            <div
              v-if="editForm.component === 'MediaSlide'"
              class="flex items-center gap-1.5 bg-black/20 p-1 rounded-lg"
            >
              <button
                @click="panMode = 'start'"
                class="px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wide transition-colors"
                :class="
                  panMode === 'start'
                    ? 'bg-color-secondary text-white shadow-md'
                    : 'text-text-secondary hover:bg-bg-surface'
                "
              >
                Старт
              </button>
              <button
                @click="panMode = 'end'"
                class="px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wide transition-colors"
                :class="
                  panMode === 'end'
                    ? 'bg-[#EF4444] text-text-primary shadow-md'
                    : 'text-text-secondary hover:bg-bg-surface'
                "
              >
                Конец
              </button>
              <div class="w-px h-4 bg-bg-hover mx-0.5"></div>
              <button
                @click="resetPan"
                class="p-1 rounded-md text-text-muted hover:text-text-primary hover:bg-bg-surface transition-colors"
                title="Сбросить в центр"
              >
                <Icon
                  icon="heroicons:arrow-path-rounded-square"
                  class="text-sm"
                />
              </button>
            </div>
          </div>

          <div
            class="relative w-full h-40 bg-black/50 border border-gray-200 rounded-lg overflow-hidden flex items-center justify-center mt-2 group hover:border-text-secondary transition-colors"
          >
            <!-- Mini Media Preview -->
            <img
              v-if="mediaPreviewUrl && !mediaPreviewUrl.endsWith('.mp4')"
              :src="mediaPreviewUrl"
              class="absolute inset-0 w-full h-full object-cover opacity-30 pointer-events-none"
              :style="previewStyle"
            />
            <video
              v-else-if="mediaPreviewUrl && mediaPreviewUrl.endsWith('.mp4')"
              :src="mediaPreviewUrl"
              class="absolute inset-0 w-full h-full object-cover opacity-30 pointer-events-none"
              :style="previewStyle"
            ></video>

            <template v-if="editForm.component === 'MediaSlide'">
              <!-- Trajectory Line -->
              <svg
                class="absolute inset-0 w-full h-full pointer-events-none overflow-visible z-10"
                v-if="hasTrajectory && !director.isPlaying.value"
              >
                <line
                  :x1="panX + '%'"
                  :y1="panY + '%'"
                  :x2="panEndX + '%'"
                  :y2="panEndY + '%'"
                  stroke="rgb(var(--text-primary-rgb) / 0.8)"
                  stroke-width="2.5"
                  stroke-dasharray="6 4"
                />
              </svg>

              <!-- Radar SVG Grid -->
              <svg
                viewBox="0 0 100 100"
                preserveAspectRatio="none"
                class="absolute inset-0 w-full h-full z-20"
                v-if="!director.isPlaying.value"
              >
                <defs>
                  <linearGradient
                    id="overlapGradient"
                    x1="0%"
                    y1="0%"
                    x2="100%"
                    y2="100%"
                  >
                    <stop
                      offset="0%"
                      stop-color="rgb(var(--color-secondary-rgb) / 0.8)"
                    />
                    <stop offset="100%" stop-color="rgba(239,68,68,0.8)" />
                  </linearGradient>
                </defs>

                <path
                  v-for="sec in radarSectors"
                  :key="sec.id"
                  :d="sec.d"
                  :fill="getSectorFill(sec)"
                  :stroke="getSectorStroke(sec)"
                  stroke-width="0.5"
                  class="cursor-pointer transition-all duration-150 hover:fill-white/30"
                  @mousedown="selectRadarSector(sec.panX, sec.panY)"
                />
              </svg>
            </template>

            <template v-else-if="editForm.component === 'AdvancedVideoSlide'">
              <!-- Grid Overlay for AdvancedVideoSlide -->
              <div
                class="absolute inset-0 z-20 grid w-full h-full"
                style="
                  grid-template-columns: repeat(5, 1fr);
                  grid-template-rows: repeat(5, 1fr);
                "
              >
                <template v-for="row in 5" :key="'r' + row">
                  <div
                    v-for="col in 5"
                    :key="'c' + col"
                    class="w-full h-full border border-text-secondary hover:bg-bg-surface cursor-pointer transition-colors"
                    :class="
                      (col - 1) * 25 + '% ' + (row - 1) * 25 + '%' ===
                      parsedData.object_position
                        ? 'bg-color-secondary/40 border-color-secondary'
                        : ''
                    "
                    @mousedown="
                      parsedData.object_position =
                        (col - 1) * 25 + '% ' + (row - 1) * 25 + '%'
                    "
                  />
                </template>
              </div>
            </template>
          </div>
        </div>

        <!-- Zoom Settings -->
        <div class="space-y-3 pt-3 border-t border-gray-200">
          <div class="flex flex-col gap-3">
            <!-- Base Scale -->
            <div class="space-y-1">
              <div class="flex justify-between items-center">
                <label
                  class="text-[10px] text-text-secondary font-bold uppercase tracking-wide"
                  >Базовый масштаб картинки</label
                >
                <span
                  class="text-xs font-mono text-color-warning bg-color-warning/10 px-1.5 py-0.5 rounded"
                  >{{ baseScale.toFixed(2) }}</span
                >
              </div>
              <div
                class="flex items-center gap-3 bg-bg-surface px-3 py-2 rounded-md border border-gray-200"
                @wheel.prevent="onWheelBaseScale"
              >
                <div class="relative flex-1 flex items-center h-5">
                  <!-- Ticks for Base Scale: 0.5, 1.0 (neutral), 1.5, 2.0, 2.5, 3.0 -->
                  <div
                    v-for="tick in [0, 20, 40, 60, 80, 100]"
                    :key="'b-' + tick"
                    class="absolute w-0.5 pointer-events-none rounded-full"
                    :class="
                      tick === 20
                        ? 'h-4 bg-color-warning'
                        : 'h-2 bg-color-warning/30'
                    "
                    :style="`left: ${tick}%; top: 50%; transform: translate(-50%, -50%)`"
                  ></div>
                  <input
                    type="range"
                    v-model.number="baseScale"
                    min="0.5"
                    max="3.0"
                    step="0.05"
                    class="w-full accent-color-warning relative z-10 bg-transparent cursor-ew-resize"
                    title="Крутите колесиком мыши для настройки"
                  />
                </div>
              </div>
            </div>

            <!-- Intensity -->
            <div v-if="editForm.component === 'MediaSlide'" class="space-y-1">
              <div class="flex justify-between items-center">
                <label
                  class="text-[10px] text-text-secondary font-bold uppercase tracking-wide"
                  >Анимация: Шаг зума</label
                >
                <span
                  class="text-xs font-mono text-color-secondary bg-color-secondary/10 px-1.5 py-0.5 rounded"
                  >{{ zoomIntensity > 0 ? "+" : ""
                  }}{{ zoomIntensity.toFixed(2) }}</span
                >
              </div>
              <div
                class="flex items-center gap-3 bg-bg-surface px-3 py-2 rounded-md border border-gray-200"
                @wheel.prevent="onWheelZoomIntensity"
              >
                <div class="relative flex-1 flex items-center h-5">
                  <!-- Ticks for Zoom Intensity: -1.5 to 1.5, steps of 0.5 -->
                  <div
                    v-for="tick in [0, 16.66, 33.33, 50, 66.66, 83.33, 100]"
                    :key="'z-' + tick"
                    class="absolute w-0.5 pointer-events-none rounded-full"
                    :class="
                      tick === 50
                        ? 'h-4 bg-color-secondary'
                        : 'h-2 bg-color-secondary/30'
                    "
                    :style="`left: ${tick}%; top: 50%; transform: translate(-50%, -50%)`"
                  ></div>
                  <input
                    type="range"
                    v-model.number="zoomIntensity"
                    min="-1.5"
                    max="1.5"
                    step="0.05"
                    class="w-full accent-color-secondary relative z-10 bg-transparent cursor-ew-resize"
                    title="Крутите колесиком мыши для настройки"
                  />
                </div>
              </div>
            </div>

            <div class="flex gap-4">
              <!-- Duration -->
              <div
                v-if="editForm.component === 'MediaSlide'"
                class="flex-1 space-y-1"
              >
                <label
                  class="text-[10px] text-text-secondary font-bold uppercase tracking-wide"
                  >Длительность зума</label
                >
                <TimePicker
                  :modelValue="Number(parsedData.zoom_duration) || 0"
                  @update:modelValue="parsedData.zoom_duration = $event"
                />
              </div>
              <!-- Start Time (Media) -->
              <div class="flex-1 space-y-1">
                <label
                  class="text-[10px] text-text-secondary font-bold uppercase tracking-wide"
                  >Старт анимации</label
                >
                <TimePicker
                  :modelValue="Number(parsedData.start_time) || 0"
                  @update:modelValue="parsedData.start_time = $event"
                />
              </div>
            </div>

            <div
              v-if="editForm.component === 'AdvancedVideoSlide'"
              class="space-y-4 pt-2"
            >
              <!-- Frame Dropdown -->
              <div class="space-y-1">
                <label
                  class="text-[10px] text-text-secondary font-bold uppercase tracking-wide"
                  >Рамка (Frame)</label
                >
                <div class="relative">
                  <select
                    v-model="parsedData.frame"
                    class="w-full bg-white border border-gray-200 rounded-lg px-3 py-2 text-text-primary text-sm focus:outline-none focus:border-color-secondary cursor-pointer appearance-none"
                  >
                    <option value="browser">Браузер (Mac)</option>
                    <option value="mobile">Смартфон</option>
                    <option value="none">Без рамки</option>
                  </select>
                  <div
                    class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-text-secondary"
                  >
                    <svg
                      class="h-4 w-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M19 9l-7 7-7-7"
                      ></path>
                    </svg>
                  </div>
                </div>
              </div>

              <div class="flex gap-4">
                <!-- Trim Start -->
                <div class="flex-1 space-y-1">
                  <label
                    class="text-[10px] text-text-secondary font-bold uppercase tracking-wide"
                    >Обрезка: Старт</label
                  >
                  <TimePicker
                    :modelValue="(Number(parsedData.trim_start) || 0) * 1000"
                    @update:modelValue="parsedData.trim_start = $event / 1000"
                  />
                </div>
                <!-- Trim End -->
                <div class="flex-1 space-y-1">
                  <label
                    class="text-[10px] text-text-secondary font-bold uppercase tracking-wide"
                    >Обрезка: Конец</label
                  >
                  <TimePicker
                    :modelValue="(Number(parsedData.trim_end) || 0) * 1000"
                    @update:modelValue="
                      parsedData.trim_end =
                        $event === 0 ? undefined : $event / 1000
                    "
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Slide Data (Dynamic UI) -->
      <div
        class="bg-gray-50/50 p-4 rounded-lg border border-gray-200 space-y-4"
      >
        <div
          class="flex items-center justify-between border-b border-gray-200 pb-3"
        >
          <div class="flex gap-1">
            <button
              @click="dataTab = 'data'"
              :class="
                dataTab === 'data'
                  ? 'text-gray-900 border-b-2 border-gray-800 bg-transparent'
                  : 'text-gray-400 hover:text-gray-600 border-b-2 border-transparent'
              "
              class="pb-2 px-1 text-sm font-bold flex items-center gap-1.5 transition-all"
            >
              <Icon icon="heroicons:adjustments-horizontal" class="text-sm" />
              Данные
            </button>
            <button
              @click="
                dataTab = 'sounds';
                ensureItemSfx();
              "
              :class="
                dataTab === 'sounds'
                  ? 'text-gray-900 border-b-2 border-gray-800 bg-transparent'
                  : 'text-gray-400 hover:text-gray-600 border-b-2 border-transparent'
              "
              class="pb-2 px-1 text-sm font-bold flex items-center gap-1.5 transition-all"
            >
              <Icon icon="heroicons:speaker-wave" class="text-sm" />
              Звуки (SFX)
            </button>
          </div>
          <div
            v-if="dataTab === 'data' && appliedFromBrand.length"
            class="mt-2 mb-1 text-[11px] text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2"
          >
            Из бренда проекта подставятся пустые поля: <b>{{ appliedFromBrand.join(', ') }}</b>.
            Заполни поле, чтобы переопределить, или впиши <code>__none__</code>, чтобы не подставлять.
          </div>
          <div
            class="flex bg-gray-100 p-0.5 rounded-lg border border-gray-200"
            v-if="dataTab === 'data'"
          >
            <button
              @click="editorMode = 'ui'"
              :class="
                editorMode === 'ui'
                  ? 'bg-white text-gray-800 shadow-sm'
                  : 'text-gray-400 hover:text-gray-600'
              "
              class="px-3 py-1 rounded-md text-xs font-bold transition-all"
            >
              Интерфейс
            </button>
            <button
              @click="editorMode = 'json'"
              :class="
                editorMode === 'json'
                  ? 'bg-white text-gray-800 shadow-sm'
                  : 'text-gray-400 hover:text-gray-600'
              "
              class="px-3 py-1 rounded-md text-xs font-bold transition-all"
            >
              JSON
            </button>
          </div>
        </div>

        <template v-if="dataTab === 'data'">
          <DynamicJsonEditor
            v-if="editorMode === 'ui'"
            v-model="parsedData"
            :template="activeComponentSchema?.default_payload || {}"
            :schema="activeComponentSchema?.payload_schema?.fields || {}"
            :hiddenKeys="
              ['MediaSlide', 'AdvancedVideoSlide'].includes(editForm.component)
                ? [
                    'initial_scale',
                    'target_scale',
                    'zoom_duration',
                    'object_position',
                    'target_position',
                    'start_time',
                    'trim_start',
                    'trim_end',
                    'frame',
                    'pan_x',
                    'pan_y',
                    'zoom',
                  ]
                : []
            "
            @request-media="handleRequestMedia"
            @request-icon="handleRequestIcon"
            @request-emoji="handleRequestEmoji"
            @request-color="handleRequestColor"
            :slide-duration="currentSlideDuration"
          />
          <div
            v-else
            class="relative h-96 group rounded-lg overflow-hidden border border-gray-200 mt-4"
          >
            <div
              ref="jsonPreRef"
              class="absolute inset-0 bg-white overflow-hidden p-3 pointer-events-none"
            >
              <pre
                class="m-0 font-mono text-[11px] leading-relaxed"
              ><code v-html="highlightedJson"></code></pre>
            </div>
            <textarea
              v-model="rawJsonInput"
              @blur="applyRawJson"
              @scroll="syncScroll"
              class="absolute inset-0 w-full h-full bg-transparent text-transparent caret-gray-800 p-3 font-mono text-[11px] leading-relaxed focus:outline-none border border-transparent resize-none"
              spellcheck="false"
            ></textarea>
            <div
              v-if="jsonError"
              class="absolute bottom-2 right-2 text-red-600 text-xs font-bold bg-red-50 border border-red-200 px-2 py-1 rounded"
            >
              Invalid JSON
            </div>
          </div>
        </template>

        <template v-else-if="dataTab === 'sounds'">
          <div v-if="parsedData.item_sfx" class="space-y-4 pt-2">
            <p class="text-xs text-text-secondary leading-relaxed">
              Этот звук будет автоматически воспроизводиться для каждого айтема
              внутри этого компонента, если у него настроено время анимации.
            </p>

            <!-- SFX Path -->
            <div class="space-y-1">
              <label
                class="text-[10px] text-text-secondary font-bold uppercase tracking-wide"
                >Аудиофайл (SFX)</label
              >
              <div class="flex gap-2">
                <input
                  v-model="parsedData.item_sfx.src"
                  type="text"
                  class="flex-1 bg-white border border-gray-200 rounded-md px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-[#A78BFA] transition-colors"
                  placeholder="/uploads/audio.mp3"
                />
                <button
                  @click="requestSfxMedia"
                  class="px-3 py-2 bg-[#A78BFA]/20 hover:bg-[#A78BFA]/30 text-[#A78BFA] rounded-md transition-colors border border-[#A78BFA]/30 flex items-center gap-2 text-sm font-bold shrink-0"
                >
                  <Icon icon="heroicons:folder-open" />
                  Выбрать
                </button>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-4 pt-4">
              <!-- Time Offset -->
              <div class="space-y-2">
                <div class="flex justify-between items-center">
                  <label
                    class="text-[10px] text-text-secondary font-bold uppercase tracking-wide"
                    >Смещение тайминга</label
                  >
                  <span
                    class="text-[10px] text-[#A78BFA] font-mono bg-[#A78BFA]/10 px-1.5 py-0.5 rounded-md"
                    >{{ parsedData.item_sfx?.time_offset || 0 }} ms</span
                  >
                </div>
                <input
                  type="range"
                  v-model.number="parsedData.item_sfx.time_offset"
                  min="-2000"
                  max="2000"
                  step="50"
                  class="w-full accent-[#A78BFA]"
                />
                <div
                  class="flex justify-between text-[9px] text-text-muted font-mono"
                >
                  <span>-2000ms</span>
                  <span>0</span>
                  <span>+2000ms</span>
                </div>
              </div>

              <!-- Volume -->
              <div class="space-y-2">
                <div class="flex justify-between items-center">
                  <label
                    class="text-[10px] text-text-secondary font-bold uppercase tracking-wide"
                    >Громкость</label
                  >
                  <span
                    class="text-[10px] text-[#A78BFA] font-mono bg-[#A78BFA]/10 px-1.5 py-0.5 rounded-md"
                    >{{ sfxVolumePercent }} %</span
                  >
                </div>
                <input
                  type="range"
                  v-model.number="sfxVolumePercent"
                  min="0"
                  max="150"
                  step="1"
                  class="w-full accent-[#A78BFA]"
                />
                <div
                  class="flex justify-between text-[9px] text-text-muted font-mono"
                >
                  <span>0%</span>
                  <span>100%</span>
                  <span>150%</span>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- Component Library Modal (Nested for Edit Mode) -->
    <ComponentSelectModal
      :isOpen="showComponentSelectModal"
      @close="showComponentSelectModal = false"
      @select="handleComponentChange"
    />

    <!-- Icon Picker Modal -->
    <IconPickerModal
      :isOpen="showIconPickerModal"
      @close="showIconPickerModal = false"
      @select="insertIconString"
    />

    <!-- Emoji Picker Modal -->
    <EmojiPickerModal
      :isOpen="showEmojiPickerModal"
      @close="showEmojiPickerModal = false"
      @select="insertEmojiString"
    />

    <!-- Color Library Modal -->
    <ColorLibraryModal
      :show="showColorLibraryModal"
      :presentation-id="props.slide?.presentation_id || null"
      @close="showColorLibraryModal = false"
      @select="insertColorString"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, inject } from "vue";
import { Icon } from "@iconify/vue";
import { fetchComponents } from "../../services/api";
import ComponentSelectModal from "./ComponentSelectModal.vue";
import DynamicJsonEditor from "./DynamicJsonEditor.vue";
import IconPickerModal from "./IconPickerModal.vue";
import EmojiPickerModal from "./EmojiPickerModal.vue";
import ColorLibraryModal from "./ColorLibraryModal.vue";
import TimePicker from "./TimePicker.vue";
import { useDirector } from "../../composables/useDirector";
import { useMobile } from "../../composables/useMobile";

const { isMobile } = useMobile();

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false,
  },
  isFullscreen: {
    type: Boolean,
    default: false,
  },
  slide: Object,
  previousSlide: Object,
  nextSlide: Object,
  saveWarnings: {
    type: Array,
    default: () => [],
  },
  presetInfo: {
    type: Object,
    default: null,
  },
  // BRAND KIT: дефолты проекта для этого компонента — показываем, что подставится
  // из бренда, если поле слайда пустое (редактор читает сырой payload).
  projectDefaults: {
    type: Object,
    default: () => ({}),
  },
});

const emit = defineEmits([
  "close",
  "save",
  "delete",
  "open-media-library",
  "live-update",
  "update-style",
]);

const confirmDelete = ref(false);
let deleteTimeout = null;

// Style-lint warnings с последнего save (не блокируют, dismissible)
const dismissedWarnings = ref(false);
const visibleWarnings = computed(() =>
  !dismissedWarnings.value && (props.saveWarnings || []).length
    ? props.saveWarnings
    : [],
);
watch(
  () => props.isOpen,
  () => {
    dismissedWarnings.value = false;
  },
);

const handleDeleteClick = () => {
  if (confirmDelete.value) {
    emit("delete");
    confirmDelete.value = false;
    clearTimeout(deleteTimeout);
  } else {
    confirmDelete.value = true;
    deleteTimeout = setTimeout(() => {
      confirmDelete.value = false;
    }, 3000);
  }
};
const availableComponents = ref([]);
const dbComponentSchemas = ref([]);

const showComponentSelectModal = ref(false);

// Close on escape key, but only if nested modals aren't open
const handleKeydown = (e) => {
  if (props.isOpen && e.key === "Escape") {
    if (showComponentSelectModal.value || showIconPickerModal.value) return; // Let the nested modal close itself
    emit("close");
  }
};

const closeAllNestedEditorPanels = () => {
  showComponentSelectModal.value = false;
  showIconPickerModal.value = false;
  showEmojiPickerModal.value = false;
  showColorLibraryModal.value = false;
};

onMounted(async () => {
  window.addEventListener("keydown", handleKeydown);
  window.addEventListener(
    "presentation:close-all-modals",
    closeAllNestedEditorPanels,
  );
  loadPresets();
  try {
    const schemas = await fetchComponents();
    dbComponentSchemas.value = schemas;
    availableComponents.value = schemas.map((s) => s.slug);
  } catch (err) {
    console.error("Failed to load components:", err);
  }
});

onUnmounted(() => {
  window.removeEventListener("keydown", handleKeydown);
  window.removeEventListener(
    "presentation:close-all-modals",
    closeAllNestedEditorPanels,
  );
});

const editForm = ref({
  slide_id: "",
  title: "",
  subtitle: "",
  start_time: 0,
  component: "",
  layout: "default",
  order_index: 0,
});

const MIN_DISTANCE_MS = 2000;

const minLimit = computed(() => {
  if (props.previousSlide) {
    return (
      (props.previousSlide.start_time || props.previousSlide.startTime || 0) +
      MIN_DISTANCE_MS
    );
  }
  return 0;
});

const maxLimit = computed(() => {
  return 9999999;
});

const handleComponentChange = (comp) => {
  editForm.value.component = comp.slug;
  showComponentSelectModal.value = false;

  if (
    confirm(
      `Заменить текущие данные на стандартный шаблон компонента "${comp.title}"?`,
    )
  ) {
    parsedData.value = JSON.parse(JSON.stringify(comp.default_payload || {}));
  }
};

const parsedData = ref({});

// --- MediaSlide Custom Controls Logic ---
const baseScale = computed({
  get: () => {
    const s = Number(parsedData.value.initial_scale);
    return isNaN(s) ? 1.0 : s;
  },
  set: (val) => {
    const diff = zoomIntensity.value;
    parsedData.value.initial_scale = val;
    parsedData.value.target_scale = Number((val + diff).toFixed(2));
  },
});

const zoomIntensity = computed({
  get: () => {
    const i = Number(parsedData.value.initial_scale) || 1.0;
    const t = Number(parsedData.value.target_scale) || 1.0;
    return Number((t - i).toFixed(2));
  },
  set: (val) => {
    const i = Number(parsedData.value.initial_scale) || 1.0;
    parsedData.value.target_scale = Number((i + Number(val)).toFixed(2));
  },
});

const panX = computed({
  get: () => {
    const match = (parsedData.value.object_position || "50% 50%").match(
      /(-?\d+(\.\d+)?)%/,
    );
    return match ? Number(match[1]) : 50;
  },
  set: (val) => {
    const py = panY.value;
    parsedData.value.object_position = `${val}% ${py}%`;
  },
});

const panY = computed({
  get: () => {
    const match = (parsedData.value.object_position || "50% 50%").match(
      /%\s*(-?\d+(\.\d+)?)%/,
    );
    return match ? Number(match[1]) : 50;
  },
  set: (val) => {
    const px = panX.value;
    parsedData.value.object_position = `${px}% ${val}%`;
  },
});

const panEndX = computed({
  get: () => {
    const match = (
      parsedData.value.target_position ||
      parsedData.value.object_position ||
      "50% 50%"
    ).match(/(-?\d+(\.\d+)?)%/);
    return match ? Number(match[1]) : 50;
  },
  set: (val) => {
    const py = panEndY.value;
    parsedData.value.target_position = `${val}% ${py}%`;
  },
});

const panEndY = computed({
  get: () => {
    const match = (
      parsedData.value.target_position ||
      parsedData.value.object_position ||
      "50% 50%"
    ).match(/%\s*(-?\d+(\.\d+)?)%/);
    return match ? Number(match[1]) : 50;
  },
  set: (val) => {
    const px = panEndX.value;
    parsedData.value.target_position = `${px}% ${val}%`;
  },
});

const panMode = ref("start");
const hasTrajectory = computed(
  () =>
    !!parsedData.value.target_position &&
    parsedData.value.target_position !== parsedData.value.object_position,
);

const activePanX = computed({
  get: () => (panMode.value === "start" ? panX.value : panEndX.value),
  set: (val) => {
    if (panMode.value === "start") panX.value = val;
    else panEndX.value = val;
  },
});

const activePanY = computed({
  get: () => (panMode.value === "start" ? panY.value : panEndY.value),
  set: (val) => {
    if (panMode.value === "start") panY.value = val;
    else panEndY.value = val;
  },
});

const resetPan = () => {
  parsedData.value.object_position = "50% 50%";
  parsedData.value.target_position = "50% 50%";
  panMode.value = "start";
};

const radarSectors = computed(() => {
  const sectors = [];
  const cx = 50,
    cy = 50;

  // Center
  sectors.push({
    id: "center",
    d: `M 50 50 m -7, 0 a 7,7 0 1,1 14,0 a 7,7 0 1,1 -14,0`,
    panX: 50,
    panY: 50,
  });

  const getPoint = (angleDeg, r) => {
    const rad = ((angleDeg - 90) * Math.PI) / 180;
    return {
      x: cx + r * Math.cos(rad),
      y: cy + r * Math.sin(rad),
    };
  };

  const createRing = (rIn, rOut, levelName, panMultiplier) => {
    for (let i = 0; i < 8; i++) {
      const startAngle = i * 45 - 22.5;
      const endAngle = startAngle + 45;

      const p1 = getPoint(startAngle, rIn);
      const p2 = getPoint(startAngle, rOut);
      const p3 = getPoint(endAngle, rOut);
      const p4 = getPoint(endAngle, rIn);

      const largeArc = 0;
      const d = `M ${p1.x} ${p1.y} L ${p2.x} ${p2.y} A ${rOut} ${rOut} 0 ${largeArc} 1 ${p3.x} ${p3.y} L ${p4.x} ${p4.y} A ${rIn} ${rIn} 0 ${largeArc} 0 ${p1.x} ${p1.y} Z`;

      let dx = 0,
        dy = 0;
      if (i === 0) {
        dx = 0;
        dy = -1;
      } else if (i === 1) {
        dx = 1;
        dy = -1;
      } else if (i === 2) {
        dx = 1;
        dy = 0;
      } else if (i === 3) {
        dx = 1;
        dy = 1;
      } else if (i === 4) {
        dx = 0;
        dy = 1;
      } else if (i === 5) {
        dx = -1;
        dy = 1;
      } else if (i === 6) {
        dx = -1;
        dy = 0;
      } else if (i === 7) {
        dx = -1;
        dy = -1;
      }

      sectors.push({
        id: `${levelName}-${i}`,
        d,
        panX: 50 + dx * panMultiplier,
        panY: 50 + dy * panMultiplier,
      });
    }
  };

  createRing(8, 17, "level1", 12.5);
  createRing(19, 28, "level2", 25);
  createRing(30, 39, "level3", 37.5);
  createRing(41, 50, "level4", 50);

  return sectors;
});

const selectRadarSector = (px, py) => {
  if (panMode.value === "start") {
    parsedData.value.object_position = `${px}% ${py}%`;
  } else {
    parsedData.value.target_position = `${px}% ${py}%`;
  }
};

const getSectorFill = (sec) => {
  const isStart =
    Math.abs(panX.value - sec.panX) < 0.1 &&
    Math.abs(panY.value - sec.panY) < 0.1;
  const isEnd =
    Math.abs(panEndX.value - sec.panX) < 0.1 &&
    Math.abs(panEndY.value - sec.panY) < 0.1;

  if (isStart && isEnd) return "url(#overlapGradient)";
  if (isStart) return "rgb(var(--color-secondary-rgb) / 0.7)";
  if (isEnd) return "rgba(239,68,68,0.7)";
  return "rgba(0,0,0,0.5)";
};

const getSectorStroke = (sec) => {
  const isStart =
    Math.abs(panX.value - sec.panX) < 0.1 &&
    Math.abs(panY.value - sec.panY) < 0.1;
  const isEnd =
    Math.abs(panEndX.value - sec.panX) < 0.1 &&
    Math.abs(panEndY.value - sec.panY) < 0.1;

  if (isStart || isEnd) return "rgb(var(--text-primary-rgb) / 0.8)";
  return "rgb(var(--text-primary-rgb) / 0.1)";
};

const onWheelBaseScale = (e) => {
  const step = 0.05;
  if (e.deltaY < 0) {
    baseScale.value = Math.min(3.0, baseScale.value + step);
  } else {
    baseScale.value = Math.max(0.5, baseScale.value - step);
  }
};

const onWheelZoomIntensity = (e) => {
  const step = 0.05;
  if (e.deltaY < 0) {
    zoomIntensity.value = Math.min(1.5, zoomIntensity.value + step);
  } else {
    zoomIntensity.value = Math.max(-1.5, zoomIntensity.value - step);
  }
};

const panArea = ref(null);
const mediaPreviewUrl = computed(
  () =>
    parsedData.value.media_url ||
    parsedData.value.MEDIA_URL ||
    parsedData.value.image ||
    parsedData.value.video ||
    parsedData.value.video_url ||
    "",
);

// --- Saved Presets Logic ---
const savedPresets = ref([]);

const loadPresets = () => {
  try {
    const p = localStorage.getItem("mediaSlideCustomPresets");
    if (p) savedPresets.value = JSON.parse(p);
  } catch (e) {}
};

const saveCurrentPreset = () => {
  const defaultName = "Пресет " + (savedPresets.value.length + 1);
  const presetName = prompt(
    "Введите название для вашего пресета:",
    defaultName,
  );

  if (!presetName) return; // User cancelled or entered empty string

  const newPreset = {
    id: Date.now(),
    name: presetName.trim(),
    data: {
      initial_scale: parsedData.value.initial_scale,
      target_scale: parsedData.value.target_scale,
      zoom_duration: parsedData.value.zoom_duration,
      object_position: parsedData.value.object_position,
      target_position: parsedData.value.target_position,
    },
  };
  savedPresets.value.push(newPreset);
  localStorage.setItem(
    "mediaSlideCustomPresets",
    JSON.stringify(savedPresets.value),
  );
};

const deletePreset = (id) => {
  savedPresets.value = savedPresets.value.filter((p) => p.id !== id);
  localStorage.setItem(
    "mediaSlideCustomPresets",
    JSON.stringify(savedPresets.value),
  );
};

const applySavedPreset = (p) => {
  if (p.data.initial_scale !== undefined)
    parsedData.value.initial_scale = p.data.initial_scale;
  if (p.data.target_scale !== undefined)
    parsedData.value.target_scale = p.data.target_scale;
  if (p.data.zoom_duration !== undefined)
    parsedData.value.zoom_duration = p.data.zoom_duration;
  if (p.data.object_position !== undefined)
    parsedData.value.object_position = p.data.object_position;
  if (p.data.target_position !== undefined)
    parsedData.value.target_position = p.data.target_position;
};

// --- Preview Animation Logic ---
const currentSlideStartTime = computed(() => {
  return props.slide?.start_time ?? props.slide?.startTime ?? 0;
});

const currentSlideDuration = computed(() => {
  const slideStart = Number(currentSlideStartTime.value) || 0;
  if (props.nextSlide) {
    const nextStart = Number(
      props.nextSlide.start_time ?? props.nextSlide.startTime,
    );
    if (!isNaN(nextStart) && nextStart > slideStart) {
      return nextStart - slideStart;
    }
  }
  return 15000;
});

const director = useDirector();
const playbackSpeed = ref(1);

const testComponentPlayback = () => {
  if (director.isPlaying.value) {
    director.pause();
    return;
  }

  const slideStart = currentSlideStartTime.value;
  let playUntil = slideStart + 15000; // default fallback if no next slide

  if (props.nextSlide) {
    playUntil =
      (props.nextSlide.start_time ??
        props.nextSlide.startTime ??
        slideStart + 15000) - 1;
  }

  // Seek slightly before the slide starts so it mounts cleanly
  director.seek(Math.max(0, slideStart - 50));
  director.playbackRate.value = playbackSpeed.value;

  // Play until the start of the next slide
  director.play(playUntil);
};

const previewStyle = computed(() => {
  const initialS = parseFloat(parsedData.value.initial_scale) || 1.0;
  const targetS = parseFloat(parsedData.value.target_scale) || 1.0;

  const initialP = parsedData.value.object_position || "50% 50%";
  const targetP = parsedData.value.target_position || initialP;

  const dur = parseInt(parsedData.value.zoom_duration) || 8000;
  const isPlaying = director.isPlaying.value;

  return {
    transform: `scale(${isPlaying ? targetS : initialS})`,
    objectPosition: isPlaying ? targetP : initialP,
    transitionProperty: "transform, object-position",
    transitionTimingFunction: "cubic-bezier(0.25, 1, 0.5, 1)",
    transitionDuration: isPlaying ? `${dur}ms` : "0ms",
  };
});

// ----------------------------------------

const lastFocused = ref(null);

const showIconPickerModal = ref(false);
const showEmojiPickerModal = ref(false);
const targetEmojiKeyPath = ref("");

const handleRequestEmoji = (payload) => {
  targetEmojiKeyPath.value = payload.keyPath;
  showEmojiPickerModal.value = true;
};

const insertEmojiString = (emojiStr) => {
  if (targetEmojiKeyPath.value) {
    const path = targetEmojiKeyPath.value
      .replace(/\[(\w+)\]/g, ".$1")
      .replace(/^\./, "")
      .split(".");
    let current = parsedData.value;
    for (let i = 0; i < path.length - 1; i++) {
      current = current[path[i]];
    }
    const lastPart = path[path.length - 1];
    current[lastPart] = (current[lastPart] || "") + emojiStr;

    parsedData.value = { ...parsedData.value };
  }
  showEmojiPickerModal.value = false;
};

const handleRequestMedia = (payload) => {
  lastFocused.value = { type: "dynamic", keyPath: payload.keyPath };
  emit("open-media-library");
};

const handleRequestIcon = (payload) => {
  lastFocused.value = { type: "dynamic", keyPath: payload.keyPath };
  showIconPickerModal.value = true;
};

const showColorLibraryModal = ref(false);

const dataTab = ref("data"); // 'data' | 'sounds'
const editorMode = ref("ui");
const rawJsonInput = ref("");

const ensureItemSfx = () => {
  if (!parsedData.value) parsedData.value = {};
  if (!parsedData.value.item_sfx) {
    parsedData.value.item_sfx = { src: "", time_offset: 0, volume: 0.3 };
  }
};

watch(
  () => dataTab.value,
  (newTab) => {
    if (newTab === "sounds") ensureItemSfx();
  },
);

watch(
  () => parsedData.value,
  () => {
    if (dataTab.value === "sounds") ensureItemSfx();
  },
  { deep: true },
);

const requestSfxMedia = () => {
  lastFocused.value = { type: "dynamic", keyPath: "item_sfx.src" };
  emit("open-media-library");
};

const sfxVolumePercent = computed({
  get: () => Math.round((parsedData.value?.item_sfx?.volume ?? 1) * 100),
  set: (val) => {
    if (parsedData.value?.item_sfx) {
      parsedData.value.item_sfx.volume = val / 100;
    }
  },
});
const jsonError = ref(false);
const jsonPreRef = ref(null);

const syncScroll = (e) => {
  if (jsonPreRef.value) {
    jsonPreRef.value.scrollTop = e.target.scrollTop;
    jsonPreRef.value.scrollLeft = e.target.scrollLeft;
  }
};

watch(
  () => editorMode.value,
  (newMode) => {
    if (newMode === "json") {
      rawJsonInput.value = JSON.stringify(parsedData.value, null, 2);
      jsonError.value = false;
    } else {
      applyRawJson();
    }
  },
);

const applyRawJson = () => {
  if (editorMode.value !== "json") return;
  try {
    const parsed = JSON.parse(rawJsonInput.value);
    parsedData.value = parsed;
    jsonError.value = false;
  } catch (e) {
    jsonError.value = true;
  }
};

const highlightedJson = computed(() => {
  if (!rawJsonInput.value) return "";
  let html = rawJsonInput.value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  return html.replace(
    /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
    function (match) {
      let cls = "text-green-400"; // string
      if (/^"/.test(match)) {
        if (/:$/.test(match)) cls = "text-color-secondary"; // key
      } else if (/true|false/.test(match)) {
        cls = "text-purple-400"; // boolean
      } else if (/null/.test(match)) {
        cls = "text-gray-400"; // null
      } else {
        cls = "text-amber-400"; // number
      }
      return '<span class="' + cls + '">' + match + "</span>";
    },
  );
});

const handleRequestColor = (payload) => {
  lastFocused.value = { type: "dynamic", keyPath: payload.keyPath };
  showColorLibraryModal.value = true;
};

const insertColorString = (colorHex) => {
  if (lastFocused.value && lastFocused.value.type === "dynamic") {
    const path = lastFocused.value.keyPath
      .replace(/\[(\w+)\]/g, ".$1")
      .replace(/^\./, "")
      .split(".");
    let current = parsedData.value;
    for (let i = 0; i < path.length - 1; i++) {
      current = current[path[i]];
    }
    const lastPart = path[path.length - 1];
    current[lastPart] = colorHex;

    parsedData.value = { ...parsedData.value };
  }
  showColorLibraryModal.value = false;
};

const insertMediaUrl = (url) => {
  if (lastFocused.value && lastFocused.value.type === "dynamic") {
    const path = lastFocused.value.keyPath
      .replace(/\[(\w+)\]/g, ".$1")
      .replace(/^\./, "")
      .split(".");
    let current = parsedData.value;
    for (let i = 0; i < path.length - 1; i++) {
      current = current[path[i]];
    }
    current[path[path.length - 1]] = url;

    parsedData.value = { ...parsedData.value };
  }
};

const insertIconString = (iconCode) => {
  if (lastFocused.value && lastFocused.value.type === "dynamic") {
    const path = lastFocused.value.keyPath
      .replace(/\[(\w+)\]/g, ".$1")
      .replace(/^\./, "")
      .split(".");
    let current = parsedData.value;
    for (let i = 0; i < path.length - 1; i++) {
      current = current[path[i]];
    }
    current[path[path.length - 1]] = iconCode;

    parsedData.value = { ...parsedData.value };
  }
};

defineExpose({
  insertMediaUrl,
  syncData: (newData) => {
    isInitializing = true;
    parsedData.value = JSON.parse(JSON.stringify(newData));
    setTimeout(() => {
      isInitializing = false;
    }, 50);
  },
});

let isInitializing = false;

const buildLivePayload = () => {
  return {
    ...editForm.value,
    data: {
      payload: parsedData.value,
    },
    events: [],
  };
};

watch(
  () => props.slide,
  (newVal) => {
    if (newVal) {
      isInitializing = true;
      editForm.value = {
        slide_id: newVal.slide_id,
        title: newVal.title || "",
        subtitle: newVal.subtitle || "",
        start_time: newVal.start_time || 0,
        component: newVal.component || "OutroSlide",
        layout: newVal.layout || "default",
        order_index: newVal.order_index || 0,
      };

      // Parse data safely
      let dataObj = {};
      if (newVal.data && newVal.data.payload) {
        dataObj = newVal.data.payload;
      } else if (newVal.data) {
        dataObj = newVal.data; // fallback
      }
      parsedData.value = JSON.parse(JSON.stringify(dataObj));

      setTimeout(() => {
        isInitializing = false;
      }, 50);
    }
  },
  { immediate: true },
);

watch(
  () => props.slide?.start_time,
  (newTime) => {
    if (newTime !== undefined && newTime !== editForm.value.start_time) {
      editForm.value.start_time = newTime;
    }
  },
);

watch(
  [editForm, parsedData],
  () => {
    if (props.isOpen && !isInitializing) {
      emit("live-update", buildLivePayload());
    }
  },
  { deep: true },
);

// BRAND KIT: какие поля слайда пусты и будут взяты из бренда проекта.
const appliedFromBrand = computed(() => {
  const defs = props.projectDefaults || {};
  return Object.keys(defs).filter((k) => {
    const v = parsedData.value?.[k];
    return v === undefined || v === null || v === "";
  });
});

const activeComponentSchema = computed(() => {
  if (!editForm.value.component || !dbComponentSchemas.value.length)
    return null;
  return dbComponentSchemas.value.find(
    (c) => c.slug === editForm.value.component,
  );
});

const handleSave = () => {
  // Validate timing
  if (
    props.previousSlide &&
    editForm.value.start_time < props.previousSlide.start_time
  ) {
    alert(
      `Время начала не может быть меньше времени предыдущего слайда (${props.previousSlide.start_time} ms)`,
    );
    return;
  }

  const payload = buildLivePayload();

  emit("save", payload);
};
</script>
