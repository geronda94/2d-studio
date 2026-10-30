<template>
  <div v-if="isOpen" class="fixed inset-0 z-[300] bg-bg-base text-text-primary flex flex-col" :style="editorTheme">
    <header class="shrink-0 border-b border-text-muted/40 bg-bg-surface/70 px-4 py-3 flex items-center gap-3">
      <div class="min-w-0 flex-1">
        <div class="flex items-center gap-2">
          <span class="text-[10px] uppercase tracking-[0.22em] text-text-muted">Сцена</span>
          <span class="text-[10px] font-mono text-text-muted/70 truncate">{{ scene?.slide_id }}</span>
        </div>
        <input
          v-model="form.title"
          class="mt-1 w-full max-w-xl bg-transparent text-lg font-bold outline-none border-b border-transparent focus:border-brand-blue/60"
          placeholder="Название сцены"
        />
      </div>

      <label class="hidden md:flex items-center gap-2 text-[10px] uppercase tracking-wide text-text-muted">
        Старт, мс
        <input v-model.number="form.start_time" type="number" step="100"
          class="w-24 rounded-md border border-text-muted/40 bg-bg-base px-2 py-1.5 text-xs text-text-primary outline-none focus:border-brand-blue" />
      </label>
      <label class="hidden md:flex items-center gap-2 text-[10px] uppercase tracking-wide text-text-muted">
        Статус
        <select v-model="form.status" class="rounded-md border border-text-muted/40 bg-bg-base px-2 py-1.5 text-xs text-text-primary outline-none focus:border-brand-blue">
          <option value="draft">draft</option>
          <option value="review">review</option>
          <option value="approved">approved</option>
        </select>
      </label>
      <label class="hidden md:flex items-center gap-2 text-[10px] uppercase tracking-wide text-text-muted">
        Длительность, мс
        <input v-model.number="form.duration" type="number" step="100"
          class="w-24 rounded-md border border-text-muted/40 bg-bg-base px-2 py-1.5 text-xs text-text-primary outline-none focus:border-brand-blue" />
      </label>

      <button class="rounded-lg bg-brand-blue px-4 py-2 text-xs font-bold text-white hover:opacity-90" @click="save">Сохранить</button>
      <button class="rounded-lg border border-red-400/40 px-3 py-2 text-xs font-bold text-red-300 hover:bg-red-500/10" @click="$emit('delete', scene)">Удалить</button>
      <button class="rounded-lg border border-text-muted/40 px-3 py-2 text-xs text-text-secondary hover:bg-bg-surface" @click="$emit('close')">Закрыть</button>
    </header>

    <div class="flex-1 min-h-0 flex flex-col lg:flex-row">
      <section class="flex-1 min-h-0 flex flex-col bg-black/40">
        <div class="flex-1 min-h-0 flex items-center justify-center p-4">
          <div class="relative w-full max-w-[1100px] aspect-video overflow-hidden rounded-xl border border-white/10 bg-black shadow-2xl">
            <SceneHost
              ref="sceneHostRef"
              :code="form.code"
              :scene-props="parsedProps"
              :cues="form.cues"
              :start-time="0"
              :duration="form.duration"
              :time="previewTime"
              :view="form.view"
              :show-errors="true"
              preview
              @error="previewError = $event"
            />
          </div>
        </div>

        <div class="shrink-0 border-t border-text-muted/30 bg-bg-surface/50 px-4 py-3 flex items-center gap-3">
          <button class="h-9 w-9 rounded-full bg-brand-blue text-white flex items-center justify-center text-sm" @click="togglePreview">
            {{ previewPlaying ? '❚❚' : '▶' }}
          </button>
          <input v-model.number="previewTime" type="range" min="0" :max="Math.max(1, form.duration)" step="10" class="flex-1 accent-brand-blue" />
          <span class="w-28 text-right text-xs font-mono text-text-secondary">
            {{ (previewTime / 1000).toFixed(2) }}s / {{ (form.duration / 1000).toFixed(2) }}s
          </span>
          <button class="rounded-md border border-text-muted/40 px-2 py-1 text-[10px] text-text-secondary hover:bg-bg-surface" @click="previewTime = 0">0</button>
        </div>

        <div v-if="jsonError" class="shrink-0 bg-red-950/80 px-4 py-2 text-xs text-red-200 font-mono">Props JSON: {{ jsonError }}</div>
        <div v-else-if="previewError" class="shrink-0 bg-red-950/60 px-4 py-2 text-xs text-red-200 font-mono">{{ previewError }}</div>
      </section>

      <aside class="w-full lg:w-[46%] xl:w-[42%] shrink-0 border-t lg:border-t-0 lg:border-l border-text-muted/30 bg-bg-surface/40 flex flex-col min-h-0">
        <div class="shrink-0 flex items-center gap-1 px-3 pt-3 overflow-x-auto hide-scrollbar">
          <button v-for="tab in tabs" :key="tab.id"
            class="rounded-md px-3 py-1.5 text-[11px] font-bold uppercase tracking-wide transition-colors shrink-0 whitespace-nowrap"
            :class="activeTab === tab.id ? 'bg-brand-blue text-white' : 'text-text-secondary hover:bg-bg-surface'"
            @click="activeTab = tab.id">
            {{ tab.label }}
          </button>
          <div class="flex-1"></div>
          <button class="rounded-md border border-text-muted/40 px-2 py-1 text-[10px] text-text-secondary hover:bg-bg-surface" title="Загрузить демо-сцену" @click="loadDemo">Demo</button>
        </div>

        <div class="flex-1 min-h-0 p-3">
          <div v-if="activeTab === 'templates'" class="h-full overflow-y-auto space-y-2 pr-1">
            <p v-if="libraryError" class="text-xs text-red-300">{{ libraryError }}</p>
            <button
              v-for="t in templates" :key="t.slug"
              class="w-full text-left rounded-lg border border-text-muted/30 bg-bg-base px-3 py-2.5 hover:border-brand-blue/60 transition-colors"
              @click="applyTemplate(t)"
            >
              <div class="flex items-center justify-between gap-2">
                <span class="text-sm font-bold text-text-primary">{{ t.title }}</span>
                <span class="text-[10px] font-mono text-text-muted">{{ t.duration }} ms</span>
              </div>
              <div class="mt-0.5 text-[11px] leading-snug text-text-secondary">{{ t.description }}</div>
              <div class="mt-1 text-[9px] font-mono uppercase tracking-wide text-brand-light-blue">
                {{ (t.tags || []).join(' · ') }}
              </div>
            </button>
            <p v-if="!templates.length && !libraryError" class="text-xs text-text-muted">Загрузка…</p>
          </div>

          <div v-else-if="activeTab === 'environments'" class="h-full overflow-y-auto space-y-2 pr-1">
            <p v-if="libraryError" class="text-xs text-red-300">{{ libraryError }}</p>
            <button
              v-for="e in environments" :key="e.slug"
              class="w-full text-left rounded-lg border border-text-muted/30 bg-bg-base px-3 py-2.5 hover:border-brand-light-blue/60 transition-colors"
              @click="applyEnvironment(e)"
            >
              <div class="flex items-center justify-between gap-2">
                <span class="text-sm font-bold text-text-primary">{{ e.title }}</span>
                <span class="text-[10px] font-mono text-text-muted">{{ e.slug }}</span>
              </div>
              <div class="mt-0.5 text-[11px] leading-snug text-text-secondary">{{ e.description }}</div>
              <div class="mt-1 text-[9px] font-mono uppercase tracking-wide text-brand-light-blue">
                {{ (e.tags || []).join(' · ') }}
              </div>
            </button>
            <p v-if="!environments.length && !libraryError" class="text-xs text-text-muted">Загрузка…</p>
          </div>

          <div v-else-if="activeTab === 'objects'" class="h-full overflow-y-auto space-y-2 pr-1">
            <p v-if="libraryError" class="text-xs text-red-300">{{ libraryError }}</p>
            <div class="flex items-center justify-between gap-2">
              <p class="text-[10px] uppercase tracking-wide text-text-muted">
                Мир: {{ activeEnvData?.title || 'не выбран' }}
              </p>
              <label class="flex items-center gap-1 text-[10px] text-text-muted">
                <input v-model="showAllObjects" type="checkbox" class="accent-brand-blue" />
                все
              </label>
            </div>
            <p v-if="compatWarning" class="rounded-md border border-amber-400/40 bg-amber-950/40 px-2 py-1.5 text-[10px] text-amber-200">
              {{ compatWarning }}
            </p>
            <button
              v-for="o in visibleObjects" :key="o.slug"
              class="w-full text-left rounded-lg border border-text-muted/30 bg-bg-base px-3 py-2.5 hover:border-brand-green/60 transition-colors"
              @click="insertObject(o)"
            >
              <div class="text-sm font-bold text-text-primary">{{ o.title }}</div>
              <div class="mt-0.5 text-[11px] leading-snug text-text-secondary">{{ o.description }}</div>
              <div class="mt-1 text-[9px] font-mono uppercase tracking-wide text-brand-green">
                + {{ (o.domain || []).join(' · ') }}{{ o.surface ? ' / ' + o.surface : '' }}
              </div>
              <div v-if="(o.views || []).length > 1" class="mt-0.5 text-[9px] font-mono text-text-muted">
                views: {{ o.views.join(' / ') }}
              </div>
            </button>
            <p v-if="!objects.length && !libraryError" class="text-xs text-text-muted">Загрузка…</p>
          </div>

          <div v-else-if="activeTab === 'characters'" class="h-full overflow-y-auto space-y-2 pr-1">
            <p v-if="libraryError" class="text-xs text-red-300">{{ libraryError }}</p>
            <p class="text-[10px] uppercase tracking-wide text-text-muted">
              Готовые персонажи: скелет, липсинк, жесты
            </p>
            <textarea
              v-model="characterLine"
              rows="2"
              placeholder="Реплика для липсинка: «Братья и сестры, слово о главном»"
              class="w-full resize-none rounded-md border border-text-muted/30 bg-bg-base px-2 py-1.5 text-[11px] text-text-primary outline-none focus:border-brand-amber/60"
            ></textarea>
            <p class="text-[9px] text-text-muted">
              Текст превратится в виземы (7 с). Пусто — откроется демо-сцена.
            </p>
            <button
              v-for="c in characters" :key="c.slug"
              class="w-full text-left rounded-lg border border-text-muted/30 bg-bg-base px-3 py-2.5 hover:border-brand-amber/60 transition-colors"
              :disabled="characterBusy"
              @click="openCharacter(c)"
            >
              <div class="flex items-center justify-between gap-2">
                <span class="text-sm font-bold text-text-primary">{{ c.title }}</span>
                <span class="text-[9px] font-mono uppercase tracking-wide" :class="c.full_body ? 'text-brand-green' : 'text-brand-light-blue'">
                  {{ c.full_body ? 'full body' : 'bust' }}
                </span>
              </div>
              <div class="mt-0.5 text-[11px] leading-snug text-text-secondary">
                {{ c.mode }} · {{ c.visemes }} visemes · {{ (c.body || []).join(' · ') }}
              </div>
              <div class="mt-1 text-[9px] font-mono uppercase tracking-wide text-text-muted">
                {{ c.license }} · {{ c.author }}
              </div>
            </button>
            <p v-if="!characters.length && !libraryError" class="text-xs text-text-muted">Загрузка…</p>
          </div>

          <div v-else-if="activeTab === 'avatar'" class="h-full overflow-y-auto space-y-3 pr-1">
            <div v-if="!isAvatarScene" class="rounded-lg border border-brand-amber/40 bg-brand-amber/10 p-3 text-xs text-text-secondary">
              В текущей сцене нет 3D-аватара.
              <button
                class="mt-2 w-full rounded-md bg-brand-amber px-3 py-1.5 text-[11px] font-bold text-black hover:brightness-110"
                @click="openAvatarTemplate"
              >Открыть сцену «3D avatar»</button>
            </div>
            <template v-else>
              <div class="grid grid-cols-2 gap-2">
                <label class="block">
                  <span class="text-[9px] uppercase tracking-wide text-text-muted">Кадр</span>
                  <select v-model="avatar.preset" @change="postAvatar('preset')" class="mt-0.5 w-full rounded-md border border-text-muted/30 bg-bg-base px-2 py-1.5 text-[11px] text-text-primary outline-none focus:border-brand-amber/60">
                    <option v-for="v in ['face', 'bust', 'full', 'wide']" :key="v" :value="v">{{ v }}</option>
                  </select>
                </label>
                <label class="block">
                  <span class="text-[9px] uppercase tracking-wide text-text-muted">Настроение</span>
                  <select v-model="avatar.mood" @change="postAvatar('mood')" class="mt-0.5 w-full rounded-md border border-text-muted/30 bg-bg-base px-2 py-1.5 text-[11px] text-text-primary outline-none focus:border-brand-amber/60">
                    <option v-for="v in ['neutral', 'joy', 'sad', 'surprise', 'anger']" :key="v" :value="v">{{ v }}</option>
                  </select>
                </label>
              </div>

              <div class="grid grid-cols-2 gap-2">
                <label class="block">
                  <span class="text-[9px] uppercase tracking-wide text-text-muted">Базовый клип</span>
                  <select v-model="avatar.idleClip" @change="postAvatar('clips')" class="mt-0.5 w-full rounded-md border border-text-muted/30 bg-bg-base px-2 py-1.5 text-[11px] text-text-primary outline-none focus:border-brand-amber/60">
                    <option v-for="v in clipOptions" :key="v" :value="v">{{ v }}</option>
                  </select>
                </label>
                <label class="block">
                  <span class="text-[9px] uppercase tracking-wide text-text-muted">Клип речи</span>
                  <select v-model="avatar.talkClip" @change="postAvatar('clips')" class="mt-0.5 w-full rounded-md border border-text-muted/30 bg-bg-base px-2 py-1.5 text-[11px] text-text-primary outline-none focus:border-brand-amber/60">
                    <option v-for="v in clipOptions" :key="v" :value="v">{{ v }}</option>
                  </select>
                </label>
              </div>

              <label class="block">
                <span class="flex items-center justify-between text-[9px] uppercase tracking-wide text-text-muted">
                  <span>Вес речи</span><span class="font-mono text-brand-light-blue">{{ avatar.talk_weight.toFixed(2) }}</span>
                </span>
                <input v-model.number="avatar.talk_weight" type="range" min="0" max="1" step="0.05" class="w-full accent-brand-blue" @input="postAvatar('clips')" />
              </label>

              <div class="grid grid-cols-2 gap-2">
                <label class="block">
                  <span class="text-[9px] uppercase tracking-wide text-text-muted">Взгляд X</span>
                  <input v-model.number="avatar.gaze.x" type="range" min="-1" max="1" step="0.05" class="w-full accent-brand-blue" @input="postAvatar('gaze')" />
                </label>
                <label class="block">
                  <span class="text-[9px] uppercase tracking-wide text-text-muted">Взгляд Y</span>
                  <input v-model.number="avatar.gaze.y" type="range" min="-1" max="1" step="0.05" class="w-full accent-brand-blue" @input="postAvatar('gaze')" />
                </label>
              </div>

              <div>
                <span class="text-[9px] uppercase tracking-wide text-text-muted">Реплика</span>
                <textarea
                  v-model="avatarLine"
                  rows="2"
                  placeholder="Что она говорит: «Привет, это трёхмерный аватар»"
                  class="mt-0.5 w-full resize-none rounded-md border border-text-muted/30 bg-bg-base px-2 py-1.5 text-[11px] text-text-primary outline-none focus:border-brand-amber/60"
                ></textarea>
                <div class="mt-1 flex items-center gap-2">
                  <button class="rounded-md bg-brand-amber px-3 py-1.5 text-[10px] font-bold text-black hover:brightness-110 disabled:opacity-50" :disabled="avatarBusy" @click="speakAvatar">
                    {{ avatarBusy ? '…' : 'Озвучить' }}
                  </button>
                  <button class="rounded-md border border-text-muted/40 px-2 py-1.5 text-[10px] text-text-secondary hover:bg-bg-surface" @click="clearVisemes">Тишина</button>
                  <span class="text-[9px] font-mono text-text-muted">{{ avatar.visemes.length }} виземов</span>
                </div>
              </div>

              <div>
                <span class="text-[9px] uppercase tracking-wide text-text-muted">Жесты</span>
                <div class="mt-1 grid grid-cols-3 gap-1.5">
                  <button
                    v-for="g in gestureOptions" :key="g.id"
                    class="rounded-md border border-text-muted/30 bg-bg-base px-1.5 py-1.5 text-[10px] text-text-secondary hover:border-brand-amber/60 hover:text-text-primary"
                    @click="addGesture(g.id)"
                  >{{ g.label }}</button>
                </div>
                <div v-for="(g, i) in avatar.gestures" :key="'g' + i" class="mt-1 flex items-center justify-between rounded-md bg-bg-base px-2 py-1 text-[10px] text-text-secondary">
                  <span class="font-mono">{{ (g.at / 1000).toFixed(2) }}s · {{ g.type }}</span>
                  <button class="text-red-300 hover:text-red-200" @click="removeGesture(i)">×</button>
                </div>
              </div>

              <div class="rounded-lg border border-text-muted/30 bg-bg-base p-2">
                <div class="flex items-center justify-between">
                  <span class="text-[9px] uppercase tracking-wide text-text-muted">Поза (смещение)</span>
                  <span class="text-[9px] font-mono text-brand-light-blue">{{ avatarBone }}</span>
                </div>
                <select v-model="avatarBone" class="mt-1 w-full rounded-md border border-text-muted/30 bg-bg-surface px-2 py-1 text-[10px] text-text-primary outline-none" @change="loadBonePose">
                  <option v-for="b in boneOptions" :key="b" :value="b">{{ b }}</option>
                </select>
                <label v-for="axis in ['x', 'y', 'z']" :key="axis" class="mt-1 block">
                  <span class="flex items-center justify-between text-[9px] uppercase tracking-wide text-text-muted">
                    <span>{{ axis.toUpperCase() }}</span><span class="font-mono">{{ poseAngles[axis] }}°</span>
                  </span>
                  <input v-model.number="poseAngles[axis]" type="range" min="-120" max="120" step="5" class="w-full accent-brand-blue" @input="applyPoseSlider" />
                </label>
                <div class="mt-1 flex gap-1.5">
                  <button class="flex-1 rounded-md bg-brand-blue px-2 py-1.5 text-[10px] font-bold text-white hover:brightness-110" @click="addPoseKey">
                    Ключ в {{ (previewTime / 1000).toFixed(2) }}s
                  </button>
                  <button class="rounded-md border border-text-muted/40 px-2 py-1.5 text-[10px] text-text-secondary hover:bg-bg-surface" @click="resetBonePose">Сброс</button>
                </div>
                <div v-for="(k, i) in avatar.pose_keys" :key="'p' + i" class="mt-1 flex items-center justify-between rounded-md bg-bg-surface px-2 py-1 text-[10px] text-text-secondary">
                  <span class="font-mono">{{ (k.at / 1000).toFixed(2) }}s · {{ k.bone }} · {{ k.x }}/{{ k.y }}/{{ k.z }}</span>
                  <button class="text-red-300 hover:text-red-200" @click="removePoseKey(i)">×</button>
                </div>
              </div>

              <button class="w-full rounded-md border border-brand-amber/50 bg-brand-amber/10 px-3 py-2 text-[11px] font-bold text-brand-amber hover:bg-brand-amber/20" @click="applyAvatarProps">
                Записать в props
              </button>
            </template>
          </div>

          <div v-else-if="activeTab === 'layers'" class="h-full flex flex-col gap-2">
            <div class="flex-1 min-h-0 overflow-y-auto space-y-1 pr-1">
              <button
                v-for="l in layerList" :key="l.index"
                class="w-full text-left rounded-md border px-2.5 py-2 text-xs transition-colors"
                :class="selectedLayer === l.index
                  ? 'border-brand-blue bg-brand-blue/15 text-text-primary'
                  : 'border-text-muted/30 bg-bg-base text-text-secondary hover:border-brand-blue/40'"
                @click="selectedLayer = l.index"
              >
                <div class="flex items-center justify-between">
                  <span class="font-mono">{{ l.slug }}</span>
                  <span class="text-[9px] text-text-muted">#{{ l.index }}</span>
                </div>
                <div v-if="l.view" class="text-[9px] font-mono text-brand-light-blue">view: {{ l.view }}</div>
              </button>
              <p v-if="!layerList.length" class="text-xs text-text-muted py-4">
                В сцене нет объектов. Добавь мир и объект во вкладках Worlds / Objects.
              </p>
            </div>

            <div v-if="selectedLayerMeta" class="shrink-0 rounded-lg border border-text-muted/30 bg-bg-base p-2.5 space-y-2">
              <div class="text-[10px] font-mono uppercase tracking-wide text-brand-light-blue">
                {{ selectedLayerMeta.slug }} #{{ selectedLayerMeta.index }}
              </div>
              <div class="space-y-2">
                <label class="block">
                  <div class="flex justify-between text-[9px] text-text-muted"><span>X</span><span>{{ layerNum('left', 12, '%') }}{{ layerUnit('left', '%') }}</span></div>
                  <input type="range" min="-20" max="100" step="0.5" :value="layerNum('left', 12, '%')"
                    @input="setLayerNum('left', $event.target.value, '%')" class="w-full accent-brand-blue" />
                </label>
                <label class="block">
                  <div class="flex justify-between text-[9px] text-text-muted"><span>Y / bottom</span><span>{{ layerNum('bottom', 18, '%') }}{{ layerUnit('bottom', '%') }}</span></div>
                  <input type="range" min="-20" max="100" step="0.5" :value="layerNum('bottom', 18, '%')"
                    @input="setLayerNum('bottom', $event.target.value, '%')" class="w-full accent-brand-blue" />
                </label>
                <div class="grid grid-cols-2 gap-2">
                  <label class="block">
                    <div class="flex justify-between text-[9px] text-text-muted"><span>Ширина</span><span>{{ layerNum('width', 38, 'vmin') }}{{ layerUnit('width', 'vmin') }}</span></div>
                    <input type="range" min="2" max="100" step="1" :value="layerNum('width', 38, 'vmin')"
                      @input="setLayerNum('width', $event.target.value, 'vmin')" class="w-full accent-brand-blue" />
                  </label>
                  <label class="block">
                    <div class="flex justify-between text-[9px] text-text-muted"><span>Высота</span><span>{{ layerNum('height', 16, 'vmin') }}{{ layerUnit('height', 'vmin') }}</span></div>
                    <input type="range" min="2" max="100" step="1" :value="layerNum('height', 16, 'vmin')"
                      @input="setLayerNum('height', $event.target.value, 'vmin')" class="w-full accent-brand-blue" />
                  </label>
                </div>
                <div class="grid grid-cols-2 gap-2">
                  <label class="block">
                    <div class="flex justify-between text-[9px] text-text-muted"><span>Масштаб</span><span>{{ layerScale.toFixed(2) }}</span></div>
                    <input type="range" min="0.2" max="3" step="0.05" :value="layerScale"
                      @input="setLayerScale($event.target.value)" class="w-full accent-brand-blue" />
                  </label>
                  <label class="block">
                    <div class="flex justify-between text-[9px] text-text-muted"><span>Поворот</span><span>{{ layerRotate }}°</span></div>
                    <input type="range" min="-180" max="180" step="1" :value="layerRotate"
                      @input="setLayerRotate($event.target.value)" class="w-full accent-brand-blue" />
                  </label>
                </div>
                <div class="grid grid-cols-2 gap-2">
                  <label class="block">
                    <div class="flex justify-between text-[9px] text-text-muted"><span>Прозрачность</span><span>{{ Number(styleValue(selectedLayerMeta.style, 'opacity') || 1).toFixed(2) }}</span></div>
                    <input type="range" min="0" max="1" step="0.01" :value="Number(styleValue(selectedLayerMeta.style, 'opacity') || 1)"
                      @input="setLayerOpacity($event.target.value)" class="w-full accent-brand-blue" />
                  </label>
                  <label class="block">
                    <div class="flex justify-between text-[9px] text-text-muted"><span>Z-index</span><span>{{ layerNum('z-index', 10, '') }}</span></div>
                    <input type="range" min="0" max="100" step="1" :value="layerNum('z-index', 10, '')"
                      @input="setLayerNum('z-index', $event.target.value, '')" class="w-full accent-brand-blue" />
                  </label>
                </div>
              </div>
              <label v-if="(selectedLayerObject?.views || []).length > 1" class="block text-[9px] text-text-muted">
                view
                <select :value="selectedLayerMeta.view" @change="updateLayerView($event.target.value)"
                  class="mt-0.5 w-full rounded border border-text-muted/30 bg-bg-surface px-2 py-1 text-xs text-text-primary">
                  <option value="">default</option>
                  <option v-for="v in selectedLayerObject.views" :key="v" :value="v">{{ v }}</option>
                </select>
              </label>
              <div class="flex gap-2 pt-1">
                <button class="flex-1 rounded border border-text-muted/40 px-2 py-1 text-[10px] text-text-secondary hover:bg-bg-surface" @click="duplicateLayer">Дублировать</button>
                <button class="flex-1 rounded border border-red-400/40 px-2 py-1 text-[10px] text-red-300 hover:bg-red-500/10" @click="removeLayer">Удалить</button>
              </div>
            </div>
          </div>

          <div v-else-if="activeTab === 'cues'" class="h-full flex flex-col gap-2">
            <div class="relative h-10 shrink-0 rounded-md border border-text-muted/30 bg-bg-base cursor-crosshair" @click="seekFromCueBar">
              <div class="absolute top-0 bottom-0 w-px bg-white/50" :style="{ left: previewPercent + '%' }"></div>
              <div
                v-for="(c, i) in form.cues" :key="i"
                class="absolute top-1 bottom-1 w-1.5 -translate-x-1/2 rounded-full cursor-pointer"
                :class="selectedCue === i ? 'bg-brand-light-blue' : 'bg-brand-blue/70'"
                :style="{ left: cuePercent(c) + '%' }"
                @click.stop="selectedCue = i"
              ></div>
            </div>

            <div class="flex items-center justify-between shrink-0">
              <p class="text-[10px] text-text-muted">Ключей: {{ form.cues.length }} · время сцены {{ form.duration }} мс</p>
              <button class="rounded-md bg-brand-blue px-2.5 py-1 text-[10px] font-bold text-white" @click="addCue">+ ключ</button>
            </div>

            <div class="flex-1 min-h-0 overflow-y-auto space-y-2 pr-1">
              <div
                v-for="(c, i) in form.cues" :key="i"
                class="rounded-lg border bg-bg-base p-2 space-y-1.5"
                :class="selectedCue === i ? 'border-brand-blue/60' : 'border-text-muted/30'"
                @click="selectedCue = i"
              >
                <div class="flex items-center justify-between text-[10px]">
                  <span class="font-mono text-text-muted">#{{ i + 1 }}</span>
                  <span class="font-mono text-brand-light-blue">{{ c.at }} ms</span>
                  <button class="text-red-300 hover:text-red-200 px-1" @click.stop="removeCue(i)">×</button>
                </div>
                <input type="range" min="0" :max="Math.max(1, form.duration)" step="50" :value="c.at"
                  @input="setCueTime(i, $event.target.value)" class="w-full accent-brand-blue" />
                <input :value="cueSetText(c)" @input="setCueSet(i, $event.target.value)"
                  placeholder="speed=3, brake=true"
                  class="w-full rounded border border-text-muted/30 bg-bg-surface px-2 py-1 font-mono text-[11px] text-text-primary" />
              </div>
              <p v-if="!form.cues.length" class="text-xs text-text-muted py-4">
                Нет ключей. Сцена использует значения по умолчанию из своего JS.
                Добавь ключ, чтобы включить/ускорить/остановить механизм.
              </p>
            </div>
          </div>

          <div v-else-if="activeTab === 'media'" class="h-full overflow-y-auto space-y-3 pr-1">
            <div class="rounded-lg border border-text-muted/30 bg-bg-base p-3 space-y-2">
              <div class="text-sm font-bold text-text-primary">Монитор · картинка</div>
              <div v-if="parsedProps.monitor_media" class="text-[10px] font-mono text-brand-light-blue break-all">{{ parsedProps.monitor_media }}</div>
              <input type="file" accept="image/*" class="block w-full text-[11px] text-text-secondary" @change="onMediaFile($event, 'monitor_media')" />
              <div class="flex gap-2">
                <input :value="parsedProps.monitor_media || ''" @input="setProp('monitor_media', $event.target.value)"
                  placeholder="/media/... или https://..."
                  class="flex-1 rounded border border-text-muted/30 bg-bg-surface px-2 py-1 text-[11px] text-text-primary" />
                <button class="rounded border border-text-muted/40 px-2 py-1 text-[10px] text-text-secondary" @click="setProp('monitor_media', '')">Очистить</button>
              </div>
            </div>

            <div class="rounded-lg border border-text-muted/30 bg-bg-base p-3 space-y-2">
              <div class="text-sm font-bold text-text-primary">Монитор · видео</div>
              <div v-if="parsedProps.monitor_video" class="text-[10px] font-mono text-brand-light-blue break-all">{{ parsedProps.monitor_video }}</div>
              <input type="file" accept="video/*" class="block w-full text-[11px] text-text-secondary" @change="onMediaFile($event, 'monitor_video')" />
              <div class="flex gap-2">
                <input :value="parsedProps.monitor_video || ''" @input="setProp('monitor_video', $event.target.value)"
                  placeholder="/media/... или https://..."
                  class="flex-1 rounded border border-text-muted/30 bg-bg-surface px-2 py-1 text-[11px] text-text-primary" />
                <button class="rounded border border-text-muted/40 px-2 py-1 text-[10px] text-text-secondary" @click="setProp('monitor_video', '')">Очистить</button>
              </div>
            </div>

            <p v-if="mediaBusy" class="text-[11px] text-brand-light-blue">Загрузка…</p>
            <p v-if="mediaError" class="text-[11px] text-red-300">{{ mediaError }}</p>
            <p class="text-[10px] text-text-muted">
              Ключи (Cues) могут менять медиа по ходу сцены:
              <code class="text-brand-light-blue">monitor_media=/media/...</code>.
            </p>
          </div>

          <CodeEditor v-else-if="activeTab === 'html'" v-model="form.code.html" language="html" />

          <CodeEditor v-else-if="activeTab === 'css'" v-model="form.code.css" language="css" />

          <CodeEditor v-else-if="activeTab === 'js'" v-model="form.code.js" language="js" />

          <div v-else-if="activeTab === 'props'" class="h-full flex flex-col gap-2">
            <textarea v-model="propsText" spellcheck="false"
              class="flex-1 w-full resize-none rounded-lg border border-text-muted/30 bg-bg-base p-3 font-mono text-[12px] leading-relaxed text-text-primary outline-none focus:border-brand-blue"
              placeholder="{&#10;  &quot;title&quot;: &quot;Привет&quot;&#10;}"></textarea>
            <p class="text-[10px] text-text-muted">Параметры сцены. Доступны в коде как <code class="text-brand-light-blue">window.__sceneProps</code>.</p>
          </div>

          <div v-else class="h-full overflow-y-auto rounded-lg border border-text-muted/30 bg-bg-base p-3 text-xs text-text-secondary space-y-2">
            <div><span class="text-text-muted">ID:</span> {{ scene?.slide_id }}</div>
            <div><span class="text-text-muted">Компонент:</span> __scene__</div>
            <div><span class="text-text-muted">Порядок:</span> {{ scene?.order_index }}</div>
            <div class="space-y-1">
              <div class="flex justify-between text-[10px]"><span class="text-text-muted">Старт сцены</span><span>{{ form.start_time }} мс</span></div>
              <input type="range" min="0" max="120000" step="100" v-model.number="form.start_time" class="w-full accent-brand-blue" />
            </div>
            <div class="space-y-1">
              <div class="flex justify-between text-[10px]"><span class="text-text-muted">Длительность</span><span>{{ form.duration }} мс</span></div>
              <input type="range" min="500" max="20000" step="100" v-model.number="form.duration" class="w-full accent-brand-blue" />
            </div>
            <div v-if="(activeEnvData?.views || []).length" class="flex items-center gap-2 pt-1">
              <span class="text-text-muted">Вид мира:</span>
              <select v-model="form.view" class="rounded-md border border-text-muted/40 bg-bg-base px-2 py-1 text-xs text-text-primary">
                <option v-for="v in activeEnvData.views" :key="v" :value="v">{{ v }}</option>
              </select>
            </div>
            <div><span class="text-text-muted">Мир:</span> {{ activeEnvData?.title || '—' }}</div>
            <div class="pt-2 text-[10px] leading-relaxed text-text-muted">
              Контракт: <code class="text-brand-light-blue">window.scene.seek(t)</code>.
              Никаких requestAnimationFrame, Date.now и бесконечных CSS-анимаций.
              Время приходит только из таймлайна.
            </div>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed, defineAsyncComponent, onMounted, onUnmounted, ref, watch } from 'vue'
import SceneHost from './SceneHost.vue'
const CodeEditor = defineAsyncComponent(() => import('./CodeEditor.vue'))
import { DEMO_SCENE, normalizeScenePayload } from './demoScene'
import { fetchSceneCharacters, fetchSceneEnvironments, fetchSceneObjects, fetchSceneTemplates, fetchSceneTemplate, fetchTextToVisemes, uploadMedia } from '../services/api'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  scene: { type: Object, default: null },
  presentationId: { type: Number, default: 0 },
})

const emit = defineEmits(['close', 'save', 'delete'])

const editorTheme = {
  '--bg-base': '#0B1322',
  '--bg-base-rgb': '11 19 34',
  '--bg-surface': '#152033',
  '--bg-surface-rgb': '21 32 51',
  '--bg-surface-hover': '#1F2D44',
  '--bg-hover': '#152033',
  '--bg-hover-rgb': '31 45 68',
  '--text-primary': '#F8FAFC',
  '--text-primary-rgb': '248 250 252',
  '--text-secondary': '#94A3B8',
  '--text-secondary-rgb': '148 163 184',
  '--text-muted': '#64748B',
  '--text-muted-rgb': '100 116 139',
  '--brand-blue': '#2563EB',
  '--brand-blue-rgb': '37 99 235',
  '--brand-light-blue': '#38BDF8',
  '--brand-light-blue-rgb': '56 189 248',
  '--brand-green': '#10B981',
  '--brand-green-rgb': '16 185 129',
  '--color-primary': '#2563EB',
  '--color-primary-rgb': '37 99 235',
  '--color-secondary': '#38BDF8',
  '--color-secondary-rgb': '56 189 248',
}

const tabs = [
  { id: 'templates', label: 'Scenes' },
  { id: 'environments', label: 'Worlds' },
  { id: 'objects', label: 'Objects' },
  { id: 'characters', label: 'Characters' },
  { id: 'layers', label: 'Layers' },
  { id: 'cues', label: 'Cues' },
  { id: 'media', label: 'Media' },
  { id: 'html', label: 'HTML' },
  { id: 'css', label: 'CSS' },
  { id: 'js', label: 'JS' },
  { id: 'props', label: 'Props' },
  { id: 'info', label: 'Info' },
]

const activeTab = ref('html')
const previewTime = ref(0)
const previewPlaying = ref(false)
const previewError = ref('')
const propsText = ref('{}')
const jsonError = ref('')
const templates = ref([])
const environments = ref([])
const objects = ref([])
const characters = ref([])
const characterLine = ref('')
const characterBusy = ref(false)
const libraryError = ref('')
const activeEnvironment = ref('')
const showAllObjects = ref(false)
const compatWarning = ref('')
const mediaBusy = ref(false)
const mediaError = ref('')
const selectedLayer = ref(0)
const selectedCue = ref(0)
const sceneHostRef = ref(null)

// ── 3D avatar panel ────────────────────────────────────────────────────────
const clipOptions = ['Neutral_Idle', 'Idle', 'Talking', 'Thinking', 'Look_Around', 'Standing_Idle', 'Standing_Greeting']
const boneOptions = ['Head', 'Neck', 'Spine', 'Spine1', 'Spine2', 'Hips', 'RightArm', 'RightForeArm', 'RightHand', 'LeftArm', 'LeftForeArm', 'LeftHand', 'LeftUpLeg', 'RightUpLeg', 'LeftLeg', 'RightLeg']
const gestureOptions = [
  { id: 'wave', label: 'Помахать' },
  { id: 'point', label: 'Указать' },
  { id: 'nod', label: 'Кивнуть' },
  { id: 'shrug', label: 'Плечи' },
  { id: 'think', label: 'Задуматься' },
  { id: 'clap', label: 'Хлопать' },
]
const isAvatarScene = computed(() => /av-canvas/.test(String(form.value.code.html || '')))
const avatar = ref({
  preset: 'bust', idleClip: 'Neutral_Idle', talkClip: 'Talking', talk_weight: 0.4,
  mood: 'neutral', gaze: { x: 0, y: 0 }, visemes: [], gestures: [], pose: {}, pose_keys: [],
  headline: '', kicker: '3D STUDIO',
})
const avatarLine = ref('')
const avatarBusy = ref(false)
const avatarBone = ref('RightArm')
const poseAngles = ref({ x: 0, y: 0, z: 0 })

function syncAvatarFromProps() {
  if (!isAvatarScene.value) return
  let p = {}
  try { p = JSON.parse(propsText.value || '{}') } catch (e) { p = {} }
  avatar.value = {
    preset: p.preset || 'bust',
    idleClip: p.idleClip || 'Neutral_Idle',
    talkClip: p.talkClip || 'Talking',
    talk_weight: p.talk_weight !== undefined ? Number(p.talk_weight) : 0.4,
    mood: p.mood || 'neutral',
    gaze: { x: Number(p.gaze?.x) || 0, y: Number(p.gaze?.y) || 0 },
    visemes: Array.isArray(p.visemes) ? p.visemes.slice() : [],
    gestures: Array.isArray(p.gestures) ? p.gestures.slice() : [],
    pose: p.pose && typeof p.pose === 'object' ? { ...p.pose } : {},
    pose_keys: Array.isArray(p.pose_keys) ? p.pose_keys.slice() : [],
    headline: p.headline || '',
    kicker: p.kicker || '3D STUDIO',
  }
  avatarLine.value = p.spoken || ''
  loadBonePose()
}

function postAvatar(kind) {
  const a = avatar.value
  const map = {
    preset: ['avatar-preset', { preset: a.preset }],
    clips: ['avatar-clips', { clips: { idle: a.idleClip, talk: a.talkClip, talkWeight: a.talk_weight } }],
    mood: ['avatar-mood', { mood: a.mood }],
    gaze: ['avatar-gaze', { gaze: { x: a.gaze.x, y: a.gaze.y } }],
    visemes: ['avatar-visemes', { visemes: a.visemes }],
    gestures: ['avatar-gestures', { gestures: a.gestures }],
    pose: ['avatar-pose', { pose: a.pose }],
    'pose-keys': ['avatar-pose-keys', { keys: a.pose_keys }],
    text: ['avatar-text', { headline: a.headline, kicker: a.kicker }],
  }
  const item = map[kind]
  if (item) sceneHostRef.value?.post(item[0], item[1])
}

async function speakAvatar() {
  const line = String(avatarLine.value || '').trim()
  if (!line) { clearVisemes(); return }
  avatarBusy.value = true
  try {
    const end = Math.min(6000, Math.max(1400, Number(form.value.duration) - 600))
    const visemes = await fetchTextToVisemes(line, 700, end)
    avatar.value.visemes = Array.isArray(visemes) ? visemes : []
    postAvatar('visemes')
  } catch (e) {
    libraryError.value = e?.message || 'Не удалось получить виземы'
  } finally {
    avatarBusy.value = false
  }
}

function clearVisemes() {
  avatar.value.visemes = []
  postAvatar('visemes')
}

function addGesture(id) {
  avatar.value.gestures = avatar.value.gestures.concat([{ at: Math.round(previewTime.value), type: id }])
  avatar.value.gestures.sort((a, b) => (a.at || 0) - (b.at || 0))
  postAvatar('gestures')
}

function removeGesture(i) {
  avatar.value.gestures.splice(i, 1)
  postAvatar('gestures')
}

function loadBonePose() {
  const v = avatar.value.pose[avatarBone.value] || [0, 0, 0]
  poseAngles.value = { x: Number(v[0]) || 0, y: Number(v[1]) || 0, z: Number(v[2]) || 0 }
}

function applyPoseSlider() {
  avatar.value.pose[avatarBone.value] = [poseAngles.value.x, poseAngles.value.y, poseAngles.value.z]
  postAvatar('pose')
}

function resetBonePose() {
  avatar.value.pose[avatarBone.value] = [0, 0, 0]
  poseAngles.value = { x: 0, y: 0, z: 0 }
  postAvatar('pose')
}

function addPoseKey() {
  const key = {
    at: Math.round(previewTime.value),
    bone: avatarBone.value,
    x: poseAngles.value.x, y: poseAngles.value.y, z: poseAngles.value.z,
  }
  avatar.value.pose_keys = avatar.value.pose_keys.concat([key]).sort((a, b) => (a.at || 0) - (b.at || 0))
  avatar.value.pose[avatarBone.value] = [0, 0, 0]
  poseAngles.value = { x: 0, y: 0, z: 0 }
  postAvatar('pose')
  postAvatar('pose-keys')
}

function removePoseKey(i) {
  avatar.value.pose_keys.splice(i, 1)
  postAvatar('pose-keys')
}

function avatarPropsPatch(p) {
  const a = avatar.value
  p.preset = a.preset
  p.idleClip = a.idleClip
  p.talkClip = a.talkClip
  p.talk_weight = a.talk_weight
  p.mood = a.mood
  p.gaze = { x: a.gaze.x, y: a.gaze.y }
  p.visemes = a.visemes
  p.gestures = a.gestures
  p.pose = a.pose
  p.pose_keys = a.pose_keys
  p.spoken = avatarLine.value
  return p
}

function applyAvatarProps() {
  let p = {}
  try { p = JSON.parse(propsText.value || '{}') } catch (e) { p = {} }
  propsText.value = JSON.stringify(avatarPropsPatch(p), null, 2)
}

async function openAvatarTemplate() {
  try {
    const t = await fetchSceneTemplate('character-3d')
    if (!t) return
    applyTemplate(t)
    activeTab.value = 'avatar'
    syncAvatarFromProps()
  } catch (e) {
    libraryError.value = e?.message || 'Не удалось открыть 3D-сцену'
  }
}

const form = ref({
  title: '',
  start_time: 0,
  duration: 5000,
  code: { html: '', css: '', js: '' },
  props_schema: {},
  view: '',
  cues: [],
  status: 'draft',
})

let previewTimer = null

function resetFromScene(scene) {
  const raw = scene?.data?.payload || {}
  const p = normalizeScenePayload({
    code: scene?.code || raw.code || {},
    props: scene?.props || raw.props || {},
    props_schema: scene?.props_schema || raw.props_schema || {},
    duration: scene?.duration ?? raw.duration,
  })
  form.value = {
    title: scene?.title || 'Новая сцена',
    start_time: Number(scene?.start_time) || 0,
    duration: Number(p.duration) || DEMO_SCENE.duration,
    code: { ...p.code },
    props_schema: scene?.props_schema || p.props_schema || {},
    view: scene?.view || p.view || '',
    cues: Array.isArray(p.cues) ? p.cues.map((c) => ({ at: Number(c.at) || 0, set: { ...(c.set || {}) } })) : [],
    status: p.status || 'draft',
  }
  form.value.code.html = ensureLayerIds(form.value.code.html)
  propsText.value = JSON.stringify(p.props || {}, null, 2)
  syncAvatarFromProps()
  const envMatch = String(p.code.html || '').match(/env-([a-z-]+)/)
  activeEnvironment.value = envMatch ? envMatch[1] : ''
  previewTime.value = Math.min(1200, form.value.duration)
  previewPlaying.value = false
  previewError.value = ''
  jsonError.value = ''
  activeTab.value = 'html'
  selectedLayer.value = 0
  selectedCue.value = 0
  stopPreview()
}

watch(() => props.scene, (s) => { if (s) resetFromScene(s) }, { immediate: true })
watch(() => props.isOpen, (open) => {
  if (!open) { stopPreview(); previewPlaying.value = false }
  else if (!templates.value.length || libraryError.value) loadLibrary()
})

const activeEnvData = computed(() =>
  environments.value.find((e) => e.slug === activeEnvironment.value) || null,
)

const compatibleObjects = computed(() => {
  if (!activeEnvironment.value) return objects.value
  const domain = activeEnvData.value?.domain
  return objects.value.filter((o) => {
    if (Array.isArray(o.environments) && o.environments.length) {
      return o.environments.includes(activeEnvironment.value)
    }
    return Array.isArray(o.domain) && domain ? o.domain.includes(domain) : true
  })
})

const visibleObjects = computed(() =>
  showAllObjects.value ? objects.value : compatibleObjects.value,
)

function sceneObjects() {
  try {
    const doc = new DOMParser().parseFromString(form.value.code.html || '', 'text/html')
    return Array.from(doc.body.querySelectorAll('*')).filter((el) =>
      Array.from(el.classList || []).some((c) => c.startsWith('obj-')),
    )
  } catch (e) {
    return []
  }
}

const layerList = computed(() => {
  const els = sceneObjects()
  return els.map((el, i) => {
    const cls = Array.from(el.classList || [])
    return {
      index: i,
      id: el.dataset.layerId || `layer-${i}`,
      slug: (cls.find((c) => c.startsWith('obj-')) || 'obj').replace('obj-', ''),
      view: (cls.find((c) => c.startsWith('view-')) || '').replace('view-', ''),
      style: el.getAttribute('style') || '',
    }
  })
})

const selectedLayerMeta = computed(() => layerList.value[selectedLayer.value] || null)

const selectedLayerObject = computed(() =>
  selectedLayerMeta.value ? objects.value.find((o) => o.slug === selectedLayerMeta.value.slug) : null,
)

function styleValue(style, key) {
  const m = String(style || '').match(new RegExp('(?:^|;)\\s*' + key + '\\s*:\\s*([^;]+)'))
  return m ? m[1].trim() : ''
}

function ensureLayerIds(html) {
  try {
    const doc = new DOMParser().parseFromString(html || '', 'text/html')
    const els = Array.from(doc.body.querySelectorAll('*')).filter((el) =>
      Array.from(el.classList || []).some((c) => c.startsWith('obj-')),
    )
    els.forEach((el, i) => {
      if (!el.dataset.layerId) el.dataset.layerId = `layer-${i}`
    })
    return doc.body.innerHTML
  } catch (e) {
    return html
  }
}

function mutateLayer(fn) {
  const doc = new DOMParser().parseFromString(form.value.code.html || '', 'text/html')
  const els = Array.from(doc.body.querySelectorAll('*')).filter((el) =>
    Array.from(el.classList || []).some((c) => c.startsWith('obj-')),
  )
  const el = els[selectedLayer.value]
  if (!el) return
  fn(el, doc)
  els.forEach((item, i) => {
    if (!item.dataset.layerId) item.dataset.layerId = `layer-${i}`
  })
  form.value.code.html = doc.body.innerHTML
}

function patchLayer(styles) {
  const id = selectedLayerMeta.value?.id
  mutateLayer((el) => {
    for (const [key, value] of Object.entries(styles || {})) {
      if (value === '' || value === null || value === undefined) el.style.removeProperty(key)
      else el.style.setProperty(key, String(value))
    }
  })
  if (id && sceneHostRef.value?.patchObject) sceneHostRef.value.patchObject(id, styles)
}

function updateLayerStyle(key, value) {
  patchLayer({ [key]: value })
}

function styleParts(style, key, fallback, defaultUnit) {
  const raw = styleValue(style, key)
  const m = raw.match(/^(-?[\d.]+)\s*([a-z%]*)$/i)
  return {
    num: m ? Number(m[1]) : fallback,
    unit: m ? (m[2] || defaultUnit || '') : (defaultUnit || ''),
  }
}

function layerNum(key, fallback, unit) {
  return styleParts(selectedLayerMeta.value?.style, key, fallback, unit).num
}

function layerUnit(key, unit) {
  return styleParts(selectedLayerMeta.value?.style, key, 0, unit).unit || unit
}

function setLayerNum(key, value, unit) {
  const suffix = unit === '%' || unit === 'vmin' ? (layerUnit(key, unit) || unit) : ''
  patchLayer({ [key]: `${value}${suffix}` })
}

const layerTransform = computed(() => styleValue(selectedLayerMeta.value?.style, 'transform'))
const layerScale = computed(() => {
  const m = layerTransform.value.match(/scale\(([^)]+)\)/)
  return m ? Number(m[1]) || 1 : 1
})
const layerRotate = computed(() => {
  const m = layerTransform.value.match(/rotate\(([-\d.]+)deg\)/)
  return m ? Number(m[1]) || 0 : 0
})

function setLayerScale(value) {
  patchLayer({ transform: `scale(${Number(value) || 1}) rotate(${layerRotate.value}deg)` })
}

function setLayerRotate(value) {
  patchLayer({ transform: `scale(${layerScale.value}) rotate(${Number(value) || 0}deg)` })
}

function setLayerOpacity(value) {
  patchLayer({ opacity: String(value) })
}

function updateLayerView(view) {
  mutateLayer((el) => {
    Array.from(el.classList || [])
      .filter((c) => c.startsWith('view-'))
      .forEach((c) => el.classList.remove(c))
    if (view) el.classList.add(`view-${view}`)
  })
}

function removeLayer() {
  mutateLayer((el) => el.remove())
  selectedLayer.value = Math.max(0, Math.min(selectedLayer.value, layerList.value.length - 1))
}

function duplicateLayer() {
  mutateLayer((el) => {
    const clone = el.cloneNode(true)
    if (el.parentNode) el.parentNode.appendChild(clone)
  })
}

const previewPercent = computed(() =>
  Math.max(0, Math.min(100, (previewTime.value / Math.max(1, form.value.duration)) * 100)),
)

function cuePercent(cue) {
  return Math.max(0, Math.min(100, (Number(cue.at) || 0) / Math.max(1, form.value.duration) * 100))
}

function cueSetText(cue) {
  return Object.entries(cue.set || {})
    .map(([k, v]) => `${k}=${typeof v === 'string' ? v : JSON.stringify(v)}`)
    .join(', ')
}

function parseSet(text) {
  const out = {}
  String(text || '').split(',').forEach((part) => {
    const idx = part.indexOf('=')
    if (idx <= 0) return
    const key = part.slice(0, idx).trim()
    let value = part.slice(idx + 1).trim()
    try { value = JSON.parse(value) } catch (e) { /* keep string */ }
    if (key) out[key] = value
  })
  return out
}

function setCueSet(index, text) {
  if (form.value.cues[index]) form.value.cues[index].set = parseSet(text)
}

function setCueTime(index, value) {
  if (form.value.cues[index]) form.value.cues[index].at = Number(value) || 0
}

function addCue() {
  form.value.cues.push({ at: Math.round(previewTime.value), set: { speed: 1 } })
  form.value.cues.sort((a, b) => (a.at || 0) - (b.at || 0))
  selectedCue.value = form.value.cues.length - 1
}

function removeCue(index) {
  form.value.cues.splice(index, 1)
  selectedCue.value = Math.max(0, Math.min(selectedCue.value, form.value.cues.length - 1))
}

function seekFromCueBar(event) {
  const rect = event.currentTarget.getBoundingClientRect()
  const ratio = Math.max(0, Math.min(1, (event.clientX - rect.left) / Math.max(1, rect.width)))
  previewTime.value = Math.round(ratio * form.value.duration)
}

function setProp(key, value) {
  let obj = {}
  try { obj = JSON.parse(propsText.value || '{}') } catch (e) { obj = {} }
  if (!value) delete obj[key]
  else obj[key] = value
  propsText.value = JSON.stringify(obj, null, 2)
}

async function onMediaFile(event, key) {
  const file = event.target.files && event.target.files[0]
  if (!file) return
  mediaBusy.value = true
  mediaError.value = ''
  try {
    const res = await uploadMedia(props.presentationId, file, key === 'monitor_video' ? 'video' : 'image')
    setProp(key, res.file_path || res.url || '')
  } catch (err) {
    mediaError.value = err?.message || 'Не удалось загрузить медиа'
  } finally {
    mediaBusy.value = false
    event.target.value = ''
  }
}

const parsedProps = computed(() => {
  try {
    const v = JSON.parse(propsText.value || '{}')
    jsonError.value = ''
    return v && typeof v === 'object' ? v : {}
  } catch (e) {
    jsonError.value = e.message
    return {}
  }
})

function togglePreview() {
  if (previewPlaying.value) stopPreview()
  else startPreview()
}

function startPreview() {
  stopPreview()
  previewPlaying.value = true
  if (previewTime.value >= form.value.duration) previewTime.value = 0
  let last = performance.now()
  previewTimer = setInterval(() => {
    const now = performance.now()
    const dt = now - last
    last = now
    previewTime.value = Math.min(form.value.duration, previewTime.value + dt)
    if (previewTime.value >= form.value.duration) {
      previewTime.value = form.value.duration
      stopPreview()
    }
  }, 16)
}

function stopPreview() {
  if (previewTimer) clearInterval(previewTimer)
  previewTimer = null
  previewPlaying.value = false
}

function applyTemplate(t) {
  if (!t) return
  form.value.code = { ...(t.code || {}) }
  form.value.code.html = ensureLayerIds(form.value.code.html)
  form.value.duration = Number(t.duration) || form.value.duration
  form.value.props_schema = t.props_schema || {}
  activeEnvironment.value = t.environment || ''
  form.value.view = t.view || activeEnvData.value?.default_view || ''
  form.value.cues = Array.isArray(t.cues) ? t.cues.map((c) => ({ at: Number(c.at) || 0, set: { ...(c.set || {}) } })) : []
  form.value.status = 'draft' 
  propsText.value = JSON.stringify(t.default_props || {}, null, 2)
  syncAvatarFromProps()
  previewTime.value = Math.min(1200, form.value.duration)
  previewError.value = ''
}

function applyEnvironment(e) {
  if (!e) return
  form.value.code = {
    html: `<div class="scene">\n${e.html || ''}\n</div>`,
    css: e.css || '',
    js: 'window.scene = { seek(t) {} };',
  }
  form.value.code.html = ensureLayerIds(form.value.code.html)
  form.value.duration = 5000
  form.value.props_schema = {}
  activeEnvironment.value = e.slug || ''
  form.value.view = e.default_view || ''
  form.value.cues = []
  compatWarning.value = ''
  propsText.value = '{}'
  previewTime.value = 1200
  previewError.value = ''
  activeTab.value = 'html'
}

function insertObject(o) {
  if (!o) return
  compatWarning.value = ''
  if (activeEnvironment.value && !compatibleObjects.value.some((x) => x.slug === o.slug)) {
    compatWarning.value = `${o.title} не предназначен для мира «${activeEnvData.value?.title || activeEnvironment.value}». Вставлено принудительно.`
  }
  form.value.code.html = (form.value.code.html || '') + '\n' + (o.html || '')
  form.value.code.css = (form.value.code.css || '') + '\n' + (o.css || '')
  form.value.code.js = (form.value.code.js || '') + '\n' + (o.js || '')
  activeTab.value = 'html'
}

async function openCharacter(c) {
  if (!c) return
  characterBusy.value = true
  try {
    if (c.template) {
      const t = await fetchSceneTemplate(c.template)
      if (t) {
        const line = String(characterLine.value || '').trim()
        if (line) {
          const visemes = await fetchTextToVisemes(line, 700, 6000)
          t.default_props = {
            ...(t.default_props || {}),
            headline: line.length > 48 ? line.slice(0, 47) + '…' : line,
            visemes,
          }
          t.duration = Math.max(7000, Number(t.duration) || 7000)
        }
        applyTemplate(t)
        activeTab.value = 'html'
        return
      }
    }
  } catch (e) {
    libraryError.value = e?.message || 'Не удалось открыть персонажа'
  } finally {
    characterBusy.value = false
  }
  const o = objects.value.find((x) => x.slug === c.slug)
  if (o) insertObject(o)
}

async function loadLibrary() {
  try {
    const [t, e, o, ch] = await Promise.all([
      fetchSceneTemplates(),
      fetchSceneEnvironments(),
      fetchSceneObjects(),
      fetchSceneCharacters(),
    ])
    templates.value = Array.isArray(t) ? t : []
    environments.value = Array.isArray(e) ? e : []
    objects.value = Array.isArray(o) ? o : []
    characters.value = Array.isArray(ch) ? ch : []
  } catch (e) {
    libraryError.value = e?.message || 'Не удалось загрузить библиотеку'
  }
}

onMounted(loadLibrary)

async function loadDemo() {
  try {
    const t = await fetchSceneTemplate('forest-drive')
    if (t) { applyTemplate(t); return }
  } catch (e) { /* fallback below */ }
  const local = templates.value.find((x) => x.slug === 'forest-drive')
  if (local) { applyTemplate(local); return }
  form.value.code = { ...DEMO_SCENE.code }
  form.value.props_schema = {}
  propsText.value = JSON.stringify(DEMO_SCENE.props || {}, null, 2)
  previewTime.value = Math.min(1200, form.value.duration)
  previewError.value = ''
}

function save() {
  if (!props.scene) return
  let p = {}
  try { p = JSON.parse(propsText.value || '{}') } catch (e) { jsonError.value = e.message; return }
  if (isAvatarScene.value) p = avatarPropsPatch(p)
  emit('save', {
    slide_id: props.scene.slide_id,
    component: '__scene__',
    start_time: Number(form.value.start_time) || 0,
    title: form.value.title || '',
    subtitle: '',
    layout: 'col',
    order_index: props.scene.order_index || 0,
    kind: 'scene',
    duration: Number(form.value.duration) || 5000,
    code: { ...form.value.code },
    props: p,
    props_schema: form.value.props_schema || {},
    view: form.value.view || '',
    cues: form.value.cues,
    status: form.value.status || 'draft',
    track: props.scene.track || 'main',
    z_index: props.scene.z_index ?? 0,
    data: {
      payload: {
        kind: 'scene',
        code: { ...form.value.code },
        props: p,
        props_schema: form.value.props_schema || {},
        view: form.value.view || '',
        cues: form.value.cues,
        status: form.value.status || 'draft',
        duration: Number(form.value.duration) || 5000,
      },
    },
    events: [],
  })
}

onUnmounted(stopPreview)
</script>
