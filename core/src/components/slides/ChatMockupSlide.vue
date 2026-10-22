<template>
 <div :class="mobile ? 'flex flex-col items-stretch w-full mt-2 h-full min-h-0 pb-2' : 'w-full h-full flex items-stretch justify-center'">
 <ChatMockup :mobile="mobile" :title="title" :botName="bot_name" :botSubtitle="bot_subtitle" :botAvatar="bot_avatar" mode="director" :messages="filteredMessages" :clicks="clicks" :variant="variant" />
 </div>
</template>
<script setup>
import { computed } from 'vue'
import ChatMockup from '../ui/ChatMockup.vue'
import { useDirector } from '../../composables/useDirector.js'

const props = defineProps({ mobile: Boolean, title: String, bot_name: String, bot_subtitle: String, bot_avatar: String, mode: String, messages: Array, clicks: Number, variant: String, slideStartTime: { type: Number, default: 0 } })

const { currentTime } = useDirector()
const localTime = computed(() => Math.max(0, currentTime.value - props.slideStartTime))

const filteredMessages = computed(() => {
 return (props.messages || []).filter(msg => {
 const t = msg.start_time !== undefined ? Number(msg.start_time) : (Number(msg.time) || 0)
 return localTime.value >= t
 })
})
</script>