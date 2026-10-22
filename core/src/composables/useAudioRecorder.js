import { ref } from 'vue'
import { useDirector } from './useDirector.js'

export const useAudioRecorder = (onRecordComplete) => {
  const isRecording = ref(false)
  const recordingTrackId = ref(null)
  
  let mediaRecorder = null
  let audioChunks = []
  let recordingStartTime = 0
  
  const { currentTime, play, pause, setAudioMute } = useDirector()

  const startRecording = async (trackId) => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      
      // Pick the best supported MIME type
      const preferredTypes = [
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/ogg;codecs=opus',
        'audio/ogg',
        'audio/mp4',
      ]
      const mimeType = preferredTypes.find(t => MediaRecorder.isTypeSupported(t)) || ''
      
      mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : {})
      audioChunks = []
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.push(event.data)
        }
      }
      
      mediaRecorder.onstop = () => {
        // Use the actual mimeType that was negotiated, not a hardcoded one
        const actualMime = mediaRecorder.mimeType || mimeType || 'audio/webm'
        
        // Derive a proper file extension from the MIME type
        let ext = 'webm'
        if (actualMime.includes('ogg')) ext = 'ogg'
        else if (actualMime.includes('mp4')) ext = 'mp4'
        
        const blob = new Blob(audioChunks, { type: actualMime })
        const file = new File([blob], `recording-${Date.now()}.${ext}`, { type: actualMime })
        
        if (onRecordComplete) {
          onRecordComplete({
            trackId: recordingTrackId.value,
            file,
            startTime: recordingStartTime
          })
        }
        
        recordingTrackId.value = null
        isRecording.value = false
        setAudioMute(false) // Unmute sounds after recording
        
        // Stop all tracks to release mic
        stream.getTracks().forEach(track => track.stop())
      }
      
      recordingTrackId.value = trackId
      isRecording.value = true
      recordingStartTime = currentTime.value
      setAudioMute(true) // Mute sounds during recording
      
      mediaRecorder.start()
      play() // Auto-play presentation while recording
      
    } catch (err) {
      console.error("Microphone access denied or error:", err)
      alert("Не удалось получить доступ к микрофону. Проверьте разрешения браузера.")
    }
  }

  const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop()
      pause() // Auto-pause when stopping recording
      setAudioMute(false) // Safely unmute here too just in case
    }
  }

  const toggleRecording = (trackId) => {
    if (isRecording.value && recordingTrackId.value === trackId) {
      stopRecording()
    } else if (!isRecording.value) {
      startRecording(trackId)
    }
  }

  return {
    isRecording,
    recordingTrackId,
    startRecording,
    stopRecording,
    toggleRecording
  }
}
