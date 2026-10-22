import re

with open('core/src/composables/useScreenRecorder.js', 'r') as f:
    content = f.read()

# Add script loader
loader = """
  const loadFixWebmDuration = () => {
    return new Promise((resolve) => {
      if (window.ysFixWebmDuration) return resolve(window.ysFixWebmDuration)
      const script = document.createElement('script')
      script.src = 'https://unpkg.com/fix-webm-duration@1.0.6/fix-webm-duration.js'
      script.onload = () => resolve(window.ysFixWebmDuration)
      document.head.appendChild(script)
    })
  }
"""

if "loadFixWebmDuration" not in content:
    content = content.replace("export function useScreenRecorder() {", loader + "\nexport function useScreenRecorder() {")

# Track startTime
if "let autoStopTimer = null" in content:
    content = content.replace("let autoStopTimer = null", "let autoStopTimer = null\n  let recordingStartTime = 0")

if "mediaRecorder.start(1000)" in content:
    content = content.replace("mediaRecorder.start(1000)", "recordingStartTime = Date.now()\n      mediaRecorder.start(1000)")

# Fix blob saving
old_save = """      mediaRecorder.onstop = () => {
        clearAutoStop()
        removeCaptureOverlay()
        const blob = new Blob(recordedChunks, { type: mediaRecorder?.mimeType || 'video/webm' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        document.body.appendChild(a)
        a.style = 'display: none'
        a.href = url

        const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
        a.download = `presentation-live-capture-${timestamp}.webm`
        a.click()
        window.URL.revokeObjectURL(url)
        isRecording.value = false

        stopAllTracks()
      }"""

new_save = """      mediaRecorder.onstop = async () => {
        clearAutoStop()
        removeCaptureOverlay()
        const durationMs = Date.now() - recordingStartTime
        const rawBlob = new Blob(recordedChunks, { type: mediaRecorder?.mimeType || 'video/webm' })
        
        const saveBlob = (blobToSave) => {
          const url = URL.createObjectURL(blobToSave)
          const a = document.createElement('a')
          document.body.appendChild(a)
          a.style = 'display: none'
          a.href = url
          const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
          a.download = `presentation-live-capture-${timestamp}.webm`
          a.click()
          window.URL.revokeObjectURL(url)
          isRecording.value = false
          stopAllTracks()
        }

        try {
          const fixWebmDuration = await loadFixWebmDuration()
          fixWebmDuration(rawBlob, durationMs, (fixedBlob) => {
            saveBlob(fixedBlob)
          })
        } catch (e) {
          console.error("Failed to load fix-webm-duration, saving raw blob", e)
          saveBlob(rawBlob)
        }
      }"""

content = content.replace(old_save, new_save)

with open('core/src/composables/useScreenRecorder.js', 'w') as f:
    f.write(content)
