<template>
  <div v-if="isOpen" class="fixed inset-0 z-[400] flex items-center justify-center p-2 md:p-0">
    <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="$emit('close')"></div>
    
    <div class="relative bg-bg-base w-full max-w-[95vw] md:max-w-5xl h-[85dvh] rounded-2xl border border-text-muted shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
      
      <!-- Header -->
      <div class="p-6 border-b border-text-muted bg-bg-surface flex flex-col shrink-0 gap-4">
        <div class="flex justify-between items-center">
          <div>
            <h2 class="text-xl font-bold text-text-primary flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-color-secondary"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
              Медиа-библиотека проекта
            </h2>
            <p class="text-text-secondary text-sm mt-1" v-if="mode === 'select'">Кликните на файл, чтобы вставить его путь</p>
            <p class="text-text-secondary text-sm mt-1" v-else>Управление файлами проекта</p>
          </div>
          
          <div class="flex items-center gap-4">
            <button @click="$emit('close')" class="p-2 text-text-secondary hover:text-text-primary transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </button>
          </div>
        </div>
        
        <!-- Tabs -->
        <div class="flex gap-2">
          <button @click="activeTab = 'library'" :class="['px-4 py-2 rounded-lg font-bold text-sm transition-colors', activeTab === 'library' ? 'bg-color-secondary text-white' : 'bg-bg-surface text-text-secondary hover:bg-bg-surface']">
            Мои файлы
          </button>
          <button @click="activeTab = 'search'" :class="['px-4 py-2 rounded-lg font-bold text-sm transition-colors', activeTab === 'search' ? 'bg-color-secondary text-white' : 'bg-bg-surface text-text-secondary hover:bg-bg-surface']">
            Поиск в интернете
          </button>
        </div>
      </div>
      
      <!-- Body -->
      <div class="flex-1 overflow-y-auto bg-bg-base flex flex-col relative" 
           @dragover.prevent="isDragging = true" 
           @dragleave.prevent="isDragging = false" 
           @drop.prevent="handleDrop">
        
        <!-- Dropzone Overlay -->
        <div v-if="isDragging && activeTab === 'library'" class="absolute inset-0 bg-color-secondary/10 border-4 border-dashed border-color-secondary z-10 flex flex-col items-center justify-center backdrop-blur-sm">
          <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-color-secondary mb-4"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
          <h2 class="text-2xl font-bold text-color-secondary">Отпустите файлы для загрузки</h2>
        </div>
        
        <div v-if="activeTab === 'library'" class="flex-1 flex flex-col p-6">
          <div class="flex flex-col md:flex-row gap-4 mb-6 items-start md:items-center justify-between">
            <div class="flex gap-2 w-full md:w-auto min-w-0">
              <div class="flex bg-bg-hover border border-text-muted rounded-xl overflow-x-auto hide-scrollbar max-w-full">
                <button @click="libraryFilter = 'all'" :class="['px-4 py-2 text-sm font-bold transition-colors', libraryFilter === 'all' ? 'bg-color-secondary text-white' : 'text-text-secondary hover:text-text-primary hover:bg-bg-surface']">Все</button>
                <button @click="libraryFilter = 'image'" :class="['px-4 py-2 text-sm font-bold transition-colors', libraryFilter === 'image' ? 'bg-color-secondary text-white' : 'text-text-secondary hover:text-text-primary hover:bg-bg-surface']">Фото</button>
                <button @click="libraryFilter = 'video'" :class="['px-4 py-2 text-sm font-bold transition-colors', libraryFilter === 'video' ? 'bg-color-secondary text-white' : 'text-text-secondary hover:text-text-primary hover:bg-bg-surface']">Видео</button>
                <button @click="libraryFilter = 'audio'" :class="['px-4 py-2 text-sm font-bold transition-colors', libraryFilter === 'audio' ? 'bg-color-secondary text-white' : 'text-text-secondary hover:text-text-primary hover:bg-bg-surface']">Аудио</button>
                <button @click="libraryFilter = 'voice'" :class="['px-4 py-2 text-sm font-bold transition-colors', libraryFilter === 'voice' ? 'bg-color-secondary text-white' : 'text-text-secondary hover:text-text-primary hover:bg-bg-surface']">Голос</button>
                <button @click="libraryFilter = 'sfx'" :class="['px-4 py-2 text-sm font-bold transition-colors', libraryFilter === 'sfx' ? 'bg-color-secondary text-white' : 'text-text-secondary hover:text-text-primary hover:bg-bg-surface']">SFX</button>
                <button @click="libraryFilter = 'ai_voice'" :class="['px-4 py-2 text-sm font-bold transition-colors', libraryFilter === 'ai_voice' ? 'bg-color-secondary text-white' : 'text-text-secondary hover:text-text-primary hover:bg-bg-surface']">ИИ Озвучка</button>
              </div>
            </div>
            
            <div class="flex bg-bg-hover p-1 rounded-xl border border-text-muted shrink-0">
              <button @click="isGlobal = false" :class="['px-4 py-1.5 rounded-lg text-xs font-bold transition-all', !isGlobal ? 'bg-bg-surface text-text-primary shadow-sm' : 'text-text-secondary hover:text-text-primary']">Эта презентация</button>
              <button @click="isGlobal = true" :class="['px-4 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-2', isGlobal ? 'bg-color-secondary text-white shadow-sm' : 'text-text-secondary hover:text-white']">
                <svg v-if="loadingGlobal" class="animate-spin" xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56"></path></svg>
                Весь проект
              </button>
            </div>
          </div>
          <div class="flex flex-col md:flex-row gap-4 mb-6">
            <label class="px-4 py-3 bg-color-success hover:bg-color-success text-white font-bold rounded-xl transition-colors cursor-pointer flex items-center justify-center gap-2 shrink-0" :class="{'opacity-50 pointer-events-none': uploading}">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
              {{ uploading ? 'Загрузка...' : 'Загрузить файл' }}
              <input type="file" class="hidden" @change="handleFileUpload" accept="image/*,audio/*,video/*" multiple />
            </label>
            
            <div class="flex-1 flex flex-col sm:flex-row gap-2 min-w-0">
              <input v-model="manualUrl" type="text" placeholder="Или вставьте URL картинки/видео/аудио..." class="flex-1 min-w-0 bg-bg-hover border border-text-muted rounded-xl px-4 py-3 text-text-primary focus:outline-none focus:border-color-secondary transition-colors" @keyup.enter="handleDownloadUrl">
              <button @click="handleDownloadUrl" :disabled="!manualUrl || isDownloading" class="w-full sm:w-auto px-6 py-3 bg-color-secondary hover:bg-color-primary text-white font-bold rounded-xl transition-colors disabled:opacity-50">
                {{ isDownloading ? '...' : 'Скачать' }}
              </button>
            </div>
          </div>
          
          <div v-if="loadingGlobal && isGlobal" class="flex-1 flex flex-col items-center justify-center text-text-muted min-h-[300px]">
            <svg class="animate-spin mb-3" xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56"></path></svg>
            <p>Загружаю файлы…</p>
          </div>
          <div v-else-if="groupedMediaFiles.length === 0 && libraryFilter === 'all'" class="flex-1 flex flex-col items-center justify-center text-text-muted min-h-[300px]">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" class="mb-4"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
            <p>{{ isGlobal ? 'В этом проекте пока нет медиафайлов.' : 'В этой презентации пока нет медиафайлов.' }}</p>
            <p class="text-sm mt-1">Перетащите файлы сюда или загрузите по ссылке</p>
          </div>
          <div v-else-if="groupedMediaFiles.length === 0" class="flex-1 flex flex-col items-center justify-center text-text-muted min-h-[300px]">
            <p>Нет файлов выбранного типа.</p>
          </div>
          
          <div v-else class="flex-1 flex flex-col">
            <div v-if="activeBatchId" class="mb-4 flex items-center justify-between">
              <button @click="activeBatchId = null" class="px-4 py-2 bg-bg-surface hover:bg-bg-surface text-text-primary rounded-lg text-sm font-bold flex items-center gap-2 transition-colors">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>
                Назад к библиотеке
              </button>
              <button v-if="mode === 'select'" @click="$emit('select-batch', groupedMediaFiles)" class="px-4 py-2 bg-[#A78BFA] hover:bg-[#8B5CF6] text-text-primary rounded-lg text-sm font-bold flex items-center gap-2 transition-colors shadow-lg shadow-[#A78BFA]/30">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
                Вставить весь пакет на таймлайн
              </button>
            </div>
            
            <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
            <div 
              v-for="file in groupedMediaFiles" :key="file.id"
              @click="(mode === 'select' && !file.isBatchFolder) ? $emit('select', file.file_path) : selectFile(file)"
              class="bg-bg-hover border border-text-muted rounded-xl overflow-hidden hover:border-color-secondary transition-all cursor-pointer group flex flex-col relative"
            >
              <!-- Preview -->
              <div class="h-32 bg-black/50 flex items-center justify-center relative overflow-hidden group/preview">
                <img v-if="file.file_type === 'image'" :src="file.file_path" class="w-full h-full object-cover" />
                <div v-else-if="file.file_type === 'audio' || file.file_type === 'voice' || file.file_type === 'ai_voice'" class="text-color-success flex items-center justify-center relative w-full h-full" @click.stop="toggleAudio(file, $event)">
                  <audio :src="file.file_path" preload="metadata" :ref="el => setAudioRef(el, file.id)" @ended="playingAudioId = null"></audio>
                  <svg v-if="playingAudioId !== file.id" xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="transition-transform group-hover/preview:scale-110"><path d="M5 3l14 9-14 9V3z"></path></svg>
                  <svg v-else xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="transition-transform group-hover/preview:scale-110 text-text-primary drop-shadow-[0_0_8px_rgb(var(--text-primary-rgb) / 0.5)]"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg>
                </div>
                <div v-else-if="file.file_type === 'sfx'" class="text-color-warning flex items-center justify-center relative w-full h-full" @click.stop="toggleAudio(file, $event)">
                  <audio :src="file.file_path" preload="metadata" :ref="el => setAudioRef(el, file.id)" @ended="playingAudioId = null"></audio>
                  <svg v-if="playingAudioId !== file.id" xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="transition-transform group-hover/preview:scale-110"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path><path d="M19.07 4.93a10 10 0 0 1 0 14.14"></path></svg>
                  <svg v-else xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="transition-transform group-hover/preview:scale-110 text-text-primary drop-shadow-[0_0_8px_rgb(var(--text-primary-rgb) / 0.5)]"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg>
                </div>
                <div v-else-if="file.file_type === 'video'" class="text-[#A78BFA]">
                  <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg>
                </div>
                <div v-else-if="file.isBatchFolder" class="text-color-secondary">
                  <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
                </div>
                <div v-else class="text-text-secondary">
                  <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path><polyline points="13 2 13 9 20 9"></polyline></svg>
                </div>
              </div>
                
              <!-- Details and Actions -->
              <div class="p-3 flex flex-col gap-2 bg-bg-surface/80 group-hover:bg-bg-hover transition-colors h-full">
                <div class="text-text-primary text-xs font-medium truncate" :title="file.filename">{{ file.filename }}</div>
                <div class="flex items-center justify-between mt-auto pt-1">
                  <div class="text-text-muted text-[10px] uppercase font-bold tracking-wider">{{ file.isBatchFolder ? 'Папка' : file.file_type }}</div>
                  <div class="flex gap-1" v-if="!file.isBatchFolder">
                    <button v-if="file.file_type !== 'audio' && file.file_type !== 'voice' && file.file_type !== 'sfx' && file.file_type !== 'ai_voice'" @click.stop="selectFile(file)" class="text-text-secondary hover:text-text-primary bg-bg-surface hover:bg-bg-hover p-1.5 rounded transition-colors" title="Предпросмотр">
                      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                    </button>
                    <button v-if="file.file_type === 'ai_voice'" @click.stop="$emit('edit-ai-voice', file)" class="text-color-secondary hover:text-text-primary bg-color-secondary/10 hover:bg-color-secondary/30 p-1.5 rounded transition-colors" title="Информация / Изменить">
                      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                    </button>
                    <button v-if="mode === 'select'" @click.stop="$emit('select', file.file_path)" class="text-color-secondary bg-color-secondary/10 hover:bg-color-secondary/30 p-1.5 rounded transition-colors" title="Выбрать">
                      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
                    </button>
                    <button @click.stop="handleDeleteMedia(file, $event)" class="text-red-500 hover:text-red-400 bg-red-500/10 hover:bg-red-500/20 p-1.5 rounded transition-colors" title="Удалить">
                      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
          </div>
        </div>

        <!-- Tab: Search Web -->
        <div v-else-if="activeTab === 'search'" class="flex-1 flex flex-col p-6">
          <div class="flex flex-col gap-4 mb-6">
            <div class="flex flex-wrap gap-3 items-center">
              <select v-model="searchEngine" @change="handleSearch" class="bg-bg-hover border border-text-muted rounded-xl px-4 py-3 text-text-primary focus:outline-none focus:border-color-secondary transition-colors w-40 sm:w-48 shrink-0 appearance-none">
                <option value="">Все источники</option>
                <option value="pixabay">Pixabay</option>
                <option value="unsplash">Unsplash</option>
                <option value="bing">Bing</option>
              </select>
              
              <div class="flex bg-bg-hover border border-text-muted rounded-xl overflow-x-auto hide-scrollbar shrink-0">
                <button @click="searchType = 'image'; handleSearch()" :class="['px-4 py-3 text-sm font-bold transition-colors', searchType === 'image' ? 'bg-color-secondary text-white' : 'text-text-secondary hover:text-text-primary hover:bg-bg-surface']">Фото</button>
                <button @click="searchType = 'video'; handleSearch()" :class="['px-4 py-3 text-sm font-bold transition-colors', searchType === 'video' ? 'bg-color-secondary text-white' : 'text-text-secondary hover:text-text-primary hover:bg-bg-surface']">Видео</button>
                <button @click="searchType = 'sfx'; handleSearch()" :class="['px-4 py-3 text-sm font-bold transition-colors', searchType === 'sfx' ? 'bg-color-secondary text-white' : 'text-text-secondary hover:text-text-primary hover:bg-bg-surface']">SFX</button>
              </div>

              <div class="flex flex-1 min-w-[200px] gap-2 relative">
                <input v-model="searchQuery" type="text" :placeholder="searchType === 'image' ? 'Поиск изображений...' : searchType === 'video' ? 'Поиск видео...' : 'Поиск звуков...'" class="flex-1 bg-bg-hover border border-text-muted rounded-xl px-4 py-3 pr-10 text-text-primary focus:outline-none focus:border-color-secondary transition-colors" @keyup.enter="handleSearch">
                <button v-if="searchQuery" @click="clearSearch" class="absolute right-[88px] top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary p-1 rounded z-10">
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                </button>
                <button @click="handleSearch" :disabled="!searchQuery || isSearching" class="px-6 py-3 bg-color-secondary hover:bg-color-primary text-white font-bold rounded-xl transition-colors flex items-center justify-center disabled:opacity-50 relative z-10">
                  <svg v-if="!isSearching" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                  <svg v-else class="animate-spin" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56"></path></svg>
                </button>
              </div>
            </div>
          </div>

          <div v-if="isSearching" class="flex-1 flex items-center justify-center">
            <svg class="animate-spin text-color-secondary" xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56"></path></svg>
          </div>
          <div v-else-if="searchResults.length === 0 && !hasSearched" class="flex-1 flex flex-col items-center justify-center text-text-muted">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" class="mb-4"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
            <p>Введите запрос для поиска по стокам и в интернете</p>
          </div>
          <div v-else-if="searchResults.length === 0 && hasSearched" class="flex-1 flex flex-col items-center justify-center text-text-muted">
            <p>По вашему запросу ничего не найдено</p>
          </div>
          <div v-else class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
            <div 
              v-for="result in searchResults" :key="result.id"
              @click="handleSelectSearchResult(result)"
              class="bg-bg-hover border border-text-muted rounded-xl overflow-hidden hover:border-color-success transition-all cursor-pointer group flex flex-col relative"
            >
              <div class="h-32 bg-black/50 flex items-center justify-center relative overflow-hidden">
                <img v-if="result.thumbnail" :src="result.thumbnail" class="w-full h-full object-cover" />
                <div v-else-if="searchType === 'sfx' || result.sfx" class="text-color-warning">
                  <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path><path d="M19.07 4.93a10 10 0 0 1 0 14.14"></path></svg>
                </div>
                <div v-else-if="searchType === 'video'" class="text-[#A78BFA]">
                  <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg>
                </div>
                <div v-else class="text-text-secondary">
                  <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
                </div>
                
                <div class="absolute inset-0 bg-black/70 flex flex-col items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity p-3 text-center gap-2">
                  <button @click.stop="previewSearchResult = result" class="px-3 py-1.5 bg-bg-hover hover:bg-bg-hover text-text-primary rounded-lg text-xs font-bold transition-colors w-full flex items-center justify-center gap-1">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                    Предпросмотр
                  </button>
                  <button @click.stop="handleSelectSearchResult(result)" class="px-3 py-1.5 bg-color-success hover:bg-color-success text-white rounded-lg text-xs font-bold transition-colors w-full flex items-center justify-center gap-1">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                    Скачать
                  </button>
                </div>
              </div>
              <div class="p-3 flex flex-col gap-1">
                <div class="flex justify-between items-center">
                  <div class="text-text-secondary text-[10px] uppercase truncate" :title="result.source">{{ result.source }}</div>
                  <div v-if="result.format" class="text-color-secondary text-[10px] uppercase font-bold">{{ result.format }}</div>
                </div>
                <div v-if="result.content" class="text-text-muted text-[9px] truncate" :title="result.content">{{ result.content }}</div>
              </div>
            </div>
          </div>
        </div>

      </div>
      
      <!-- Fullscreen Preview Overlay for Library Files -->
      <div v-if="previewFile" class="absolute inset-0 z-50 bg-bg-base/95 backdrop-blur-md flex flex-col animate-in fade-in zoom-in-95 duration-200">
        <div class="p-4 flex justify-between items-center bg-bg-surface border-b border-text-muted shrink-0">
          <h3 class="text-text-primary font-bold">{{ previewFile.filename }}</h3>
          <button @click="previewFile = null" class="p-2 text-text-secondary hover:text-text-primary transition-colors bg-bg-surface rounded-lg">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>
        <div class="flex-1 flex items-center justify-center p-6 overflow-hidden relative">
          <img v-if="previewFile.file_type === 'image'" :src="previewFile.file_path" class="max-w-full max-h-full object-contain drop-shadow-2xl rounded-lg" />
          <video v-else-if="previewFile.file_type === 'video'" :src="previewFile.file_path" controls autoplay class="max-w-full max-h-full drop-shadow-2xl rounded-lg"></video>
          <audio v-else-if="previewFile.file_type === 'audio' || previewFile.file_type === 'sfx'" :src="previewFile.file_path" controls autoplay class="w-full max-w-md drop-shadow-2xl"></audio>
          <div v-else class="text-text-secondary flex flex-col items-center">
            <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mb-4"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path><polyline points="13 2 13 9 20 9"></polyline></svg>
            <p>Предпросмотр недоступен</p>
          </div>
        </div>
        <div class="p-4 flex justify-end gap-3 bg-bg-surface border-t border-text-muted shrink-0">
          <button v-if="mode === 'select'" @click="emit('select', previewFile.file_path); previewFile = null" class="px-6 py-2 bg-color-secondary hover:bg-color-primary text-white font-bold rounded-lg transition-colors">
            Выбрать файл
          </button>
        </div>
      </div>
      
      <!-- Fullscreen Preview Overlay for Search Results -->
      <div v-if="previewSearchResult" class="absolute inset-0 z-50 bg-bg-base/95 backdrop-blur-md flex flex-col animate-in fade-in zoom-in-95 duration-200">
        <div class="p-4 flex justify-between items-center bg-bg-surface border-b border-text-muted shrink-0">
          <div class="flex items-center gap-4">
            <h3 class="text-text-primary font-bold truncate max-w-lg">{{ previewSearchResult.title || 'Предпросмотр' }}</h3>
            <span v-if="previewSearchResult.format" class="px-2 py-1 bg-bg-surface text-text-secondary text-xs rounded uppercase font-bold">{{ previewSearchResult.format }}</span>
            <span class="px-2 py-1 bg-bg-surface text-text-secondary text-xs rounded">{{ previewSearchResult.source }}</span>
          </div>
          <button @click="previewSearchResult = null" class="p-2 text-text-secondary hover:text-text-primary transition-colors bg-bg-surface rounded-lg">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>
        <div class="flex-1 flex items-center justify-center p-6 overflow-hidden relative w-full h-full">
          <iframe v-if="searchType === 'video' && previewSearchResult.iframe" :src="previewSearchResult.iframe" class="w-full h-full max-w-4xl max-h-[80vh] drop-shadow-2xl rounded-lg" frameborder="0" allowfullscreen allow="autoplay; encrypted-media"></iframe>
          <video v-else-if="searchType === 'video'" :src="previewSearchResult.url" controls class="max-w-full max-h-full drop-shadow-2xl rounded-lg" :poster="previewSearchResult.thumbnail"></video>
          <audio v-else-if="searchType === 'sfx' || previewSearchResult.sfx" :src="previewSearchResult.url" controls autoplay class="w-full max-w-md drop-shadow-2xl"></audio>
          <img v-else :src="previewSearchResult.url" class="max-w-full max-h-full object-contain drop-shadow-2xl rounded-lg" />
        </div>
        <div class="p-4 flex justify-between items-center bg-bg-surface border-t border-text-muted shrink-0">
          <div class="text-text-muted text-sm">
            <span v-if="previewSearchResult.content">{{ previewSearchResult.content }}</span>
            <span v-else>Дополнительная информация недоступна</span>
          </div>
          <div class="flex gap-2">
            <a v-if="previewSearchResult.source_url" :href="previewSearchResult.source_url" target="_blank" class="px-6 py-2 bg-bg-surface hover:bg-bg-hover text-text-primary font-bold rounded-lg transition-colors flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
              Источник
            </a>
            <button @click="handleSelectSearchResult(previewSearchResult); previewSearchResult = null" class="px-6 py-2 bg-color-success hover:bg-color-success text-white font-bold rounded-lg transition-colors flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
              Скачать в библиотеку
            </button>
          </div>
        </div>
      </div>
      
      <div v-if="isDownloading" class="absolute inset-0 z-[60] bg-black/50 backdrop-blur-sm flex flex-col items-center justify-center">
        <svg class="animate-spin text-color-secondary mb-4" xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56"></path></svg>
        <p class="text-text-primary font-bold text-lg">Загрузка файла...</p>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { uploadMedia, downloadMediaFromUrl, searchMedia, searchSfx, downloadSfx, deleteMedia, fetchProjectMedia } from '../../services/api'

const props = defineProps({
  isOpen: Boolean,
  presentationId: {
    type: Number,
    required: true
  },
  mediaFiles: {
    type: Array,
    default: () => []
  },
  mode: {
    type: String,
    default: 'select' // 'select' | 'manage'
  }
})

const emit = defineEmits(['close', 'select', 'select-batch', 'uploaded', 'deleted', 'edit-ai-voice'])

const activeTab = ref('library') // 'library' | 'search'

// Global vs Local state
const isGlobal = ref(true)
const globalMediaFiles = ref([])
const loadingGlobal = ref(false)

// Загрузка медиа проекта. force=true — перечитать (после открытия/загрузки файла),
// иначе из кэша. Раньше это висело только на watch(isGlobal) и не срабатывало
// при открытии модалки (presentationId приходил позже, чем происходил immediate-вызов).
const loadGlobal = async (force = false) => {
  if (!props.presentationId) return
  if (!force && globalMediaFiles.value.length) return
  loadingGlobal.value = true
  try {
    globalMediaFiles.value = await fetchProjectMedia(props.presentationId)
  } catch (e) {
    console.error('Failed to load project media', e)
  } finally {
    loadingGlobal.value = false
  }
}

watch(isGlobal, (val) => {
  if (val) loadGlobal()
})

// Открытие модалки: сбрасываем состояние и принудительно тянем свежий список.
watch(() => props.isOpen, (open) => {
  if (!open) return
  activeTab.value = 'library'
  activeBatchId.value = null
  previewFile.value = null
  previewSearchResult.value = null
  globalMediaFiles.value = []
  loadGlobal(true)
}, { immediate: true })

// Смена презентации при открытой модалке (переход по папкам).
watch(() => props.presentationId, () => {
  if (props.isOpen) {
    globalMediaFiles.value = []
    loadGlobal(true)
  }
})

// Library Filter
const libraryFilter = ref('all') // 'all' | 'image' | 'video' | 'audio' | 'sfx' | 'voice'
const activeBatchId = ref(null)

watch(libraryFilter, () => {
  activeBatchId.value = null
})

const groupedMediaFiles = computed(() => {
  const sourceFiles = isGlobal.value ? globalMediaFiles.value : props.mediaFiles
  let filtered = sourceFiles
  if (libraryFilter.value !== 'all') {
    filtered = sourceFiles.filter(f => f.file_type === libraryFilter.value)
  }
  
  if (activeBatchId.value) {
    return filtered.filter(f => {
      let settings = f.ai_settings;
      if (typeof settings === 'string') {
        try { settings = JSON.parse(settings) } catch(e) {}
      }
      return f.file_type === 'ai_voice' && (settings || {}).batch_id === activeBatchId.value
    })
  }
  
  const result = []
  const batchCounts = {}
  
  for (const f of filtered) {
    let settings = f.ai_settings;
    if (typeof settings === 'string') {
      try { settings = JSON.parse(settings) } catch(e) {}
    }
    f.ai_settings_parsed = settings || {};

    if (f.file_type === 'ai_voice' && f.ai_settings_parsed?.batch_id) {
      if (!batchCounts[f.ai_settings_parsed.batch_id]) {
        batchCounts[f.ai_settings_parsed.batch_id] = {
           isBatchFolder: true,
           batch_id: f.ai_settings_parsed.batch_id,
           count: 0,
           filename: 'Пакет ' + f.ai_settings_parsed.batch_id.substring(0, 5),
           file_type: 'batch_folder',
           id: 'batch_' + f.ai_settings_parsed.batch_id
        }
        result.push(batchCounts[f.ai_settings_parsed.batch_id])
      }
      batchCounts[f.ai_settings_parsed.batch_id].count++
      batchCounts[f.ai_settings_parsed.batch_id].filename = 'Пакет из ' + batchCounts[f.ai_settings_parsed.batch_id].count + ' фрагментов'
    } else {
      result.push(f)
    }
  }
  return result
})

// Audio Preview Inline
const playingAudioId = ref(null)
const audioRefs = ref({})
const setAudioRef = (el, id) => {
  if (el) audioRefs.value[id] = el
}
const toggleAudio = (file, e) => {
  e.stopPropagation()
  if (playingAudioId.value === file.id) {
    audioRefs.value[file.id]?.pause()
    playingAudioId.value = null
  } else {
    if (playingAudioId.value && audioRefs.value[playingAudioId.value]) {
      audioRefs.value[playingAudioId.value].pause()
    }
    playingAudioId.value = file.id
    audioRefs.value[file.id]?.play().catch(e => console.error('Audio play error', e))
  }
}

const handleDeleteMedia = async (file, e) => {
  e.stopPropagation()
  if (!confirm(`Вы уверены что хотите удалить файл "${file.filename}"?`)) return
  try {
    await deleteMedia(file.presentation_id || props.presentationId, file.id)
    emit('deleted', file.id)
    if (isGlobal.value) {
      globalMediaFiles.value = globalMediaFiles.value.filter(m => m.id !== file.id)
    }
  } catch (err) {
    console.error("Delete failed", err)
    alert("Ошибка удаления файла")
  }
}

// Search state
const searchQuery = ref('')
const searchResults = ref([])
const isSearching = ref(false)
const hasSearched = ref(false)
const searchEngine = ref('')
const searchType = ref('image')

const clearSearch = () => {
  searchQuery.value = ''
  searchResults.value = []
  hasSearched.value = false
}

// Download State
const manualUrl = ref('')
const isDownloading = ref(false)

// Preview State
const previewFile = ref(null)
const previewSearchResult = ref(null)

// Close on escape key
const handleKeydown = (e) => {
  if (props.isOpen && e.key === 'Escape') {
    if (previewFile.value) {
      previewFile.value = null
    } else if (previewSearchResult.value) {
      previewSearchResult.value = null
    } else {
      emit('close')
    }
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

const uploading = ref(false)
const isDragging = ref(false)

const selectFile = (file) => {
  if (file.isBatchFolder) {
    activeBatchId.value = file.batch_id
    return
  }
  previewFile.value = file
}

const handleFileUpload = async (e) => {
  const files = e.target.files
  if (!files || files.length === 0) return
  await processFiles(Array.from(files))
}

const handleDrop = async (e) => {
  isDragging.value = false
  const files = e.dataTransfer.files
  if (!files || files.length === 0) return
  await processFiles(Array.from(files))
}

const processFiles = async (files) => {
  uploading.value = true
  try {
    for (const file of files) {
      const uploadedMedia = await uploadMedia(props.presentationId, file)
      emit('uploaded', uploadedMedia)
    }
    if (isGlobal.value) await loadGlobal(true)
  } catch (err) {
    console.error("Upload failed", err)
    alert("Ошибка загрузки файла")
  } finally {
    uploading.value = false
  }
}

const handleDownloadUrl = async () => {
  if (!manualUrl.value) return
  isDownloading.value = true
  try {
    const uploadedMedia = await downloadMediaFromUrl(props.presentationId, manualUrl.value)
    emit('uploaded', uploadedMedia)
    manualUrl.value = ''
    if (isGlobal.value) await loadGlobal(true)
    alert("Файл успешно скачан!")
  } catch (e) {
    console.error("Failed to download URL", e)
    alert("Ошибка скачивания по ссылке")
  } finally {
    isDownloading.value = false
  }
}

const handleSearch = async () => {
  if (!searchQuery.value.trim()) return
  isSearching.value = true
  hasSearched.value = true
  try {
    if (searchType.value === 'sfx') {
      const data = await searchSfx(props.presentationId, searchQuery.value)
      searchResults.value = (data.hits || []).map(hit => ({
        id: hit.id,
        url: hit.preview, // The actual MP3 URL to download
        title: hit.name || hit.tags,
        source: 'FreeSound API',
        format: 'mp3',
        sfx: true,
        duration: hit.duration
      }))
    } else {
      searchResults.value = await searchMedia(searchQuery.value, 'searxng', searchType.value, searchEngine.value)
    }
  } catch (e) {
    console.error(e)
    alert("Ошибка поиска")
  } finally {
    isSearching.value = false
  }
}

const handleSelectSearchResult = async (result) => {
  if (!result.url) return
  isDownloading.value = true
  try {
    let uploadedMedia;
    if (result.sfx) {
      uploadedMedia = await downloadSfx(props.presentationId, result.url, result.title + ".mp3")
    } else {
      uploadedMedia = await downloadMediaFromUrl(props.presentationId, result.url)
    }
    emit('uploaded', uploadedMedia)
    activeTab.value = 'library'
    if (isGlobal.value) await loadGlobal(true)
  } catch (e) {
    console.error(e)
    alert("Не удалось скачать этот файл, возможно сервер запретил скачивание (CORS/403).")
  } finally {
    isDownloading.value = false
  }
}
</script>
