<template>
  <div class="dynamic-editor space-y-4">
    <!-- Global hidden color picker for fallback (centered on screen so popup never overflows) -->
    <input type="color" ref="globalColorInput" class="fixed top-1/2 left-1/2 opacity-0 pointer-events-none w-10 h-10 z-[300]" @input="onGlobalColorInput" />
    
    <!-- Loop through all keys in the template (or modelValue if template is missing) -->
    <template v-for="(key) in currentKeys" :key="key">
      <div class="pl-2 border-l border-gray-200 ml-2 mb-4">
        
        <!-- Label & Actions -->
        <div v-if="key !== 'sfx'" class="flex items-center justify-between mb-2">
          <label class="block text-xs font-bold text-text-secondary uppercase tracking-wider">
            {{ key }}
          </label>
          <div class="flex gap-2">
            <button 
              v-if="getType(key) === 'array' && hasTimings(key, modelValue[key])" 
              @click="resetTimings(key)"
              class="text-[10px] bg-red-500/10 text-red-500 hover:bg-red-500/20 px-2 py-1 rounded transition-colors flex items-center gap-1 font-bold"
              title="Сбросить все тайминги в 0"
            >
              <Icon icon="heroicons:arrow-path" />
              В НУЛЬ
            </button>
            <button 
              v-if="getType(key) === 'array' && hasTimings(key, modelValue[key])" 
              @click="openDistributeModal(key)"
              class="text-[10px] bg-color-secondary/10 text-color-secondary hover:bg-color-secondary/20 px-2 py-1 rounded transition-colors flex items-center gap-1 font-bold"
            >
              <Icon icon="heroicons:clock" />
              РАСПРЕДЕЛИТЬ
            </button>
          </div>
        </div>
        
        <!-- Role/Sender Input -->
        <div v-if="isRoleField(key)" class="flex bg-white border border-gray-200 rounded-lg p-1">
          <button 
            v-for="role in ['user', 'bot', 'assistant']" 
            :key="role"
            @click="updateField(key, role)"
            class="flex-1 py-1.5 text-xs font-bold rounded-md transition-colors capitalize"
            :class="getVal(key) === role ? 'bg-color-primary text-white shadow-md' : 'text-text-muted hover:text-text-primary hover:bg-bg-surface'"
          >
            {{ role }}
          </button>
        </div>

        <!-- TimePicker Input -->
        <div v-else-if="isTimeField(key)" class="flex gap-2">
           <div class="flex-1 min-w-0">
             <TimePicker 
               :modelValue="Number(getVal(key)) || 0" 
               @update:modelValue="updateField(key, $event)"
             />
           </div>
           <button @click="updateField(key, 0)" class="p-2 w-[38px] h-[38px] shrink-0 bg-red-500/10 hover:bg-red-500/20 text-red-500 rounded-lg transition-colors flex items-center justify-center" title="Сбросить тайминг в 0">
             <Icon icon="heroicons:arrow-path" class="text-xl" />
           </button>
        </div>

        <!-- String Input -->
        <div v-else-if="getType(key) === 'string'" class="flex gap-2">
          <!-- Textarea if it seems like a long string, otherwise input -->
          <textarea 
            v-if="isLongText(key)"
            :value="getVal(key)" 
            @input="updateField(key, $event.target.value)"
            rows="3"
            class="flex-1 bg-white border border-gray-200 rounded-lg px-3 py-2 text-gray-800 text-sm focus:outline-none focus:border-color-primary"
          ></textarea>
          <template v-else>
            <!-- Media/Icon Preview -->
            <img v-if="isMediaField(key) && getVal(key) && !getVal(key).endsWith('.mp4')" :src="getVal(key)" class="w-[38px] h-[38px] rounded-lg object-cover bg-gray-100 border border-gray-200 shrink-0" />
            <video v-else-if="isMediaField(key) && getVal(key) && getVal(key).endsWith('.mp4')" :src="getVal(key)" class="w-[38px] h-[38px] rounded-lg object-cover bg-gray-100 border border-gray-200 shrink-0" muted loop playsinline autoplay></video>
            <div v-else-if="isIconField(key) && getVal(key)" class="w-[38px] h-[38px] rounded-lg bg-gray-100 border border-gray-200 shrink-0 flex items-center justify-center">
              <Icon :icon="getVal(key)" class="text-xl text-text-primary" />
            </div>
            
            <!-- Input -->
            <select v-if="key === 'type'" :value="getVal(key)" @change="updateField(key, $event.target.value)" class="flex-1 bg-white border border-gray-200 rounded-lg px-3 py-2 text-gray-800 text-sm focus:outline-none focus:border-color-primary appearance-none cursor-pointer">
              <option value="text">Текст / Цифры</option>
              <option value="icon">Иконка</option>
              <option value="boolean">Булево (галочка / крестик)</option>
              <option value="trend">Тренд (стрелка ±%)</option>
              <option value="status">Статус (плашка)</option>
              <option value="image">Картинка / Скриншот</option>
              <option value="html">Сырой HTML код</option>
            </select>
            <select v-else-if="key === 'align'" :value="getVal(key)" @change="updateField(key, $event.target.value)" class="flex-1 bg-white border border-gray-200 rounded-lg px-3 py-2 text-gray-800 text-sm focus:outline-none focus:border-color-primary appearance-none cursor-pointer">
              <option value="left">Слева</option>
              <option value="center">По центру</option>
              <option value="right">Справа</option>
            </select>
            <select v-else-if="key === 'image_position'" :value="getVal(key) || 'top'" @change="updateField(key, $event.target.value)" class="flex-1 bg-white border border-gray-200 rounded-lg px-3 py-2 text-gray-800 text-sm focus:outline-none focus:border-color-primary cursor-pointer">
              <option value="top">Сверху</option>
              <option value="center">По центру</option>
              <option value="bottom">Снизу</option>
            </select>
            <select v-else-if="key === 'size'" :value="getVal(key) || '1x1'" @change="updateField(key, $event.target.value)" class="flex-1 bg-white border border-gray-200 rounded-lg px-3 py-2 text-gray-800 text-sm focus:outline-none focus:border-color-primary cursor-pointer">
              <option value="1x1">1x1 (Квадрат)</option>
              <option value="1x2">1x2 (Вертикальный)</option>
              <option value="2x1">2x1 (Горизонтальный)</option>
              <option value="2x2">2x2 (Большой квадрат)</option>
              <option value="3x2">3x2 (Широкий)</option>
              <option value="4x2">4x2 (На всю ширину)</option>
            </select>
            <input 
              v-else
              type="text" 
              :value="getVal(key)" 
              @input="updateField(key, $event.target.value)"
              class="flex-1 bg-white border border-gray-200 rounded-lg px-3 py-2 text-gray-800 text-sm focus:outline-none focus:border-color-primary min-w-0"
            >
          </template>
          
          <!-- Emoji button for long texts -->
          <button v-if="isLongText(key)" @click="$emit('request-emoji', {keyPath: key})" class="p-2 h-[38px] w-[38px] bg-color-warning/10 hover:bg-color-warning/20 text-color-warning rounded-lg transition-colors flex items-center justify-center shrink-0" title="Вставить эмодзи">
            <Icon icon="heroicons:face-smile" class="text-xl" />
          </button>
          
          <!-- Color inputs -->
          <div v-if="isColorField(key)" @click="pickColorWithEyeDropper(key)" class="relative h-[38px] w-[38px] rounded-lg shrink-0 border border-gray-200 cursor-pointer overflow-hidden group" title="Взять цвет с экрана (Пипетка)">
            <div class="w-full h-full" :style="{ backgroundColor: getVal(key) }"></div>
            <div class="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
              <Icon icon="lucide:pipette" class="text-text-primary text-lg" />
            </div>
          </div>
          <button v-if="isColorField(key)" @click="$emit('request-color', {keyPath: key})" class="p-2 h-[38px] w-[38px] bg-pink-500/10 hover:bg-pink-500/20 text-pink-500 rounded-lg transition-colors flex items-center justify-center shrink-0" title="Палитра">
            <Icon icon="heroicons:swatch" class="text-xl" />
          </button>
          
          <!-- Special button for media/icons -->
          <button v-if="isMediaField(key)" @click="$emit('request-media', {keyPath: key})" class="p-2 h-[38px] w-[38px] bg-color-secondary/10 hover:bg-color-secondary/20 text-color-secondary rounded-lg transition-colors flex items-center justify-center shrink-0" title="Select Media">
            <Icon icon="heroicons:photo" class="text-xl" />
          </button>
          <button v-if="isIconField(key)" @click="$emit('request-icon', {keyPath: key})" class="p-2 h-[38px] w-[38px] bg-[#A78BFA]/10 hover:bg-[#A78BFA]/20 text-[#A78BFA] rounded-lg transition-colors flex items-center justify-center shrink-0" title="Select Icon">
            <Icon icon="heroicons:sparkles" class="text-xl" />
          </button>
        </div>
        
        <!-- Wheel Slider Input for scroll_amount -->
        <div v-else-if="key === 'scroll_amount'" class="space-y-1 w-full bg-bg-surface p-3 rounded-lg border border-gray-200">
          <div class="flex justify-between items-center mb-2">
            <span class="text-[10px] text-text-secondary font-bold uppercase tracking-wide">Процент скролла</span>
            <span class="text-xs font-mono text-color-secondary bg-color-secondary/10 px-1.5 py-0.5 rounded">{{ getVal(key) }}%</span>
          </div>
          <div class="flex items-center gap-3 bg-gray-50 px-3 py-2 rounded-md border border-gray-200" @wheel.prevent="updateField(key, Math.max(0, Math.min(100, (getVal(key) || 0) + ($event.deltaY > 0 ? -5 : 5))))">
             <div class="relative flex-1 flex items-center h-5">
               <!-- Ticks -->
               <div v-for="tick in [0, 25, 50, 75, 100]" :key="'t-'+tick" 
                    class="absolute w-0.5 pointer-events-none rounded-full"
                    :class="tick === 100 ? 'h-4 bg-color-secondary' : 'h-2 bg-color-secondary/30'"
                    :style="`left: ${tick}%; top: 50%; transform: translate(-50%, -50%)`">
               </div>
               <input type="range" :value="getVal(key)" @input="updateField(key, Number($event.target.value))" min="0" max="100" step="1" class="w-full accent-color-secondary relative z-10 bg-transparent cursor-ew-resize" title="Крутите колесиком мыши для настройки" />
             </div>
          </div>
        </div>
        
        <!-- Number Input -->
        <input 
          v-else-if="getType(key) === 'number'" 
          type="number" 
          :step="isFloatField(key) ? '0.1' : '1'"
          :value="getVal(key)" 
          @input="updateField(key, Number($event.target.value))"
          class="w-full bg-white border border-gray-200 rounded-lg px-3 py-2 text-gray-800 text-sm focus:outline-none focus:border-color-primary"
        >
        
        <!-- Boolean Input -->
        <div v-else-if="getType(key) === 'boolean'" class="flex items-center gap-3 mt-1 cursor-pointer w-max" @click="updateField(key, !getVal(key))">
          <div class="relative inline-flex items-center h-6 rounded-full w-11 transition-colors duration-300"
               :class="getVal(key) ? 'bg-color-secondary' : 'bg-bg-surface'">
            <span class="inline-block w-4 h-4 transform bg-bg-surface rounded-full transition-transform duration-300"
                  :class="getVal(key) ? 'translate-x-6' : 'translate-x-1'"></span>
          </div>
          <span class="text-sm font-bold tracking-wide transition-colors duration-300" :class="getVal(key) ? 'text-color-secondary' : 'text-text-secondary'">{{ getVal(key) ? 'True' : 'False' }}</span>
        </div>
        
        <!-- Compact Columns Editor -->
        <div v-else-if="getType(key) === 'array' && key === 'columns'" class="w-full bg-white rounded-lg border border-gray-200 overflow-x-auto p-4">
          <table class="w-full text-left text-sm border-separate border-spacing-0">
            <thead>
              <tr class="text-text-muted text-[10px] uppercase tracking-wider">
                <th class="pb-2 font-medium">Key</th>
                <th class="pb-2 font-medium pl-2">Label</th>
                <th class="pb-2 font-medium pl-2">Type</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in modelValue[key]" :key="index" class="group">
                <td class="py-1 border-b border-gray-100 group-last:border-0"><input :value="item.key" @input="item.key = $event.target.value; updateField(key, [...modelValue[key]])" type="text" class="w-full bg-white border border-gray-200 rounded px-2 py-1.5 text-text-primary text-xs focus:outline-none focus:border-color-primary" /></td>
                <td class="pl-2 py-1 border-b border-gray-100 group-last:border-0"><input :value="item.label" @input="item.label = $event.target.value; updateField(key, [...modelValue[key]])" type="text" class="w-full bg-white border border-gray-200 rounded px-2 py-1.5 text-text-primary text-xs focus:outline-none focus:border-color-primary" /></td>
                <td class="pl-2 py-1 border-b border-gray-100 group-last:border-0">
                  <select :value="item.type" @change="item.type = $event.target.value; updateField(key, [...modelValue[key]])" class="w-full bg-white border border-gray-200 rounded px-2 py-1.5 text-text-primary text-xs focus:outline-none focus:border-color-primary appearance-none">
                    <option value="text">Текст</option>
                    <option value="icon">Иконка</option>
                    <option value="boolean">Булево</option>
                    <option value="trend">Тренд</option>
                    <option value="status">Статус</option>
                  </select>
                </td>
                <td class="pl-2 py-1 border-b border-gray-100 group-last:border-0 w-8">
                  <button @click.stop="removeArrayItem(key, index)" class="p-1.5 text-red-400 opacity-20 group-hover:opacity-100 bg-red-900/20 rounded hover:bg-red-900/40 transition-opacity"><Icon icon="heroicons:trash" class="w-4 h-4" /></button>
                </td>
              </tr>
            </tbody>
          </table>
          <button @click="modelValue[key].push({key: 'new_col', label: 'Новая', type: 'text'}); updateField(key, [...modelValue[key]])" class="mt-3 text-[11px] font-bold uppercase tracking-wider flex items-center gap-1 text-color-secondary hover:text-text-primary bg-color-secondary/10 hover:bg-color-secondary/20 px-3 py-2 rounded-lg transition-colors w-max"><Icon icon="heroicons:plus" class="w-4 h-4" /> Добавить колонку</button>
        </div>

        <!-- Node Connections Editor (For Interactive Architecture) -->
        <div v-else-if="key === 'to' && (rootValue || modelValue)?.nodes" class="flex flex-wrap gap-2 p-2 bg-white rounded-lg border border-gray-200">
           <div v-for="node in (rootValue || modelValue).nodes" :key="node.id">
             <button v-if="node.id !== modelValue.id" 
                     @click="toggleNodeConnection(key, node.id)"
                     class="px-3 py-1.5 rounded-lg text-xs font-bold transition-all border"
                     :class="(modelValue[key] || []).includes(node.id) ? 'bg-color-primary border-color-primary text-white shadow-lg' : 'bg-bg-surface border-gray-200 text-gray-500 hover:bg-gray-50'">
               {{ node.label || node.id }}
             </button>
           </div>
        </div>

        <!-- Default Array Editor -->
        <div v-else-if="getType(key) === 'array'" class="space-y-3">
          <div v-for="(item, index) in (modelValue[key] || [])" :key="index" class="relative group bg-bg-surface p-4 pt-6 rounded-lg border border-gray-200 hover:border-gray-200 transition-colors">
            <button @click.stop="removeArrayItem(key, index)" class="absolute top-2 right-2 p-1 text-red-400 opacity-0 group-hover:opacity-100 transition-opacity bg-red-900/20 rounded hover:bg-red-900/40" title="Remove Item">
              <Icon icon="heroicons:trash" />
            </button>
            <div class="absolute top-2 left-4 text-[10px] text-text-muted font-bold uppercase tracking-wider">Item {{ index + 1 }}</div>
            
            <!-- Recursive call for array item -->
            <DynamicJsonEditor 
              v-if="typeof item === 'object' && item !== null"
              :modelValue="item"
              :template="template[key]?.[0] || {}"
              :schema="fieldSchema(key)?.item?.fields || {}"
              :rootValue="rootValue || modelValue"
              :hiddenKeys="hiddenKeys"
              @update:modelValue="updateArrayItem(key, index, $event)"
              @request-media="(payload) => $emit('request-media', {keyPath: `${key}.${index}.${payload.keyPath}`})"
              @request-icon="(payload) => $emit('request-icon', {keyPath: `${key}.${index}.${payload.keyPath}`})"
              @request-emoji="(payload) => $emit('request-emoji', {keyPath: `${key}.${index}.${payload.keyPath}`})"
              @request-color="(payload) => $emit('request-color', {keyPath: `${key}.${index}.${payload.keyPath}`})"
            />
            <div v-else-if="typeof item === 'string'" class="flex gap-2">
              <!-- Media/Icon Preview -->
              <img v-if="isMediaField(key) && item && !item.endsWith('.mp4')" :src="item" class="w-[38px] h-[38px] rounded-lg object-cover bg-gray-100 border border-gray-200 shrink-0" />
              <video v-else-if="isMediaField(key) && item && item.endsWith('.mp4')" :src="item" class="w-[38px] h-[38px] rounded-lg object-cover bg-gray-100 border border-gray-200 shrink-0" muted loop playsinline autoplay></video>
              <div v-else-if="isIconField(key) && item" class="w-[38px] h-[38px] rounded-lg bg-gray-100 border border-gray-200 shrink-0 flex items-center justify-center">
                <Icon :icon="item" class="text-xl text-text-primary" />
              </div>

              <!-- Input -->
              <input 
                type="text" 
                :value="item"
                @input="updateArrayItem(key, index, $event.target.value)"
                class="flex-1 bg-white border border-gray-200 rounded-lg px-3 py-2 text-gray-800 text-sm focus:outline-none focus:border-color-primary min-w-0"
              >
              <!-- Color inputs -->
              <div v-if="isColorField(key)" @click="pickColorWithEyeDropper(key, true, index)" class="relative h-[38px] w-[38px] rounded-lg shrink-0 border border-gray-200 cursor-pointer overflow-hidden group" title="Взять цвет с экрана (Пипетка)">
                <div class="w-full h-full" :style="{ backgroundColor: modelValue[key][index] || '#000000' }"></div>
                <div class="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                  <Icon icon="lucide:pipette" class="text-text-primary text-lg" />
                </div>
              </div>
              <button v-if="isColorField(key)" @click="$emit('request-color', {keyPath: `${key}[${index}]`})" class="p-2 h-[38px] w-[38px] bg-pink-500/10 hover:bg-pink-500/20 text-pink-500 rounded-lg transition-colors flex items-center justify-center shrink-0" title="Палитра">
                <Icon icon="heroicons:swatch" class="text-xl" />
              </button>
              <button v-if="isMediaField(key)" @click="$emit('request-media', {keyPath: `${key}[${index}]`})" class="p-2 h-[38px] w-[38px] bg-color-secondary/10 hover:bg-color-secondary/20 text-color-secondary rounded-lg transition-colors flex items-center justify-center shrink-0" title="Select Media">
                <Icon icon="heroicons:photo" class="text-xl" />
              </button>
              <button v-if="isIconField(key)" @click="$emit('request-icon', {keyPath: `${key}[${index}]`})" class="p-2 h-[38px] w-[38px] bg-[#A78BFA]/10 hover:bg-[#A78BFA]/20 text-[#A78BFA] rounded-lg transition-colors flex items-center justify-center shrink-0" title="Select Icon">
                <Icon icon="heroicons:sparkles" class="text-xl" />
              </button>
            </div>
            <input 
              v-else-if="typeof item === 'number'"
              type="number" 
              :step="isFloatField(key) ? '0.1' : '1'"
              :value="item"
              @input="updateArrayItem(key, index, Number($event.target.value))"
              class="w-full bg-white border border-gray-200 rounded-lg px-3 py-2 text-gray-800 text-sm focus:outline-none focus:border-color-primary"
            >
          </div>
          
          <button @click="addArrayItem(key)" class="w-full py-2 border border-dashed border-text-secondary rounded-xl text-text-secondary hover:text-text-primary hover:border-text-secondary hover:bg-bg-surface transition-all flex items-center justify-center gap-2 text-sm mt-2">
            <Icon icon="heroicons:plus" /> Add Item
          </button>
        </div>
        
        <!-- Object Editor -->
        <div v-else-if="getType(key) === 'object'" class="bg-white rounded-xl border border-gray-200" :class="key === 'sfx' ? 'p-2' : 'p-4'">
          <details v-if="key === 'sfx'" class="group">
            <summary class="text-xs text-[#A78BFA]/70 cursor-pointer font-bold uppercase tracking-wider outline-none group-open:mb-3 transition-colors hover:text-[#A78BFA] flex items-center gap-1">
              <Icon icon="heroicons:chevron-right" class="w-4 h-4 group-open:rotate-90 transition-transform" />
              Тонкая настройка (Индивидуальный SFX)
            </summary>
            <div class="pl-2 border-l border-gray-200 ml-2">
              <DynamicJsonEditor 
                :modelValue="modelValue[key] || {}"
                :template="template[key] || {}"
                :schema="fieldSchema(key)?.fields || {}"
                :rootValue="rootValue || modelValue"
                @update:modelValue="updateField(key, $event)"
                @request-media="(payload) => $emit('request-media', {keyPath: `${key}.${payload.keyPath}`})"
                @request-icon="(payload) => $emit('request-icon', {keyPath: `${key}.${payload.keyPath}`})"
                @request-emoji="(payload) => $emit('request-emoji', {keyPath: `${key}.${payload.keyPath}`})"
                @request-color="(payload) => $emit('request-color', {keyPath: `${key}.${payload.keyPath}`})"
              />
            </div>
          </details>
          <DynamicJsonEditor 
            v-else
            :modelValue="modelValue[key] || {}"
            :template="template[key] || {}"
            :schema="fieldSchema(key)?.fields || {}"
            :rootValue="rootValue || modelValue"
            @update:modelValue="updateField(key, $event)"
            @request-media="(payload) => $emit('request-media', {keyPath: `${key}.${payload.keyPath}`})"
            @request-icon="(payload) => $emit('request-icon', {keyPath: `${key}.${payload.keyPath}`})"
            @request-emoji="(payload) => $emit('request-emoji', {keyPath: `${key}.${payload.keyPath}`})"
            @request-color="(payload) => $emit('request-color', {keyPath: `${key}.${payload.keyPath}`})"
          />
        </div>
        
      </div>
    </template>
    
    <!-- Distribute Timings Modal -->
    <div v-if="showDistributeModal" class="fixed inset-0 z-[200] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div class="bg-white border border-gray-200 rounded-2xl p-6 w-full max-w-sm shadow-2xl relative">
        <h3 class="text-lg font-bold text-text-primary mb-4">Распределение таймингов</h3>
        <div class="space-y-4">
          <div>
            <label class="block text-xs font-bold text-text-secondary mb-2">Начальный отступ (ms)</label>
            <input type="number" v-model="distributeStart" class="w-full bg-white border border-gray-200 rounded-lg px-3 py-2 text-gray-800 text-sm focus:outline-none focus:border-color-primary font-mono" />
          </div>
          <div>
            <label class="block text-xs font-bold text-text-secondary mb-2">Интервал (ms)</label>
            <input type="number" v-model="distributeInterval" @input="onManualIntervalChange" class="w-full bg-white border border-gray-200 rounded-lg px-3 py-2 text-gray-800 text-sm focus:outline-none focus:border-color-primary font-mono" />
          </div>
          
          <div class="mt-2 border-t border-gray-200 pt-3">
            <div class="flex justify-between items-center mb-1">
              <label class="text-[10px] uppercase font-bold text-text-muted">Плотность / Скорость</label>
              <span class="text-[10px] font-mono" :class="distributeScale < 100 ? 'text-color-secondary' : 'text-text-secondary'">{{ distributeScale }}%</span>
            </div>
            <input type="range" min="10" max="200" step="5" v-model="distributeScale" @input="applyScale" class="w-full accent-color-secondary h-1.5 bg-text-muted/30 rounded-lg appearance-none cursor-pointer" />
          </div>
          <div class="flex flex-col gap-2 mt-6">
            <div class="flex gap-2">
              <button @click="smartDistribute(false)" class="flex-1 py-2 rounded-lg font-bold text-color-secondary bg-color-secondary/10 hover:bg-color-secondary/20 transition-colors border border-color-secondary/30 text-[10px] uppercase flex items-center justify-center gap-1" title="От начала (с отступом только в конце)">
                 <Icon icon="heroicons:bars-3-bottom-left" class="text-sm" /> АВТО (Слева)
              </button>
              <button @click="smartDistribute(true)" class="flex-1 py-2 rounded-lg font-bold text-color-secondary bg-color-secondary/10 hover:bg-color-secondary/20 transition-colors border border-color-secondary/30 text-[10px] uppercase flex items-center justify-center gap-1" title="Равномерные отступы с обеих сторон">
                 <Icon icon="heroicons:arrows-right-left" class="text-sm" /> АВТО (По центру)
              </button>
            </div>
            <div class="flex gap-2 mt-1">
              <button @click="cancelDistribution" class="py-2 px-3 flex-1 rounded-lg font-bold text-text-secondary hover:text-text-primary bg-bg-surface hover:bg-bg-surface transition-colors text-sm">Отмена</button>
              <button @click="confirmDistribution" class="flex-1 py-2 rounded-lg font-bold text-white bg-color-primary hover:bg-color-primary/80 transition-colors text-sm">Применить</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Icon } from '@iconify/vue'
import TimePicker from './TimePicker.vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  },
  template: {
    type: Object,
    default: () => ({})
  },
  schema: {
    type: Object,
    default: () => ({})
  },
  hiddenKeys: {
    type: Array,
    default: () => []
  },
  rootValue: {
    type: Object,
    default: null
  },
  slideDuration: {
    type: Number,
    default: 15000
  }
})

const emit = defineEmits(['update:modelValue', 'request-media', 'request-icon', 'request-emoji', 'request-color'])

const showDistributeModal = ref(false)
const distributeKey = ref(null)
const distributeStart = ref(0)
const distributeInterval = ref(1000)
const distributeScale = ref(100)
const baseInterval = ref(1000)

const applyScale = () => {
  distributeInterval.value = Math.floor(baseInterval.value * (distributeScale.value / 100))
}

const onManualIntervalChange = () => {
  baseInterval.value = distributeInterval.value
  distributeScale.value = 100
}

const globalColorInput = ref(null)
const activeColorField = ref(null)

const onGlobalColorInput = (e) => {
  if (!activeColorField.value) return
  const { key, isArray, index } = activeColorField.value
  if (isArray) {
    updateArrayItem(key, index, e.target.value)
  } else {
    updateField(key, e.target.value)
  }
}

const pickColorWithEyeDropper = async (key, isArray = false, index = 0) => {
  if (window.EyeDropper) {
    try {
      const eyeDropper = new window.EyeDropper()
      const result = await eyeDropper.open()
      if (result && result.sRGBHex) {
        if (isArray) {
          updateArrayItem(key, index, result.sRGBHex)
        } else {
          updateField(key, result.sRGBHex)
        }
      }
      return
    } catch (err) {
      console.log('EyeDropper canceled', err)
      return
    }
  }
  
  // Fallback: use global centralized color picker
  activeColorField.value = { key, isArray, index }
  if (globalColorInput.value) {
    let currentVal = isArray ? (props.modelValue[key] || [])[index] : (props.modelValue[key] !== undefined ? props.modelValue[key] : props.template[key])
    globalColorInput.value.value = currentVal || '#000000'
    globalColorInput.value.click()
  }
}

const hasTimings = (key, arr) => {
  const k = key.toLowerCase()
  if (k.includes('message') || k.includes('director') || k.includes('event') || k.includes('chat')) return true
  
  if (!Array.isArray(arr) || arr.length === 0) return false
  const first = arr[0]
  if (typeof first !== 'object' || first === null) return false
  return 'time' in first || 'start_time' in first
}

const originalArrayBackup = ref(null)

const openDistributeModal = (key) => {
  distributeKey.value = key
  
  const arr = props.modelValue[key] || []
  originalArrayBackup.value = JSON.parse(JSON.stringify(arr))
  
  // Calculate smart defaults if possible
  if (arr.length > 0 && props.slideDuration > 0) {
    const availableTime = Math.max(1000, props.slideDuration - 500)
    distributeInterval.value = Math.floor(availableTime / arr.length)
    distributeStart.value = 0
    baseInterval.value = distributeInterval.value
    distributeScale.value = 100
  }
  
  showDistributeModal.value = true
}

const cancelDistribution = () => {
  const key = distributeKey.value
  if (key && originalArrayBackup.value) {
    updateField(key, originalArrayBackup.value)
  }
  showDistributeModal.value = false
}

const confirmDistribution = () => {
  showDistributeModal.value = false
}

const smartDistribute = (centered = false) => {
  const key = distributeKey.value
  if (!key) return
  
  const arr = props.modelValue[key] || []
  const count = arr.length
  if (count > 0 && props.slideDuration > 0) {
    if (centered) {
      if (count === 1) {
        distributeStart.value = Math.floor(props.slideDuration / 2)
        distributeInterval.value = 0
      } else {
        const padding = Math.max(500, Math.floor(props.slideDuration * 0.1))
        const availableTime = props.slideDuration - (padding * 2)
        distributeStart.value = padding
        distributeInterval.value = Math.floor(availableTime / (count - 1))
      }
    } else {
      const availableTime = Math.max(1000, props.slideDuration - 500)
      distributeInterval.value = Math.floor(availableTime / count)
      distributeStart.value = 0
    }
    
    baseInterval.value = distributeInterval.value
    distributeScale.value = 100
  }
  
  applyDistribution()
}

const resetTimings = (key) => {
  if (!confirm('Сбросить все тайминги элементов в 0?')) return
  
  const arr = [...(props.modelValue[key] || [])]
  const newArr = arr.map((item) => {
    const newItem = { ...item }
    const k = key.toLowerCase()
    if ('time' in newItem || k.includes('director') || k.includes('event')) {
      newItem.time = 0
    }
    if ('start_time' in newItem || k.includes('message') || k.includes('chat')) {
      newItem.start_time = 0
    }
    return newItem
  })
  
  updateField(key, newArr)
}

const applyDistribution = () => {
  const key = distributeKey.value
  if (!key) return
  
  const arr = [...(originalArrayBackup.value || props.modelValue[key] || [])]
  const newArr = arr.map((item, index) => {
    const newItem = { ...item }
    const t = distributeStart.value + (index * distributeInterval.value)
    
    const k = key.toLowerCase()
    if ('time' in newItem || k.includes('director') || k.includes('event')) {
      newItem.time = t
    }
    if ('start_time' in newItem || k.includes('message') || k.includes('chat')) {
      newItem.start_time = t
    }
    
    return newItem
  })
  
  updateField(key, newArr)
}

watch([distributeStart, distributeInterval], () => {
  if (showDistributeModal.value) {
    applyDistribution()
  }
})

const currentKeys = computed(() => {
  const keys = new Set([...Object.keys(props.modelValue || {}), ...Object.keys(props.template || {})])
  if (keys.has('role') || keys.has('sender')) {
    keys.add('image')
  }
  
  let sortedKeys = Array.from(keys)
  
  if (props.hiddenKeys && props.hiddenKeys.length > 0) {
    sortedKeys = sortedKeys.filter(k => !props.hiddenKeys.includes(k))
  }
  
  if (props.modelValue && props.modelValue.type === 'image' && sortedKeys.includes('content')) {
    if (!sortedKeys.includes('image_position')) sortedKeys.push('image_position')
  }
  
  if (props.modelValue && props.modelValue.scroll === true) {
    if (!sortedKeys.includes('scroll_amount')) sortedKeys.push('scroll_amount')
  }
  
  sortedKeys.sort((a, b) => {
    const typeA = getType(a)
    const typeB = getType(b)
    const isComplexA = typeA === 'array' || typeA === 'object'
    const isComplexB = typeB === 'array' || typeB === 'object'
    
    if (isComplexA === isComplexB) return 0
    return isComplexA ? 1 : -1
  })
  
  return sortedKeys
})

const getType = (key) => {
  let val = getVal(key)
  
  if (key === 'is_main') return 'boolean'
  
  if (val === undefined || val === null) {
    if (isMediaField(key) || isIconField(key)) return 'string'
    if (isRoleField(key)) return 'string'
    if (isTimeField(key) || key === 'scroll_amount') return 'number'
    return 'string'
  }
  
  if (Array.isArray(val)) return 'array'
  if (typeof val === 'object') return 'object'
  return typeof val
}

const getVal = (key) => {
  if (key === 'is_main' && props.modelValue[key] === undefined && props.modelValue['type'] === 'core') {
    return true
  }
  return props.modelValue[key] !== undefined ? props.modelValue[key] : props.template[key]
}

// ── Schema-driven field typing (Iteration 1.1) ─────────────────────────────
// `props.schema` — это плоская карта { key: { type, ... } } (см. payload_schema).
// Тип инпута определяется по schema.type, а НЕ по имени ключа.
// Если ключа нет в схеме — fallback на старые эвристики (обратная совместимость).
const fieldSchema = (key) => {
  return props.schema?.[key] || null
}

const fieldType = (key) => {
  const s = fieldSchema(key)
  return (s && s.type) ? s.type : null
}

const isMediaField = (key) => {
  const k = key.toLowerCase()
  // Полиморфное поле `content` (BrowserMockup): картинка, когда sibling `type === 'image'`.
  if (k === 'content') return props.modelValue?.type === 'image'
  const t = fieldType(key)
  if (t) return t === 'image' || t === 'video' || t === 'audio'
  if (k === 'image_position') return false
  return k.includes('image') || k.includes('avatar') || k.includes('src') || k.includes('photo') || k.includes('logo') || k.includes('bg') || k.includes('media') || k.includes('video')
}

const isIconField = (key) => {
  const t = fieldType(key)
  if (t) return t === 'icon'
  const k = key.toLowerCase()
  return k.includes('icon')
}

const isTimeField = (key) => {
  const t = fieldType(key)
  if (t) return t === 'time'
  const k = key.toLowerCase()
  return k.includes('time') || k.includes('duration') || k.includes('delay')
}

const isRoleField = (key) => {
  const t = fieldType(key)
  const k = key.toLowerCase()
  if (t) return t === 'enum' && (k === 'role' || k === 'sender')
  return k === 'role' || k === 'sender'
}

const isLongText = (key) => {
  const k = key.toLowerCase()
  // Полиморфное поле `content`: textarea, когда sibling `type !== 'image'`.
  if (k === 'content') return props.modelValue?.type !== 'image'
  const t = fieldType(key)
  if (t) return t === 'long_text' || t === 'code' || t === 'html'
  if (isMediaField(key)) return false
  return k.includes('text') || k.includes('desc') || k.includes('message') || k.includes('content') || k.includes('code')
}

const isColorField = (key) => {
  const t = fieldType(key)
  if (t) return t === 'color' || t === 'gradient'
  const k = key.toLowerCase()
  return k.includes('color') || k.includes('bg') || k.includes('gradient') || k.includes('stroke') || k.includes('fill') || k.includes('shadow')
}

const isFloatField = (key) => {
  const t = fieldType(key)
  if (t) return t === 'number'
  const k = key.toLowerCase()
  return k.includes('scale') || k.includes('opacity') || k.includes('speed') || k.includes('factor')
}

const updateField = (key, value) => {
  const newData = { ...props.modelValue, [key]: value }
  emit('update:modelValue', newData)
}

const getArrayTemplate = (key) => {
  const arr = props.template[key]
  if (Array.isArray(arr) && arr.length > 0) {
    return arr[0]
  }
  return {}
}

const updateArrayItem = (key, index, newValue) => {
  const newArr = [...(props.modelValue[key] || [])]
  
  if (typeof newValue === 'object' && newValue !== null) {
    const oldItem = newArr[index] || {}
    
    // Mutually exclusive radio behavior for specific boolean flags (like is_focused)
    if (newValue.is_focused === true && oldItem.is_focused !== true) {
      newArr.forEach((item, i) => {
        if (i !== index && item && typeof item === 'object') {
          newArr[i] = { ...item, is_focused: false }
        }
      })
    }
    
    let timeField = null
    if ('time' in newValue) timeField = 'time'
    else if ('start_time' in newValue) timeField = 'start_time'
    
    if (timeField) {
      let t = Number(newValue[timeField])
      
      // Bypass gap enforcement and cascade shift if explicitly resetting to 0
      if (t !== 0) {
        // Enforce 100ms minimum gap from previous item
        if (index > 0) {
          const prevItem = newArr[index - 1]
          if (prevItem && typeof prevItem === 'object') {
            const prevT = Number(prevItem[timeField] !== undefined ? prevItem[timeField] : (prevItem.time !== undefined ? prevItem.time : prevItem.start_time))
            if (!isNaN(prevT) && t < prevT + 100) {
              t = prevT + 100
              newValue = { ...newValue, [timeField]: t }
            }
          }
        }
        
        const oldT = Number(oldItem[timeField])
        if (!isNaN(oldT) && !isNaN(t)) {
          const delta = t - oldT
          if (delta !== 0) {
            // Cascade shift subsequent items
            for (let i = index + 1; i < newArr.length; i++) {
              const subsequentItem = { ...newArr[i] }
              const subT = Number(subsequentItem[timeField])
              if (!isNaN(subT)) {
                subsequentItem[timeField] = subT + delta
                newArr[i] = subsequentItem
              }
            }
          }
        }
      }
    }
  }
  
  newArr[index] = newValue
  updateField(key, newArr)
}

const removeArrayItem = (key, index) => {
  const newArr = [...(props.modelValue[key] || [])]
  newArr.splice(index, 1)
  updateField(key, newArr)
}

const toggleNodeConnection = (key, nodeId) => {
  const arr = [...(props.modelValue[key] || [])]
  const idx = arr.indexOf(nodeId)
  if (idx > -1) arr.splice(idx, 1)
  else arr.push(nodeId)
  updateField(key, arr)
}

const addArrayItem = (key) => {
  const newArr = [...(props.modelValue[key] || [])]
  const templateItem = getArrayTemplate(key)
  
  let newItem
  if (typeof templateItem === 'object' && templateItem !== null) {
    newItem = JSON.parse(JSON.stringify(templateItem))
    if (newItem.id) {
      newItem.id = 'item_' + Math.random().toString(36).substring(2, 9)
    }
  } else if (typeof templateItem === 'string') {
    newItem = ""
  } else if (typeof templateItem === 'number') {
    newItem = 0
  } else {
    newItem = {}
  }
  
  newArr.push(newItem)
  updateField(key, newArr)
}
</script>
