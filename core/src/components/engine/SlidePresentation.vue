<template>
  <div
    class="flex viewport-w viewport-h bg-bg-base overflow-hidden relative touch-manipulation overscroll-none"
    :data-render="isRenderMode ? '1' : null"
    :style="{ paddingBottom: isMobile ? '0px' : 'var(--timeline-height, 0px)' }"
  >
    <!-- Прозрачный слой: клик по канвасу/любому месту вне панели сразу закрывает nav -->
    <div
      v-if="isMobile && navOpen"
      class="absolute inset-0 z-[95]"
      @click="isSidebarOpen = false"
      @touchstart.passive="isSidebarOpen = false"
    ></div>

    <!-- Navigation Sidebar: desktop — в потоке; mobile — полупрозрачный оверлей слева
         (канвас не сжимает), нижняя граница = верх таймлайна. -->
    <div
      class="nav-drawer border-r border-text-muted flex flex-col overflow-y-auto shrink-0 z-[100] transition-all duration-300 overflow-x-hidden hide-scrollbar"
      :class="[
        isMobile
          ? [
              'absolute top-0 left-0 w-[62vw] max-w-[250px] shadow-2xl bg-bg-surface/80 backdrop-blur-xl',
              navOpen ? 'translate-x-0' : '-translate-x-full pointer-events-none invisible',
            ]
          : [navOpen ? 'w-52 bg-bg-surface' : 'w-0 border-r-0'],
      ]"
      :style="isMobile ? { bottom: 'var(--timeline-height, 0px)' } : {}"
      :aria-hidden="!navOpen"
    >
      <div
        class="nav-head p-3 pt-[max(0.75rem,env(safe-area-inset-top))] border-b border-text-muted flex justify-between items-center sticky top-0 bg-bg-surface z-10 shrink-0"
      >
        <span
          class="text-text-secondary text-xs font-bold uppercase tracking-wider ml-1"
          >Слайды</span
        >
        <div class="flex gap-1">
          <button
            @click="isSidebarOpen = false; $emit('open-settings')"
            class="text-text-secondary hover:text-text-primary p-1.5 rounded hover:bg-bg-surface transition-colors"
            title="Настройки презентации (Аудио, Тема)"
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
              <circle cx="12" cy="12" r="3"></circle>
              <path
                d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"
              ></path>
            </svg>
          </button>
          <button
            @click="isSidebarOpen = false"
            class="text-text-secondary hover:text-text-primary p-1.5 rounded hover:bg-bg-surface transition-colors"
            title="Закрыть панель"
          >
            <svg
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
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
      </div>
      <div class="p-2 flex flex-col gap-2">
        <template v-for="(slide, index) in slidesData" :key="slide.id || index">
          <div
            v-if="slide.component !== 'EndMarkerSlide'"
            :ref="
              (el) => {
                if (el) sidebarItems[index] = el;
              }
            "
            @click="goTo(index)"
            @contextmenu.prevent="openSlideMenu(index, $event)"
            class="cursor-pointer group h-14 w-full"
          >
            <div
              class="nav-row w-full h-full rounded border transition-all duration-300 flex flex-row items-center p-2 shadow-lg relative gap-3"
              :class="
                currentSlide === index
                  ? 'border-brand-blue bg-brand-blue/10 text-brand-blue scale-[1.02]'
                  : 'border-text-muted bg-bg-surface text-text-muted group-hover:border-text-secondary group-hover:bg-bg-surface'
              "
              :title="thumbnails[index] || `Слайд ${index + 1}`"
            >
              <!-- Slide Number and Time -->
              <div
                class="flex flex-col items-center justify-center min-w-[28px] shrink-0"
              >
                <div
                  class="text-lg font-bold font-mono opacity-80 leading-none"
                >
                  {{ index + 1 }}
                </div>
                <div
                  v-if="
                    slide.start_time !== undefined ||
                    slide.startTime !== undefined
                  "
                  class="text-[8px] mt-1 font-mono flex items-center gap-0.5 opacity-70"
                  :class="
                    currentSlide === index
                      ? 'text-brand-light-blue'
                      : 'text-text-secondary'
                  "
                >
                  {{ formatTimeSimple(slide.start_time ?? slide.startTime) }}
                </div>
              </div>

              <!-- Slide Title (Truncated / rename inline) -->
              <div class="flex-1 min-w-0 flex flex-col justify-center">
                <input
                  v-if="renamingIndex === index"
                  v-model="renameText"
                  @click.stop
                  @keyup.enter="commitRename"
                  @keyup.esc="renamingIndex = null"
                  @blur="commitRename"
                  :ref="(el) => { if (el && renamingIndex === index) el.focus() }"
                  class="text-xs font-medium bg-bg-base border border-brand-blue rounded px-1 py-0.5 text-text-primary focus:outline-none w-full"
                />
                <div
                  v-else
                  class="text-xs font-medium truncate opacity-90 group-hover:opacity-100"
                  :class="
                    currentSlide === index
                      ? 'text-brand-light-blue'
                      : 'text-text-secondary'
                  "
                >
                  {{
                    thumbnails[index]
                      ? thumbnails[index].replace(/<[^>]*>?/gm, "")
                      : "Без названия"
                  }}
                </div>
                <div
                  class="text-[9px] truncate opacity-50 font-mono mt-0.5"
                  :title="slide.component"
                >
                  {{ slide.component }}
                </div>
              </div>
            </div>
          </div>
        </template>
        <!-- Add Slide Button -->
        <button
          @click="$emit('add-slide')"
          class="w-full h-12 flex flex-row items-center justify-center gap-2 bg-brand-green/10 hover:bg-brand-green/20 text-brand-green rounded-lg transition-colors border border-brand-green/30 font-bold group mt-1"
          title="Add Slide"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="group-hover:rotate-90 transition-transform"
          >
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          <span class="text-sm">Новый слайд</span>
        </button>
        <template
          v-for="(slide, index) in slidesData"
          :key="'end' + (slide.id || index)"
        >
          <div
            v-if="slide.component === 'EndMarkerSlide'"
            v-show="isEditorOpen"
            :ref="
              (el) => {
                if (el) sidebarItems[index] = el;
              }
            "
            @click="goTo(index)"
            class="cursor-pointer group h-14 w-full mt-4"
          >
            <div
              class="nav-row w-full h-full rounded border transition-all duration-300 flex flex-row items-center p-2 shadow-lg relative gap-3"
              :class="
                currentSlide === index
                  ? 'border-red-500 bg-red-500/20 text-red-400 scale-[1.02]'
                  : 'border-red-500/20 bg-red-500/5 text-red-500/70 group-hover:border-red-500/50 group-hover:bg-red-500/10'
              "
            >
              <div
                class="flex flex-col items-center justify-center min-w-[28px] shrink-0"
              >
                <span class="text-xl opacity-80">🏁</span>
              </div>
              <div class="flex-1 min-w-0 flex flex-col justify-center">
                <div
                  class="text-xs font-bold truncate opacity-90 group-hover:opacity-100"
                  :class="
                    currentSlide === index
                      ? 'text-red-400'
                      : 'text-text-secondary'
                  "
                >
                  Конец презентации
                </div>
                <div
                  v-if="
                    slide.start_time !== undefined ||
                    slide.startTime !== undefined
                  "
                  class="text-[9px] font-mono mt-0.5 opacity-50"
                  :class="
                    currentSlide === index
                      ? 'text-red-400'
                      : 'text-text-secondary'
                  "
                >
                  {{ formatTimeSimple(slide.start_time ?? slide.startTime) }}
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- Slide context menu -->
    <div
      v-if="ctxMenu"
      class="fixed inset-0 z-[400]"
      @click="ctxMenu = null"
      @contextmenu.prevent="ctxMenu = null"
    ></div>
    <div
      v-if="ctxMenu"
      class="fixed z-[401] w-52 rounded-xl border border-text-muted bg-bg-surface shadow-2xl py-1.5 text-sm"
      :style="{ left: ctxMenu.x + 'px', top: ctxMenu.y + 'px' }"
      @click.stop
    >
      <button @click="startRename" class="w-full text-left px-4 py-2 hover:bg-bg-surface-hover text-text-primary transition-colors">✏️ Переименовать</button>
      <button @click="emit('duplicate-slide', ctxMenu.index); ctxMenu = null" class="w-full text-left px-4 py-2 hover:bg-bg-surface-hover text-text-primary transition-colors">⧉ Дублировать</button>
      <div class="px-4 py-2 flex items-center gap-2 border-t border-text-muted mt-1 pt-2">
        <span class="text-text-secondary text-xs">Стиль:</span>
        <select
          :value="slidesData[ctxMenu.index]?.data?.payload?.variant || ''"
          @change="emit('set-slide-variant', { index: ctxMenu.index, variant: $event.target.value || null }); ctxMenu = null"
          class="flex-1 min-w-0 bg-bg-base border border-text-muted rounded-md px-1.5 py-1 text-xs text-text-primary focus:outline-none"
        >
          <option value="">— проект —</option>
          <option v-for="v in variantsList" :key="v.slug" :value="v.slug">{{ v.name || v.slug }}</option>
        </select>
      </div>
      <button @click="emit('delete-slide', ctxMenu.index); ctxMenu = null" class="w-full text-left px-4 py-2 hover:bg-red-500/20 text-red-400 transition-colors border-t border-text-muted mt-1 pt-2">🗑 Удалить</button>
    </div>

    <!-- Main Content Wrapper -->
    <div
      class="flex-1 min-w-0 flex flex-col relative transition-all duration-300"
      :style="{
        marginRight:
          props.isEditorOpen && !isFullscreen && !isMobile ? '500px' : '0px',
      }"
    >
      <div
        ref="container"
        :class="[
          'flex-1 min-w-0 outline-none select-none flex justify-center overflow-hidden relative',
          props.isEditorOpen && !isFullscreen && !isMobile
            ? 'items-start pt-8'
            : isMobile
              ? 'items-start pt-2'
              : 'items-center',
        ]"
        :style="{
          cursor:
            isCanvasInteractive && isModifierPressed
              ? isDragging
                ? 'grabbing'
                : 'grab'
              : 'default',
        }"
        tabindex="0"
        style="touch-action: pan-y"
        @mousedown="handleMouseDown"
        @mousemove="handleMouseMove"
        @mouseup="handleMouseUp"
        @mouseleave="handleMouseUp"
        @wheel="handleWheel"
        @touchstart.passive="onTouchStart"
        @touchend="onTouchEnd"
      >
        <div
          ref="slidesContainer"
          class="slides-container relative shrink-0 bg-bg-base text-text-primary shadow-2xl"
          :class="{ 'safezone-flat': !!safeZone }"
          style="clip-path: inset(0); isolation: isolate"
          :style="[
            containerStyle,
            {
              backgroundImage: 'var(--bg-image, none)',
              backgroundSize: 'cover',
              backgroundAttachment: 'fixed',
            },
          ]"
        >
          <!-- Vector/PNG Decorations Layer -->
          <div
            class="absolute inset-0 pointer-events-none z-0 bg-no-repeat"
            style="
              background: var(--bg-decorations, none);
              background-size: var(--bg-decorations-size, contain);
              background-position: var(
                --bg-decorations-position,
                bottom center
              );
            "
          ></div>

          <!-- Background Overlay (for noise/texture) -->
          <div
            class="absolute inset-0 pointer-events-none z-0 mix-blend-overlay"
            style="
              background-image: var(--bg-overlay, none);
              opacity: var(--bg-overlay-opacity, 1);
            "
          ></div>

          <!-- Safe-box: внутренний слой со слайдами. Фон контейнера (bg,
               decorations, overlay) всегда на весь кадр, а safe-zone рендера
               шортс сжимает/сдвигает только этот слой. -->
          <div class="absolute inset-0 slides-safebox" :style="safeBoxStyle">
            <div class="slides-fitbox absolute inset-0" :style="fitBoxStyle">
              <slot></slot>
            </div>
          </div>
        </div>
      </div>

      <!-- Glass Pill Controls Wrapper (Hit area) -->
      <div
        class="player-pill absolute left-1/2 -translate-x-1/2 z-[150] group/panel flex justify-center items-end h-24 w-[600px] max-w-[95vw] min-w-0"
        :style="pillStyle"
      >
        <!-- Клик вне меню закрывает дропдауны -->
        <div v-if="openMenu" class="fixed inset-0 z-40" @click="openMenu = null"></div>
        <!-- Glass Pill Controls -->
        <div
          class="relative flex items-center backdrop-blur-xl rounded-full border border-text-muted opacity-0 group-hover/panel:opacity-100 transition-opacity duration-300 delay-0 group-hover/panel:delay-300 shadow-2xl pointer-events-auto z-50 min-w-0 max-w-full flex-nowrap"
          :class="[
            isMobile
              ? 'gap-1 px-2 py-2 overflow-x-auto hide-scrollbar bg-bg-surface/45'
              : 'gap-3 px-5 py-2.5 bg-bg-surface/90',
            { 'opacity-100': !!openMenu || isMobile },
          ]"
        >
          <!-- Тоглер левой навигации (телефон): выезжащий drawer со слайдами -->
          <!-- ЛЕВАЯ ГРУППА (на десктопе flex-1, чтобы Play стоял ровно по центру) -->
          <div :class="isMobile ? 'flex items-center gap-1' : 'flex items-center gap-3 flex-1 justify-start min-w-0'">
          <button
            v-if="showControls"
            @click="isSidebarOpen = !isSidebarOpen"
            class="transition-colors p-2 -ml-1"
            :class="navOpen ? 'text-brand-blue' : 'text-text-secondary hover:text-text-primary'"
            title="Слайды (навигация)"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>
          </button>

          <!-- Навигация по слайдам (нужна и с телефона, где нет хоткеев) -->
          <button
            @click="goBack()"
            class="text-text-secondary hover:text-text-primary transition-colors disabled:opacity-30 p-1.5 -mx-0.5"
            :disabled="currentSlide === 0 && currentClick === 0"
            title="Предыдущий слайд"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
          </button>

          <!-- Slide Counter (на телефоне — кнопка открытия списка) -->
          <button
            @click="isMobile && (isSidebarOpen = !isSidebarOpen)"
            class="text-text-secondary font-mono text-sm tracking-wide select-none whitespace-nowrap shrink-0 px-1"
            :class="{ 'cursor-pointer hover:text-text-primary': isMobile }"
            :title="isMobile ? 'Список слайдов' : ''"
          >
            {{
              currentSlide >= normalSlidesCount
                ? normalSlidesCount
                : currentSlide + 1
            }}
            <span class="text-text-muted mx-0.5">/</span>
            {{ normalSlidesCount }}
          </button>

          <button
            @click="advance()"
            class="text-text-secondary hover:text-text-primary transition-colors disabled:opacity-30 p-1.5 -mx-0.5"
            :disabled="currentSlide >= normalSlidesCount"
            title="Следующий слайд"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
          </button>

          <!-- Тоглер таймлайна (телефон). Таймлайн закрывается ТОЛЬКО здесь. -->
          <button
            v-if="showControls"
            @click="isDebugOpen = !isDebugOpen"
            class="transition-colors p-2 -mx-1"
            :class="isDebugOpen ? 'text-brand-blue' : 'text-text-secondary hover:text-text-primary'"
            title="Таймлайн"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12h3l3-7 4 14 3-7h5"></path></svg>
          </button>

          <div class="w-px h-5 bg-bg-surface mx-1"></div>
          </div>
          <!-- /ЛЕВАЯ ГРУППА -->

          <!-- Controls: Play/Pause — крупная круглая кнопка по центру панели -->
          <button
            @click="isPlaying ? pause() : play()"
            class="shrink-0 mx-1 rounded-full flex items-center justify-center bg-brand-blue text-white hover:opacity-90 transition-opacity shadow-lg"
            :class="isMobile ? 'w-10 h-10' : 'w-11 h-11'"
            title="Play/Pause [P]"
          >
            <svg
              v-if="!isPlaying"
              xmlns="http://www.w3.org/2000/svg"
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="currentColor"
              stroke="currentColor"
              stroke-width="1"
              stroke-linecap="round"
              stroke-linejoin="round"
              :style="!isPlaying ? 'margin-left:2px' : ''"
            >
              <polygon points="5 3 19 12 5 21 5 3"></polygon>
            </svg>
            <svg
              v-else
              xmlns="http://www.w3.org/2000/svg"
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="currentColor"
              stroke="currentColor"
              stroke-width="1"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <rect x="6" y="4" width="4" height="16"></rect>
              <rect x="14" y="4" width="4" height="16"></rect>
            </svg>
          </button>

          <!-- ПРАВАЯ ГРУППА (на десктопе flex-1, чтобы Play стоял ровно по центру) -->
          <div :class="isMobile ? 'flex items-center gap-1' : 'flex items-center gap-3 flex-1 justify-end min-w-0'">
          <!-- Редактирование (E) — оставлен видимым как частый режим -->
          <button
            v-if="canEdit"
            @click="toggleEditMode"
            class="text-text-secondary hover:text-text-primary transition-colors"
            :class="{ 'text-brand-blue': isEditorOpen }"
            title="Режим редактирования [E]"
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
                d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"
              ></path>
              <path
                d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"
              ></path>
            </svg>
          </button>

          <!-- Настройки презентации (тема/вариант/доступ) — прямой доступ на десктопе -->
          <button
            v-if="canEdit"
            @click="$emit('open-settings')"
            class="text-text-secondary hover:text-text-primary transition-colors"
            title="Настройки презентации"
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
              <circle cx="12" cy="12" r="3"></circle>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
            </svg>
          </button>

          <!-- Вид ▾ : мобильный / слайды / полный экран / отладка (desktop) -->
          <div v-if="!isMobile" class="relative">
            <button
              @click="openMenu = openMenu === 'view' ? null : 'view'"
              class="text-text-secondary hover:text-text-primary transition-colors"
              :class="{ 'text-brand-blue': openMenu === 'view' || forceMobile || isSidebarOpen || isFullscreen || isDebugOpen }"
              title="Вид"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                <circle cx="12" cy="12" r="3"></circle>
              </svg>
              <span class="text-[9px] align-super">▾</span>
            </button>
            <div v-if="openMenu === 'view'" class="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 bg-bg-surface border border-text-muted rounded-lg shadow-2xl p-1 flex flex-col min-w-[190px] z-50">
              <button @click="toggleMobileMode(); openMenu = null" class="text-left px-3 py-2 rounded-md text-sm text-text-primary hover:bg-bg-surface-hover whitespace-nowrap">📱 Мобильный [M]</button>
              <button @click="toggleSidebar(); openMenu = null" class="text-left px-3 py-2 rounded-md text-sm text-text-primary hover:bg-bg-surface-hover whitespace-nowrap">▤ Слайды [S]</button>
              <button @click="toggleFullscreen(); openMenu = null" class="text-left px-3 py-2 rounded-md text-sm text-text-primary hover:bg-bg-surface-hover whitespace-nowrap">⛶ На весь экран [F]</button>
              <button v-if="canEdit" @click="isDebugOpen = !isDebugOpen; openMenu = null" class="text-left px-3 py-2 rounded-md text-sm text-text-primary hover:bg-bg-surface-hover whitespace-nowrap">🐞 Отладка [D]</button>
            </div>
          </div>

          <!-- Данные ▾ : звук / медиа (desktop) -->
          <div v-if="!isMobile" class="relative">
            <button
              @click="openMenu = openMenu === 'data' ? null : 'data'"
              class="text-text-secondary hover:text-text-primary transition-colors"
              :class="{ 'text-brand-blue': openMenu === 'data' }"
              title="Данные"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line>
                <line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line>
              </svg>
              <span class="text-[9px] align-super">▾</span>
            </button>
            <div v-if="openMenu === 'data'" class="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 bg-bg-surface border border-text-muted rounded-lg shadow-2xl p-1 flex flex-col min-w-[200px] z-50">
              <button v-if="isAudioLoaded" @click="toggleAudioMute(); openMenu = null" class="text-left px-3 py-2 rounded-md text-sm text-text-primary hover:bg-bg-surface-hover whitespace-nowrap">{{ isAudioMuted ? '🔊 Включить звук' : '🔇 Выключить звук' }}</button>
              <button v-if="canEdit" @click="$emit('open-media-library'); openMenu = null" class="text-left px-3 py-2 rounded-md text-sm text-text-primary hover:bg-bg-surface-hover whitespace-nowrap">🖼 Медиа-библиотека</button>
            </div>
          </div>

          <!-- Экспорт ▾ : портрет / ландшафт / рендер-ферма (desktop) -->
          <div v-if="!isMobile && canEdit" class="relative">
            <button
              @click="openMenu = openMenu === 'export' ? null : 'export'"
              class="text-text-secondary hover:text-text-primary transition-colors hover:text-brand-green"
              :class="{ 'text-brand-green': openMenu === 'export' }"
              title="Экспорт"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="17 8 12 3 7 8"></polyline>
                <line x1="12" y1="3" x2="12" y2="15"></line>
              </svg>
              <span class="text-[9px] align-super">▾</span>
            </button>
            <div v-if="openMenu === 'export'" class="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 bg-bg-surface border border-text-muted rounded-lg shadow-2xl p-1 flex flex-col min-w-[220px] z-50">
              <button @click="$emit('quick-render', 'portrait'); openMenu = null" class="text-left px-3 py-2 rounded-md text-sm text-text-primary hover:bg-bg-surface-hover whitespace-nowrap">📱 Портрет 1080×1920</button>
              <button @click="$emit('quick-render', 'landscape'); openMenu = null" class="text-left px-3 py-2 rounded-md text-sm text-text-primary hover:bg-bg-surface-hover whitespace-nowrap">🖥 Ландшафт 1920×1280</button>
              <button @click="$emit('open-render-manager'); openMenu = null" class="text-left px-3 py-2 rounded-md text-sm text-text-primary hover:bg-bg-surface-hover whitespace-nowrap">⬆ Рендер-ферма</button>
            </div>
          </div>

          <!-- ✨ AI-ассистент (desktop) -->
          <button
            v-if="!isMobile && canEdit"
            @click="$emit('open-ai')"
            class="text-text-secondary hover:text-text-primary transition-colors"
            title="AI-ассистент"
          >
            ✨
          </button>

          <!-- Ещё (телефон): одна понятная панель действий с подписями -->
          <button
            v-if="showControls"
            @click="showMore = true"
            class="transition-colors p-2 -mr-1"
            :class="showMore ? 'text-brand-blue' : 'text-text-secondary hover:text-text-primary'"
            title="Ещё"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><circle cx="5" cy="12" r="1.6"></circle><circle cx="12" cy="12" r="1.6"></circle><circle cx="19" cy="12" r="1.6"></circle></svg>
          </button>

          <div v-if="isEditorOpen" class="flex items-center gap-2 w-28 ml-1">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="12"
              height="12"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              class="text-text-muted"
            >
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
              <line x1="8" y1="11" x2="14" y2="11"></line>
            </svg>
            <input
              type="range"
              min="0.2"
              max="2"
              step="0.05"
              v-model="customScale"
              class="w-full accent-brand-lightBlue"
            />
          </div>
          </div>
          <!-- /ПРАВАЯ ГРУППА -->
        </div>
      </div>
    </div>

    <!-- Мобильная панель действий «Ещё»: понятные подписи, ничего не обрезается -->
    <div
      v-if="showControls && showMore"
      class="fixed inset-0 z-[350] flex flex-col justify-end"
    >
      <div class="absolute inset-0 bg-black/40" @click="showMore = false"></div>
      <div
        class="relative bg-bg-surface rounded-t-2xl shadow-2xl max-h-[80dvh] overflow-y-auto"
        :style="{ paddingBottom: 'calc(env(safe-area-inset-bottom, 0px) + 12px)' }"
      >
        <div class="flex items-center justify-between px-4 pt-3 pb-2 border-b border-text-muted sticky top-0 bg-bg-surface z-10">
          <span class="text-sm font-bold text-text-primary">Действия</span>
          <button @click="showMore = false" class="text-text-secondary hover:text-text-primary p-1" title="Закрыть">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>
        <div class="p-2 flex flex-col">
          <button v-if="canEdit"  @click="showMore = false; $emit('open-render-manager')" class="text-left px-4 py-3 rounded-lg text-sm text-text-primary hover:bg-bg-surface-hover flex items-center gap-3"><Icon icon="heroicons:arrow-up-tray" class="w-5 h-5 shrink-0 text-brand-green" /> Рендер-ферма — экспорт видео</button>
          <button v-if="canEdit"  @click="showMore = false; $emit('quick-render', 'portrait')" class="text-left px-4 py-3 rounded-lg text-sm text-text-primary hover:bg-bg-surface-hover flex items-center gap-3"><Icon icon="lucide:smartphone" class="w-5 h-5 shrink-0 text-text-secondary" /> Портрет 1080×1920</button>
          <button v-if="canEdit"  @click="showMore = false; $emit('quick-render', 'landscape')" class="text-left px-4 py-3 rounded-lg text-sm text-text-primary hover:bg-bg-surface-hover flex items-center gap-3"><Icon icon="lucide:monitor" class="w-5 h-5 shrink-0 text-text-secondary" /> Ландшафт 1920×1280</button>
          <button v-if="canEdit"  @click="showMore = false; $emit('open-media-library')" class="text-left px-4 py-3 rounded-lg text-sm text-text-primary hover:bg-bg-surface-hover flex items-center gap-3"><Icon icon="lucide:image" class="w-5 h-5 shrink-0 text-text-secondary" /> Медиа-библиотека</button>
          <button v-if="isAudioLoaded" @click="toggleAudioMute(); showMore = false" class="text-left px-4 py-3 rounded-lg text-sm text-text-primary hover:bg-bg-surface-hover flex items-center gap-3"><Icon :icon="isAudioMuted ? 'lucide:volume-2' : 'lucide:volume-x'" class="w-5 h-5 shrink-0 text-text-secondary" /> {{ isAudioMuted ? 'Включить звук' : 'Выключить звук' }}</button>
          <button v-if="canEdit"  @click="showMore = false; $emit('open-settings')" class="text-left px-4 py-3 rounded-lg text-sm text-text-primary hover:bg-bg-surface-hover flex items-center gap-3"><Icon icon="lucide:settings" class="w-5 h-5 shrink-0 text-text-secondary" /> Настройки презентации</button>
          <button v-if="canEdit"  @click="showMore = false; $emit('open-ai')" class="text-left px-4 py-3 rounded-lg text-sm text-text-primary hover:bg-bg-surface-hover flex items-center gap-3"><Icon icon="lucide:sparkles" class="w-5 h-5 shrink-0 text-brand-blue" /> AI-ассистент</button>
          <div class="h-px bg-bg-surface-hover my-1"></div>
          <button @click="showMore = false; toggleMobileMode()" class="text-left px-4 py-3 rounded-lg text-sm text-text-primary hover:bg-bg-surface-hover flex items-center gap-3"><Icon icon="lucide:tablet-smartphone" class="w-5 h-5 shrink-0 text-text-secondary" /> Мобильный вид {{ forceMobile ? '— выкл' : '— вкл' }}</button>
          <button @click="showMore = false; toggleFullscreen()" class="text-left px-4 py-3 rounded-lg text-sm text-text-primary hover:bg-bg-surface-hover flex items-center gap-3"><Icon icon="lucide:maximize" class="w-5 h-5 shrink-0 text-text-secondary" /> На весь экран</button>
        </div>
      </div>
    </div>

    <!-- Director Debug Panel -->
    <DirectorDebugPanel
      :isOpen="isDebugOpen"
      :isEditorOpen="isEditorOpen"
      :isFullscreen="isFullscreen"
      :slidesData="slidesData"
      :audioTimeline="audioTimeline"
      :recordingTrackId="recordingTrackId"
      @collapse="isDebugOpen = false"
      @height="onTimelineHeight"
      @update-timing="(idx, t) => $emit('update-timing', idx, t)"
      @update-local-timing="(idx) => $emit('update-local-timing', idx)"
      @dragging-local-timing="
        (idx, data) => $emit('dragging-local-timing', idx, data)
      "
      @update-audio-timeline="(data) => $emit('update-audio-timeline', data)"
      @request-add-audio="(trackId) => $emit('request-add-audio', trackId)"
      @toggle-record="(e) => $emit('toggle-record', e)"
      @request-generate-voice="
        (e) => $emit('request-generate-voice', 'edit-clip', e)
      "
      @seek="seek"
    />
    <!-- Autoplay Start Overlay -->
    <div
      v-if="requireAutoplayClick"
      class="absolute inset-0 z-[9999] flex items-center justify-center bg-bg-surface/60 backdrop-blur-md cursor-pointer"
      @click="startAutoplay"
    >
      <div class="text-center group">
        <div
          class="w-24 h-24 rounded-full bg-brand-green flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform shadow-lg shadow-brand-green/30"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="40"
            height="40"
            viewBox="0 0 24 24"
            fill="white"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="ml-2"
          >
            <polygon points="5 3 19 12 5 21 5 3"></polygon>
          </svg>
        </div>
        <h2 class="text-2xl font-bold text-text-primary mb-2 tracking-wide">
          Запустить презентацию
        </h2>
        <p class="text-text-secondary text-sm">
          Нажмите в любом месте, чтобы начать
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, provide, inject, computed, onMounted, onUnmounted, watch } from "vue";
import { Icon } from "@iconify/vue";
import { useMobile } from "../../composables/useMobile";
import { useScreenRecorder } from "../../composables/useScreenRecorder";
import DirectorDebugPanel from "./DirectorDebugPanel.vue";
import { useDirector } from "../../composables/useDirector";

const props = defineProps({
  totalSlides: {
    type: Number,
    required: true,
  },
  thumbnails: {
    type: Array,
    default: () => [],
  },
  // Стандартные размеры Core: 980x552
  width: {
    type: Number,
    default: 980,
  },
  height: {
    type: Number,
    default: 552,
  },
  initialSlide: {
    type: Number,
    default: 0,
  },
  timeline: {
    type: Array,
    default: () => [],
  },
  slidesData: {
    type: Array,
    default: () => [],
  },
  audioTimeline: {
    type: Object,
    default: () => null,
  },
  recordingTrackId: {
    type: String,
    default: null,
  },
  isEditorOpen: {
    type: Boolean,
    default: false,
  },
  renderWidth: {
    type: Number,
    default: null,
  },
  renderHeight: {
    type: Number,
    default: null,
  },
});

const normalSlidesCount = computed(() => {
  if (props.slidesData && props.slidesData.length > 0) {
    return props.slidesData.filter((s) => s.component !== "EndMarkerSlide")
      .length;
  }
  return props.totalSlides;
});

const emit = defineEmits([
  "edit-slide",
  "add-slide",
  "rename-slide",
  "duplicate-slide",
  "delete-slide",
  "set-slide-variant",
  "open-settings",
  "close-editor",
  "update-timing",
  "update-local-timing",
  "dragging-local-timing",
  "update-audio-timeline",
  "request-add-audio",
  "toggle-record",
  "request-generate-voice",
  "edit-clip",
  "open-media-library",
  "open-render-manager",
  "quick-render",
  "open-ai",
  "fullscreen-change",
]);

const isDebugOpen = ref(false);
// Группировка контролов пилюли (UX_REDESIGN Ф2 B): открытое меню 'view'|'data'|'export'|null
const openMenu = ref(null);
// Мобильная панель действий «Ещё» (единый список с подписями)
const showMore = ref(false);

const requireAutoplayClick = ref(false);
const startAutoplay = () => {
  requireAutoplayClick.value = false;
  play();
};

const { isMobile, isTouch, forceMobile, toggleForceMobile } = useMobile();
// AUTH_PLAN Ф2: права на редактирование (owner/editor). false = режим просмотра.
const canEdit = inject("canEdit", ref(true));
// Показывать контролы на любом тач-устройстве (в ландшафте isMobile=false, но hover нет)
const showControls = computed(() => isMobile.value || isTouch.value);
const { isRecording, toggleRecording, stopRecording } = useScreenRecorder();
const {
  isPlaying,
  play,
  pause,
  setTimeline,
  onEvent,
  clearListeners,
  seek,
  isAudioLoaded,
  isAudioMuted,
  toggleAudioMute,
  currentTime,
  timelineEvents,
  playUntilTime,
} = useDirector();

const isCanvasInteractive = computed(
  () => props.isEditorOpen || isDebugOpen.value,
);

const toggleEditMode = () => {
  if (!props.isEditorOpen) {
    emit("edit-slide", currentSlide.value);
  } else {
    emit("close-editor");
  }
};

const formatTimeSimple = (ms) => {
  if (ms === undefined || ms === null) return "00:00";
  const minutes = Math.floor(ms / 60000);
  const seconds = Math.floor((ms % 60000) / 1000);
  return `${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
};

// Контекстное меню слайда (UX-5): переименовать / дублировать / вариант / удалить
const ctxMenu = ref(null);
const renamingIndex = ref(null);
const renameText = ref("");
const variantsList = ref([]);

const openSlideMenu = async (index, e) => {
  if (!canEdit.value) return; // режим просмотра
  const slide = props.slidesData?.[index];
  if (!slide || slide.component === "EndMarkerSlide") return;
  ctxMenu.value = {
    index,
    x: Math.min(e.clientX, window.innerWidth - 220),
    y: Math.min(e.clientY, window.innerHeight - 220),
  };
  if (!variantsList.value.length) {
    try {
      const { fetchVariants } = await import("../../services/api");
      variantsList.value = (await fetchVariants()) || [];
    } catch {
      variantsList.value = [];
    }
  }
};

const startRename = () => {
  if (!ctxMenu.value) return;
  const idx = ctxMenu.value.index;
  const slide = props.slidesData?.[idx];
  renameText.value = (slide?.title || "").replace(/<[^>]*>/g, "");
  renamingIndex.value = idx;
  ctxMenu.value = null;
};

const commitRename = () => {
  if (renamingIndex.value === null) return;
  const idx = renamingIndex.value;
  renamingIndex.value = null;
  const title = (renameText.value || "").trim();
  if (title) emit("rename-slide", { index: idx, title });
};

watch(isRecording, (val) => {
  if (val) {
    isSidebarOpen.value = false;
  }
});

watch(
  () => props.timeline,
  (newTimeline) => {
    if (newTimeline && newTimeline.length > 0) {
      setTimeline(newTimeline);
    }
  },
  { immediate: true },
);

const currentSlide = ref(props.initialSlide);
const currentClick = ref(0);
const container = ref(null);
const slidesContainer = ref(null);
const scale = ref(1);
const isFullscreen = ref(false);
const isSidebarOpen = ref(false);
const maxClicksPerSlide = ref({});
const sidebarItems = ref([]);

// Левая навигация видима (не в полноэкранном режиме)
const navOpen = computed(() => isSidebarOpen.value && !isFullscreen.value);
// Сдвиг слайда на mobile под открытые панели (право — из-под nav, вверх — из-под таймлайна)
const panelOffset = ref({ x: 0, y: 0 });
// Измеренная высота таймлайна (реактивно; приходит событием из DirectorDebugPanel)
const timelineH = ref(0);
// Мобайл-растяжка: контейнер тянется фоном на всё свободное место,
// контент внутри — строго в пропорциях 450×800 через scale (fitBoxStyle).
const availW = ref(450);
const availH = ref(800);
const fitScale = ref(1);

watch(currentSlide, (newVal) => {
  const el = sidebarItems.value[newVal];
  if (el && typeof el.scrollIntoView === "function") {
    el.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  // Всегда сбрасываем зум и панорамирование при смене слайда
  resetView();

  if (props.isEditorOpen) {
    emit("edit-slide", newVal);
  }
});

const registerClicks = (index, maxClicks) => {
  maxClicksPerSlide.value[index] = maxClicks;
};

const toggleSidebar = () => {
  isSidebarOpen.value = !isSidebarOpen.value;
  setTimeout(updateScale, 50);
};

const toggleMobileMode = () => {
  toggleForceMobile();
  setTimeout(updateScale, 10);
};

const customScale = ref(1);

// Safe-zone для вертикального рендера (шортсы/рилсы): сжатие контентного слоя +
// лёгкий сдвиг, чтобы важное не уходило под кнопки YouTube/TikTok.
// Фон контейнера всегда остаётся на весь кадр — жмётся только .slides-safebox.
// Применяется ТОЛЬКО в рендере (серверный ?render=true&safe=... или live-захват
// портрета через событие presentation:safezone). Обычный просмотр/редактирование
// не затрагивается.
const safeZone = ref(null); // { scale: 0.85, shiftFrac: -0.02 (доля высоты слайда) }
const applySafeZone = (detail) => {
  if (!detail) {
    safeZone.value = null;
    return;
  }
  safeZone.value = {
    scale: Math.min(1, Math.max(0.5, Number(detail.scale) || 0.85)),
    shiftFrac: Number(detail.shiftFrac) || 0,
  };
};

// Стиль внутреннего слоя со слайдами (.slides-safebox — absolute inset-0,
// т.е. ровно размер контейнера). Шифт — в процентах от собственной высоты слоя,
// поэтому одинаков при любом разрешении кадра и внешнем масштабе.
const safeBoxStyle = computed(() => {
  if (!safeZone.value) return {};
  return {
    transform: `translate(0, ${safeZone.value.shiftFrac * 100}%) scale(${safeZone.value.scale})`,
    transformOrigin: "center center",
  };
});

// Видимая область (MOBILE_PLAN M0): visualViewport учитывает адресную строку/жесты.
const viewportSize = () => {
  const vv = window.visualViewport;
  if (vv && vv.width && vv.height) {
    return { width: Math.round(vv.width), height: Math.round(vv.height) };
  }
  return { width: window.innerWidth, height: window.innerHeight };
};

// Высота таймлайна из CSS-переменной (её измеряет DirectorDebugPanel).
// Единый источник правды: и drawer навигации (bottom), и ужим слайда.
const timelineHeightPx = () => {
  const v = getComputedStyle(document.documentElement).getPropertyValue(
    "--timeline-height",
  );
  const n = parseFloat(v);
  return Number.isFinite(n) ? n : 0;
};

const updateScale = () => {
  // In render mode with explicit dimensions: no scaling needed
  if (props.renderWidth && props.renderHeight) {
    scale.value = 1;
    return;
  }

  const dw = isMobile.value ? 450 : props.width;
  const dh = isMobile.value ? 800 : props.height;

  // База — видимая область (телефон учитывает адресную строку/жесты).
  // На десктопе уточняем по контейнеру (сайдбар/редактор/debug съедают место).
  const vp = viewportSize();
  let availableWidth = vp.width;
  let availableHeight = vp.height;

  if (!isMobile.value) {
    panelOffset.value = { x: 0, y: 0 };
    if (container.value) {
      availableWidth = container.value.clientWidth || vp.width;
      availableHeight = container.value.clientHeight || vp.height;
    } else {
      // Контейнер ещё не готов — приблизительно по видимой области
      const showSidebar = !isFullscreen.value && isSidebarOpen.value;
      availableWidth = showSidebar ? vp.width - 208 : vp.width;
      if (props.isEditorOpen && !isFullscreen.value) availableWidth -= 500;
      if (isDebugOpen.value && !isFullscreen.value) availableHeight -= 150;
    }
  } else {
    // Мобайл: фон контейнера растягивается на всё свободное место
    // (минус таймлайн и компактный резерв под пилюлю), а контент —
    // строго в пропорциях 450×800 через fitScale (см. fitBoxStyle).
    // Небольшие поля сверху/снизу — норма.
    const tlH =
      isDebugOpen.value && !isFullscreen.value
        ? timelineH.value || timelineHeightPx()
        : 0;
    const pillReserve = !isFullscreen.value ? 72 : 0;
    availableWidth = vp.width;
    availableHeight = Math.max(60, vp.height - tlH - pillReserve);
    availW.value = availableWidth;
    availH.value = availableHeight;
    fitScale.value = Math.min(
      Math.max(0.1, availableWidth / 450),
      Math.max(0.1, availableHeight / 800),
    );
    panelOffset.value = { x: 0, y: 0 };
    return;
  }

  const scaleX = Math.max(0.1, availableWidth / dw);
  const scaleY = Math.max(0.1, availableHeight / dh);
  scale.value = Math.min(scaleX, scaleY);
};

const panX = ref(0);
const panY = ref(0);
const isDragging = ref(false);
const isModifierPressed = ref(false);
let startX = 0;
let startY = 0;

const updateModifierState = (e) => {
  isModifierPressed.value = e.altKey || e.ctrlKey || e.metaKey;
};

const handleMouseDown = (e) => {
  if (!isCanvasInteractive.value) return;
  if (!(e.altKey || e.ctrlKey || e.metaKey)) return; // Требуем Alt/Ctrl для взаимодействия с холстом
  isDragging.value = true;
  startX = e.clientX - panX.value;
  startY = e.clientY - panY.value;
};

const handleMouseMove = (e) => {
  if (!isDragging.value || !isCanvasInteractive.value) return;
  panX.value = e.clientX - startX;
  panY.value = e.clientY - startY;
};

const handleMouseUp = () => {
  if (!isCanvasInteractive.value) return;
  isDragging.value = false;
};

const resetView = () => {
  panX.value = 0;
  panY.value = 0;
  customScale.value = 1;
  isDragging.value = false;
};

const handleWheel = (e) => {
  if (!isCanvasInteractive.value) return;
  if (!(e.altKey || e.ctrlKey || e.metaKey)) return; // Требуем Alt/Ctrl для взаимодействия с холстом
  e.preventDefault();
  const zoomSpeed = 0.05;
  if (e.deltaY < 0) {
    customScale.value = Math.min(3, Number(customScale.value) + zoomSpeed);
  } else {
    customScale.value = Math.max(0.2, Number(customScale.value) - zoomSpeed);
  }
};

watch(isCanvasInteractive, (newVal) => {
  if (!newVal) {
    resetView();
  }
});

watch(isDebugOpen, () => {
  setTimeout(updateScale, 10);
});

// Пересчитываем масштаб при смене мобильного режима
watch(isMobile, () => {
  setTimeout(updateScale, 10);
});

const containerStyle = computed(() => {
  const dw = isMobile.value ? 450 : props.width;
  const dh = isMobile.value ? 800 : props.height;

  // In render mode: fit container proportionally into target viewport
  // (фон — всегда на весь кадр; safe-zone жмёт внутренний .slides-safebox)
  if (props.renderWidth && props.renderHeight) {
    const scaleX = props.renderWidth / dw;
    const scaleY = props.renderHeight / dh;
    const fitScale = Math.min(scaleX, scaleY);
    return {
      width: `${dw}px`,
      height: `${dh}px`,
      transform: `scale(${fitScale})`,
      transformOrigin: "center center",
      transition: "none",
    };
  }

  // Мобайл: контейнер — растяжка фоном на всё доступное место (без scale —
  // масштаб уезжает внутрь, в fitBoxStyle, чтобы контент не тянулся).
  if (isMobile.value) {
    return {
      width: `${availW.value}px`,
      height: `${availH.value}px`,
      transform: `translate(${panX.value}px, ${panY.value}px)`,
      transformOrigin: "center top",
      transition: isDragging.value ? "none" : "transform 0.3s ease-out",
    };
  }

  return {
    width: `${dw}px`,
    height: `${dh}px`,
    transform: `translate(${panX.value + panelOffset.value.x}px, ${panY.value + panelOffset.value.y}px) scale(${scale.value * Number(customScale.value)})`,
    transformOrigin: "center center",
    transition: isDragging.value ? "none" : "transform 0.3s ease-out",
  };
});

// Мобайл-контент: фиксированный лист 450×800 по центру растянутого контейнера,
// масштаб — строго пропорциональный (contain). Десктоп/рендер — без изменений.
const fitBoxStyle = computed(() => {
  if (props.renderWidth && props.renderHeight) return {};
  if (!isMobile.value) return {};
  return {
    width: "450px",
    height: "800px",
    left: "50%",
    top: "50%",
    transform: `translate(-50%, -50%) scale(${fitScale.value * Number(customScale.value)})`,
    transformOrigin: "center center",
  };
});

// Пересчёт ужима при открытии/закрытии панелей на мобиле
watch([isSidebarOpen, isFullscreen], () => {
  if (isMobile.value) setTimeout(updateScale, 30);
});

// Таймлайн сообщил свою измеренную высоту → пересчитываем ужим слайда и границу nav
const onTimelineHeight = (h) => {
  timelineH.value = Number(h) || 0;
  if (isMobile.value) updateScale();
};

// Пилюля: поднимаем над открытым таймлайном, чтобы контролы оставались доступными
// (сам таймлайн не перекрываем). Z-index пилюли выше drawer — она всегда доступна.
const pillStyle = computed(() => {
  const tlH =
    isMobile.value && isDebugOpen.value && !isFullscreen.value
      ? timelineH.value
      : 0;
  return {
    bottom: `calc(${isMobile.value ? "0.25rem" : "1.5rem"} + env(safe-area-inset-bottom, 0px) + ${tlH}px)`,
  };
});

const progress = computed(() => {
  return (currentSlide.value / Math.max(1, normalSlidesCount.value)) * 100;
});

const renderedSlideIndex = computed(() => {
  const idx = currentSlide.value;
  if (
    props.slidesData &&
    props.slidesData[idx] &&
    props.slidesData[idx].component === "EndMarkerSlide"
  ) {
    for (let i = idx - 1; i >= 0; i--) {
      if (props.slidesData[i].component !== "EndMarkerSlide") {
        return i;
      }
    }
  }
  return idx;
});

provide("currentSlide", renderedSlideIndex);
provide("currentClick", currentClick);
provide("registerClicks", registerClicks);
provide("isMobile", isMobile);

const currentSlideStartTime = computed(() => {
  const slide = props.slidesData[renderedSlideIndex.value];
  return slide?.start_time ?? slide?.startTime ?? 0;
});
provide("currentSlideStartTime", currentSlideStartTime);

const advance = () => {
  const maxClicks = maxClicksPerSlide.value[currentSlide.value] || 0;
  if (currentClick.value < maxClicks) {
    currentClick.value++;
  } else if (currentSlide.value < props.totalSlides - 1) {
    currentSlide.value++;
    currentClick.value = 0;
    const t =
      props.slidesData[currentSlide.value]?.start_time ??
      props.slidesData[currentSlide.value]?.startTime;
    if (t !== undefined) {
      playSlideAnimation(currentSlide.value, t);
    }
  }
};

const goBack = () => {
  if (currentClick.value > 0) {
    currentClick.value--;
  } else if (currentSlide.value > 0) {
    currentSlide.value--;
    currentClick.value = maxClicksPerSlide.value[currentSlide.value] || 0;
    const t =
      props.slidesData[currentSlide.value]?.start_time ??
      props.slidesData[currentSlide.value]?.startTime;
    if (t !== undefined) {
      playSlideAnimation(currentSlide.value, t);
    }
  }
};

const playSlideAnimation = (index, t) => {
  seek(t);
  if (!isPlaying.value || playUntilTime.value !== null) {
    const nextIndex = props.slidesData.findIndex(
      (s, i) => i > index && s.component !== "EndMarkerSlide",
    );
    let nextT =
      nextIndex !== -1
        ? (props.slidesData[nextIndex]?.start_time ??
          props.slidesData[nextIndex]?.startTime)
        : undefined;

    const numT = Number(t) || 0;
    let numNextT = Number(nextT);

    // Ensure we have a valid future time to play until, otherwise local animation pauses instantly
    if (isNaN(numNextT) || numNextT <= numT) {
      numNextT = numT + 5000; // Default 5s duration if overlapping
    }

    play(numNextT - 1);
  }
};

// MOBILE_PLAN M2: тач-жесты по области слайда.
// Свайп ←/→ — слайд вперёд/назад; тап — пуск/пауза. Вертикаль не перехватываем
// (чтобы не ломать скролл страницы/жесты браузера).
let touchStartX = 0;
let touchStartY = 0;
let touchStartT = 0;
const onTouchStart = (e) => {
  const t = e.changedTouches && e.changedTouches[0];
  if (!t) return;
  touchStartX = t.clientX;
  touchStartY = t.clientY;
  touchStartT = Date.now();
};
const onTouchEnd = (e) => {
  const t = e.changedTouches && e.changedTouches[0];
  if (!t) return;
  const dx = t.clientX - touchStartX;
  const dy = t.clientY - touchStartY;
  const dt = Date.now() - touchStartT;
  const absX = Math.abs(dx);
  const absY = Math.abs(dy);
  if (absX > 50 && absX > absY * 1.5) {
    if (dx < 0) advance();
    else goBack();
    return;
  }
  if (absX < 12 && absY < 12 && dt < 350) {
    // Тап по слайду сворачивает левую навигацию (если открыта), иначе play/pause.
    // Таймлайн закрывается ТОЛЬКО своим тоглером — тап его не трогает.
    if (isMobile.value && isSidebarOpen.value) {
      isSidebarOpen.value = false;
      return;
    }
    if (isPlaying.value) pause();
    else play();
  }
};

const goTo = (index, fromTimeline = false) => {
  currentSlide.value = index;
  currentClick.value = 0;
  container.value?.focus();
  // На телефоне список слайдов — оверлей: после выбора закрываем, чтобы не мешал
  if (isMobile.value) isSidebarOpen.value = false;

  const t =
    props.slidesData[index]?.start_time ?? props.slidesData[index]?.startTime;
  if (!fromTimeline && t !== undefined) {
    playSlideAnimation(index, t);
  }
};

provide("goTo", goTo);

const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen().catch((err) => {
      console.warn(`Error attempting to enable fullscreen: ${err.message}`);
    });
  } else {
    document.exitFullscreen();
  }
};

// In render mode, automatically sync the current slide to the global timeline
const isRenderMode =
  new URLSearchParams(window.location.search).get("render") === "true" ||
  (props.renderWidth && props.renderHeight);
if (isRenderMode) {
  watch(currentTime, (t) => {
    if (t === undefined || t === null) return;
    let activeSlide = 0;
    for (let i = 0; i < props.slidesData.length; i++) {
      const s = props.slidesData[i];
      const start = s.start_time ?? s.startTime ?? 0;
      if (t >= start) {
        activeSlide = i;
      } else {
        break;
      }
    }
    if (currentSlide.value !== activeSlide) {
      currentSlide.value = activeSlide;
      currentClick.value = 0;
    }
  });
}

const handleFullscreenChange = () => {
  isFullscreen.value = !!document.fullscreenElement;
  emit("fullscreen-change", isFullscreen.value);
  // Даем браузеру время применить полноэкранный режим перед пересчетом масштаба
  setTimeout(updateScale, 50);
};

const toggleWorkspace = () => {
  const targetState = !(
    isSidebarOpen.value &&
    isDebugOpen.value &&
    props.isEditorOpen
  );

  if (isSidebarOpen.value !== targetState) toggleSidebar();
  isDebugOpen.value = targetState;
  if (props.isEditorOpen !== targetState) {
    if (targetState) {
      emit("edit-slide", currentSlide.value);
    } else {
      emit("close-editor");
    }
  }
};

const handleKeydownSimple = (e) => {
  // На время захвата — полный локдаун управления (пробел, W, стрелки и т.д.)
  if (typeof window !== "undefined" && window.__presentationCapturing) {
    e.preventDefault();
    return;
  }
  if (
    e.target.tagName === "INPUT" ||
    e.target.tagName === "TEXTAREA" ||
    e.target.isContentEditable
  ) {
    if (e.code === "Escape") {
      e.target.blur();
    }
    return;
  }

  const code = e.code;
  if (code === "KeyP") {
    e.preventDefault();
    if (isPlaying.value) pause();
    else play();
  } else if (code === "Space") {
    e.preventDefault();
    if (isDebugOpen.value) {
      if (isPlaying.value) pause();
      else play();
    } else {
      advance();
    }
  } else if (code === "ArrowRight" || code === "PageDown") {
    e.preventDefault();
    advance();
  } else if (code === "ArrowLeft" || code === "PageUp") {
    e.preventDefault();
    goBack();
  } else if (code === "KeyF") {
    e.preventDefault();
    toggleFullscreen();
  } else if (code === "KeyM") {
    e.preventDefault();
    toggleMobileMode();
  } else if (code === "KeyS" || code === "KeyN") {
    e.preventDefault();
    toggleSidebar();
  } else if (code === "KeyD" && canEdit.value) {
    e.preventDefault();
    isDebugOpen.value = !isDebugOpen.value;
  } else if (code === "KeyR" && canEdit.value) {
    e.preventDefault();
    emit("open-render-manager");
  } else if (code === "KeyE" && canEdit.value) {
    e.preventDefault();
    toggleEditMode();
  } else if ((code === "Backquote" || code === "KeyW") && canEdit.value) {
    e.preventDefault();
    toggleWorkspace();
  }
};

let resizeObserver = null;

const closeAllPanels = () => {
  isSidebarOpen.value = false;
  isDebugOpen.value = false;
};

onMounted(() => {
  window.addEventListener("keydown", updateModifierState);
  window.addEventListener("keyup", updateModifierState);
  window.addEventListener("mousemove", updateModifierState);
  window.addEventListener("presentation:close-all-modals", closeAllPanels);
  window.addEventListener("presentation:safezone", (e) =>
    applySafeZone(e.detail),
  );

  const urlParams = new URLSearchParams(window.location.search);

  // Safe-zone из URL (серверный рендер шортс дописывает ?safe=&safeshift=,
  // шифт — долей высоты слайда, минус = вверх).
  if (urlParams.get("render") === "true" && urlParams.has("safe")) {
    applySafeZone({
      scale: parseFloat(urlParams.get("safe")),
      shiftFrac: parseFloat(urlParams.get("safeshift") || "0"),
    });
  }

  if (urlParams.has("mobile")) {
    forceMobile.value =
      urlParams.get("mobile") === "1" || urlParams.get("mobile") === "true";
  }

  const isRenderMode =
    urlParams.has("render") &&
    (urlParams.get("render") === "1" || urlParams.get("render") === "true");

  // Reset timeline to the current slide's start time on mount
  const startT =
    props.slidesData[currentSlide.value]?.start_time ??
    props.slidesData[currentSlide.value]?.startTime ??
    0;
  seek(startT);

  if (isRenderMode) {
    // In headless render mode, do not auto-play and hide sidebar
    isSidebarOpen.value = false;
    pause();
  } else {
    // Start playing the local animation immediately upon load
    playSlideAnimation(currentSlide.value, startT);

    if (urlParams.has("autoplay")) {
      if (
        urlParams.get("autoplay") === "1" ||
        urlParams.get("autoplay") === "true"
      ) {
        isSidebarOpen.value = false; // Прячем навигацию при автовоспроизведении
        setTimeout(() => {
          play();
        }, 500);
      }
    }
  }

  onEvent("SLIDE_CHANGE", (payload) => {
    console.log(
      "SLIDE_CHANGE EVENT FIRED!",
      payload,
      "isEditorOpen:",
      props.isEditorOpen,
    );

    if (payload.slideIndex !== undefined) {
      console.log("UPDATING CURRENT SLIDE TO:", payload.slideIndex);
      currentSlide.value = payload.slideIndex;
      currentClick.value = 0;

      if (
        props.slidesData[payload.slideIndex]?.component === "EndMarkerSlide"
      ) {
        pause();
        // Snap precisely to the marker time so it doesn't overshoot visually
        const markerTime = props.slidesData[payload.slideIndex].start_time || 0;
        seek(markerTime);

        if (isRecording.value && stopRecording) {
          stopRecording();
        }
      }
    }
  });

  onEvent("COMPONENT_ACTION", (payload) => {
    if (payload.target === "Slide" && payload.action === "click") {
      if (!props.isEditorOpen) {
        advance();
      }
    }
  });

  document.addEventListener("fullscreenchange", handleFullscreenChange);

  if (container.value) {
    resizeObserver = new ResizeObserver(() => {
      updateScale();
    });
    resizeObserver.observe(container.value);
  }
  updateScale();

  // MOBILE_PLAN M0: пересчёт при изменении видимой области (адресная строка, поворот),
  // orientationchange — для iOS, где visualViewport.resize не всегда срабатывает.
  window.addEventListener("resize", updateScale);
  window.addEventListener("orientationchange", updateScale);
  if (window.visualViewport) {
    window.visualViewport.addEventListener("resize", updateScale);
    window.visualViewport.addEventListener("scroll", updateScale);
  }

  // Вешаем обработчик на window, чтобы хоткеи работали даже при потере фокуса контейнером
  window.addEventListener("keydown", handleKeydownSimple);
});

// Сброс вида в начало (для старта записи): seek меняет только время,
// а currentSlide/currentClick без тика стоят на месте — дёргаем явно.
const resetViewToStart = () => {
  currentSlide.value = 0;
  currentClick.value = 0;
};
window.addEventListener("presentation:reset-timeline", resetViewToStart);

onUnmounted(() => {
  clearListeners("SLIDE_CHANGE");

  if (resizeObserver) {
    resizeObserver.disconnect();
  }
  document.removeEventListener("fullscreenchange", handleFullscreenChange);
  window.removeEventListener("presentation:close-all-modals", closeAllPanels);
  window.removeEventListener("presentation:reset-timeline", resetViewToStart);
  window.removeEventListener("keydown", handleKeydownSimple);
  window.removeEventListener("keydown", updateModifierState);
  window.removeEventListener("keyup", updateModifierState);
  window.removeEventListener("mousemove", updateModifierState);
  window.removeEventListener("resize", updateScale);
  window.removeEventListener("orientationchange", updateScale);
  if (window.visualViewport) {
    window.visualViewport.removeEventListener("resize", updateScale);
    window.visualViewport.removeEventListener("scroll", updateScale);
  }
});
</script>

<style scoped>
.slides-container {
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.5); /* Визуальное отделение слайда от фона, если окно шире */
}

/* Мобильный nav-drawer — полупрозрачный оверлей поверх канваса (не сжимает слайд) */
@media (max-width: 900px) {
  .nav-drawer {
    background-color: rgb(var(--bg-surface-rgb) / 0.78);
    -webkit-backdrop-filter: blur(16px);
    backdrop-filter: blur(16px);
  }
  .nav-drawer .nav-head {
    background-color: transparent !important;
  }
  .nav-drawer .nav-row {
    background-color: rgb(var(--bg-surface-rgb) / 0.45) !important;
  }
}

/* Render mode: hide sidebar, controls, and fill viewport */
[data-render] .w-52 { display: none !important; }
[data-render] .absolute.bottom-6 { display: none !important; }
/* Пилюля управления: скрывать надёжно (bottom задаётся inline-стилем, класс bottom-6 не матчит) */
[data-render] .player-pill { display: none !important; }
[data-render] .flex-1.flex.flex-col.relative {
  margin-right: 0 !important;
  overflow: hidden !important;
}
[data-render] .outline-none.select-none {
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 100% !important;
  height: 100% !important;
  overflow: hidden !important;
}
/* Safe-zone (шортсы): НЕ гасим фон/декорации/оверлей контейнера.
   Раньше слайды были непрозрачной плоской заливкой, и поля сглаживали сцену
   (отсюда «flat»). Теперь слайды ПРОЗРАЧНЫ, а сцена (bg-image → bg-decorations →
   bg-overlay) — и есть фон слайда. Гашение в портретном рендере давало плоский
   фон и расхождение с превью. Поэтому сцена остаётся на весь кадр в любом
   формате — поля вокруг контента совпадают с фоном непрерывно. */
/* Hide all loading spinners in render mode */
[data-render] .bg-bg-surface.items-center.justify-center.z-10 { display: none !important; }
[data-render] .animate-pulse { display: none !important; }
/* Скрываем скроллбар для эстетики в сайдбаре */
.overflow-y-auto::-webkit-scrollbar {
  width: 4px;
}
.overflow-y-auto::-webkit-scrollbar-track {
  background: transparent;
}
.overflow-y-auto::-webkit-scrollbar-thumb {
  background: rgb(var(--text-primary-rgb) / 0.1);
  border-radius: 4px;
}
</style>
