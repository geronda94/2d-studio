<script setup>
// BRAND KIT проекта: лого, QR, контакты и дефолты компонентов.
// Значения автоматически подставляются в компоненты (напр. OutroSlide), если слайд
// не задал их явно. Меняет только владелец (PUT /projects/{id}/config).
import { ref, onMounted } from 'vue'
import { fetchProjectConfig, updateProjectConfig } from '../../services/api'
import MediaLibraryModal from './MediaLibraryModal.vue'

const props = defineProps({
  projectId: { type: Number, required: true },
  canEdit: { type: Boolean, default: false },
  // Первая презентация проекта — нужна медиатеке (она работает в разрезе презентации).
  presentationId: { type: Number, default: 0 },
})

const loading = ref(true)
const saving = ref(false)
const error = ref('')
const ok = ref('')

const form = ref({
  name: '',
  logo: '',
  qr_code: '',
  qr_data: '',
  telegram: '',
  site: '',
  email: '',
  phone: '',
  whatsapp: '',
  instagram: '',
  youtube: '',
  linkedin: '',
})
const voice = ref({ voice: '', temperature: '', style: '', pace: '', tone: '', scene: '' })
const audio = ref({ bgm: '', volume: '' })
const defaultsJson = ref('{}')

// Медиа-пикер: выбор лого/QR/BGM из медиатеки проекта вместо ручного пути.
const showMediaPicker = ref(false)
const pickTarget = ref(null)
const openPicker = (target) => {
  pickTarget.value = target
  showMediaPicker.value = true
}
const onMediaSelect = (filePath) => {
  if (!filePath) return
  const t = pickTarget.value
  if (t === 'logo') form.value.logo = filePath
  else if (t === 'qr_code') form.value.qr_code = filePath
  else if (t === 'bgm') audio.value.bgm = filePath
  showMediaPicker.value = false
  pickTarget.value = null
}

const applyConfig = (cfg) => {
  const b = cfg.brand || {}
  const c = cfg.contacts || {}
  form.value = {
    name: b.name || '',
    logo: b.logo || '',
    qr_code: b.qr_code || '',
    qr_data: b.qr_data || '',
    telegram: c.telegram || '',
    site: c.site || '',
    email: c.email || '',
    phone: c.phone || '',
    whatsapp: c.whatsapp || '',
    instagram: c.instagram || '',
    youtube: c.youtube || '',
    linkedin: c.linkedin || '',
  }
  const v = cfg.voice || {}
  voice.value = {
    voice: v.voice || '',
    temperature: v.temperature ?? '',
    style: v.style || '',
    pace: v.pace || '',
    tone: v.tone || '',
    scene: v.scene || '',
  }
  const a = cfg.audio || {}
  audio.value = { bgm: a.bgm || '', volume: a.volume ?? '' }
  defaultsJson.value = JSON.stringify(cfg.defaults || {}, null, 2)
}

const load = async () => {
  loading.value = true
  try {
    const d = await fetchProjectConfig(props.projectId)
    applyConfig(d.config || {})
  } catch (e) {
    error.value = e.message || 'Ошибка'
  } finally {
    loading.value = false
  }
}
onMounted(load)

const save = async () => {
  error.value = ''
  ok.value = ''
  let defaults = {}
  try {
    defaults = defaultsJson.value.trim() ? JSON.parse(defaultsJson.value) : {}
  } catch {
    error.value = 'Дефолты: некорректный JSON'
    return
  }
  saving.value = true
  try {
    const clean = (o) => Object.fromEntries(
      Object.entries(o).filter(([, v]) => v !== undefined && v !== null && v !== ''),
    )
    const cfg = {
      brand: clean({
        name: form.value.name,
        logo: form.value.logo,
        qr_code: form.value.qr_code,
        qr_data: form.value.qr_data,
      }),
      contacts: clean({
        telegram: form.value.telegram,
        site: form.value.site,
        email: form.value.email,
        phone: form.value.phone,
        whatsapp: form.value.whatsapp,
        instagram: form.value.instagram,
        youtube: form.value.youtube,
        linkedin: form.value.linkedin,
      }),
      voice: clean({
        voice: voice.value.voice,
        temperature: voice.value.temperature === '' ? undefined : Number(voice.value.temperature),
        style: voice.value.style,
        pace: voice.value.pace,
        tone: voice.value.tone,
        scene: voice.value.scene,
      }),
      audio: clean({
        bgm: audio.value.bgm,
        volume: audio.value.volume === '' ? undefined : Number(audio.value.volume),
      }),
      defaults,
    }
    const res = await updateProjectConfig(props.projectId, cfg)
    applyConfig(res.config || {})
    ok.value = 'Сохранено'
  } catch (e) {
    error.value = e.message || 'Ошибка'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <section class="bg-white rounded-2xl border border-gray-200 p-5 md:p-6">
    <h2 class="text-lg font-bold text-gray-900 mb-1">Бренд проекта</h2>
    <p class="text-sm text-gray-500 mb-4">
      Лого, QR и контакты подставляются в компоненты автоматически (например, OutroSlide),
      если слайд не задал своё. Не нужно дублировать в каждой презентации.
    </p>
    <p v-if="!canEdit" class="text-xs text-amber-600 mb-4">
      Менять бренд проекта может только владелец.
    </p>

    <p v-if="loading" class="text-sm text-gray-400">Загружаю…</p>
    <template v-else>
      <fieldset :disabled="!canEdit" class="border-0 p-0 m-0 min-w-0">
      <h3 class="text-xs font-bold uppercase tracking-wider text-gray-500 mb-3">Бренд</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Название</label>
          <input v-model="form.name" class="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500" />
        </div>
        <div>
          <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Лого (URL / путь)</label>
          <div class="flex gap-2">
            <input v-model="form.logo" placeholder="/media/logo.png" class="flex-1 min-w-0 border border-gray-200 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500" />
            <button v-if="presentationId" type="button" @click="openPicker('logo')" class="px-3 rounded-xl border border-gray-200 text-xs font-semibold text-gray-600 hover:bg-gray-50 shrink-0">Выбрать</button>
          </div>
        </div>
        <div>
          <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">QR-код (URL / путь, опц.)</label>
          <div class="flex gap-2">
            <input v-model="form.qr_code" placeholder="пусто — сгенерируем из ссылки" class="flex-1 min-w-0 border border-gray-200 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500" />
            <button v-if="presentationId" type="button" @click="openPicker('qr_code')" class="px-3 rounded-xl border border-gray-200 text-xs font-semibold text-gray-600 hover:bg-gray-50 shrink-0">Выбрать</button>
          </div>
        </div>
        <div>
          <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Ссылка для QR (авто)</label>
          <input v-model="form.qr_data" placeholder="https://t.me/… или сайт" class="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500" />
        </div>
      </div>
      <div v-if="projectId && !form.qr_code && (form.qr_data || form.telegram || form.site)" class="mt-3 flex items-center gap-3">
        <img
          :key="`${form.qr_data}|${form.telegram}|${form.site}`"
          :src="`/api/projects/${projectId}/qr.svg`"
          class="h-20 w-20 rounded-lg border border-gray-200 bg-white p-1"
          alt="Авто-QR"
        />
        <span class="text-[11px] text-gray-400">Так будет выглядеть авто-QR на слайде</span>
      </div>

      <h3 class="text-xs font-bold uppercase tracking-wider text-gray-500 mt-5 mb-3">Контакты</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
        <input v-model="form.telegram" placeholder="Telegram @handle" class="border border-gray-200 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500" />
        <input v-model="form.site" placeholder="Сайт https://…" class="border border-gray-200 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500" />
        <input v-model="form.email" placeholder="Email" class="border border-gray-200 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500" />
      </div>

      <h3 class="text-xs font-bold uppercase tracking-wider text-gray-500 mt-5 mb-3">Соцсети</h3>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <input v-model="form.whatsapp" placeholder="WhatsApp" class="border border-gray-200 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500" />
        <input v-model="form.instagram" placeholder="Instagram" class="border border-gray-200 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500" />
        <input v-model="form.youtube" placeholder="YouTube" class="border border-gray-200 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500" />
        <input v-model="form.linkedin" placeholder="LinkedIn" class="border border-gray-200 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500" />
      </div>

      <h3 class="text-xs font-bold uppercase tracking-wider text-gray-500 mt-5 mb-3">Озвучка (дефолты)</h3>
      <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
        <input v-model="voice.voice" placeholder="Голос (Charon)" class="border border-gray-200 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500" />
        <input v-model="voice.temperature" type="number" step="0.1" min="0" max="2" placeholder="temperature (0.9)" class="border border-gray-200 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500" />
        <input v-model="voice.pace" placeholder="pace" class="border border-gray-200 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500" />
        <input v-model="voice.style" placeholder="style" class="border border-gray-200 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500" />
        <input v-model="voice.tone" placeholder="tone" class="border border-gray-200 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500" />
        <input v-model="voice.scene" placeholder="scene" class="border border-gray-200 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500" />
      </div>

      <h3 class="text-xs font-bold uppercase tracking-wider text-gray-500 mt-5 mb-3">Фоновая музыка</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div class="md:col-span-2 flex gap-2">
          <input v-model="audio.bgm" placeholder="BGM: /media/music.mp3" class="flex-1 min-w-0 border border-gray-200 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500" />
          <button v-if="presentationId" type="button" @click="openPicker('bgm')" class="px-3 rounded-xl border border-gray-200 text-xs font-semibold text-gray-600 hover:bg-gray-50 shrink-0">Выбрать</button>
        </div>
        <input v-model="audio.volume" type="number" step="0.05" min="0" max="1" placeholder="volume 0.15" class="border border-gray-200 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500" />
      </div>
      <p class="text-[11px] text-gray-400 mt-1">BGM подкладывается в новые презентации проекта, если у них ещё нет таймлайна.</p>

      <div class="mt-3 flex flex-wrap gap-4 items-center text-xs">
        <img v-if="form.logo" :src="form.logo" class="h-10 object-contain" alt="logo preview" />
        <img v-if="form.qr_code" :src="form.qr_code" class="h-14 object-contain" alt="qr preview" />
      </div>

      <div class="mt-5">
        <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">
          Дефолты компонентов (JSON)
        </label>
        <textarea
          v-model="defaultsJson"
          rows="6"
          spellcheck="false"
          class="w-full font-mono text-xs border border-gray-200 rounded-xl px-3 py-2 outline-none focus:border-blue-500"
        ></textarea>
        <p class="text-[11px] text-gray-400 mt-1">
          Например: <code v-pre>{"OutroSlide":{"headline":"Подпишись"},"ChatMockupSlide":{"bot_name":"AI-агент"}}</code>
        </p>
      </div>

      </fieldset>
      <p v-if="error" class="text-sm text-red-500 mt-3">{{ error }}</p>
      <p v-if="ok" class="text-sm text-green-600 mt-3">{{ ok }}</p>
      <button v-if="canEdit" @click="save" :disabled="saving"
        class="mt-4 px-4 py-2.5 rounded-xl font-bold text-white bg-blue-600 hover:opacity-90 disabled:opacity-50 text-sm">
        {{ saving ? 'Сохраняю…' : 'Сохранить' }}
      </button>
    </template>

    <MediaLibraryModal
      v-if="presentationId"
      :isOpen="showMediaPicker"
      :presentation-id="presentationId"
      mode="select"
      @close="showMediaPicker = false"
      @select="onMediaSelect"
    />
  </section>
</template>
