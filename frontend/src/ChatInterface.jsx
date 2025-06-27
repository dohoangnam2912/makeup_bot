"use client"

import { useState, useEffect, useRef } from "react"
import { Card } from "./components/ui/card"
import { Input } from "./components/ui/input"
import { Button } from "./components/ui/button"
import { ScrollArea } from "./components/ui/scroll-area"
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarProvider,
  SidebarTrigger,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarInset,
} from "./components/ui/sidebar"
import { Mic, MicOff, Send, Sparkles, MessageCircle, Trash2, Plus, ChevronRight } from "lucide-react"

// Improved voice recording function with better debugging
export const recordVoiceUntilSilence = async ({
  silenceThreshold = 8,
  silenceDuration = 2000,
  onStop = () => {},
  onStart = () => {},
  onVolumeChange = () => {},
}) => {
  try {
    console.log("🎙️ Requesting microphone access...")
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
        sampleRate: 44100,
      },
    })

    console.log("🎙️ Microphone access granted")

    // Try different MIME types for better compatibility
    let mimeType = "audio/webm;codecs=opus"
    if (!MediaRecorder.isTypeSupported(mimeType)) {
      mimeType = "audio/webm"
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = "audio/mp4"
        if (!MediaRecorder.isTypeSupported(mimeType)) {
          mimeType = "" // Use default
        }
      }
    }

    console.log("🎙️ Using MIME type:", mimeType || "default")

    const mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined)
    const chunks = []

    onStart()
    console.log("🎙️ Recording started")

    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) {
        chunks.push(e.data)
        console.log("🎙️ Audio chunk received:", e.data.size, "bytes")
      }
    }

    mediaRecorder.start(100) // Collect data every 100ms

    const audioContext = new (window.AudioContext || window.webkitAudioContext)()
    const source = audioContext.createMediaStreamSource(stream)
    const analyser = audioContext.createAnalyser()
    analyser.fftSize = 2048
    source.connect(analyser)

    const bufferLength = analyser.fftSize
    const dataArray = new Uint8Array(bufferLength)
    let silenceStart = null
    let hasDetectedSound = false

    const checkSilence = () => {
      if (mediaRecorder.state !== "recording") return

      analyser.getByteTimeDomainData(dataArray)

      let sum = 0
      for (let i = 0; i < bufferLength; i++) {
        sum += Math.abs(dataArray[i] - 128)
      }
      const volume = sum / bufferLength
      const now = Date.now()

      // Call volume change callback for visual feedback
      onVolumeChange(volume)

      if (volume > silenceThreshold) {
        hasDetectedSound = true
        silenceStart = null
        console.log("🎙️ Sound detected, volume:", volume.toFixed(2))
      } else if (hasDetectedSound) {
        // Only start silence detection after we've detected some sound
        if (!silenceStart) {
          silenceStart = now
          console.log("🎙️ Silence started")
        } else if (now - silenceStart > silenceDuration) {
          console.log("🎙️ Silence duration exceeded, stopping recording")
          mediaRecorder.stop()
          stream.getTracks().forEach((t) => t.stop())
          audioContext.close()
          return
        }
      }

      requestAnimationFrame(checkSilence)
    }

    checkSilence()

    mediaRecorder.onstop = () => {
      console.log("🎙️ Recording stopped, total chunks:", chunks.length)
      const blob = new Blob(chunks, { type: mimeType || "audio/wav" })
      console.log("🎙️ Final blob size:", blob.size, "bytes, type:", blob.type)
      onStop(blob)
    }

    mediaRecorder.onerror = (event) => {
      console.error("🎙️ MediaRecorder error:", event.error)
      stream.getTracks().forEach((t) => t.stop())
      audioContext.close()
    }

    // Fallback timeout (30 seconds max)
    setTimeout(() => {
      if (mediaRecorder.state === "recording") {
        console.log("🎙️ Maximum recording time reached, stopping")
        mediaRecorder.stop()
        stream.getTracks().forEach((t) => t.stop())
        audioContext.close()
      }
    }, 30000)
  } catch (err) {
    console.error("🎙️ Voice recording failed:", err)
    throw err
  }
}

export default function ChatInterface() {
  const [messages, setMessages] = useState([])
  const [inputText, setInputText] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [recording, setRecording] = useState(false)
  const [chatHistories, setChatHistories] = useState([])
  const [currentChatId, setCurrentChatId] = useState(null)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [micPermission, setMicPermission] = useState(null)
  const [audioLevel, setAudioLevel] = useState(0)
  const [recordingDuration, setRecordingDuration] = useState(0)

  // Step-by-step state
  const [currentStepData, setCurrentStepData] = useState(null)
  const [currentStepIndex, setCurrentStepIndex] = useState(0)
  const [isInStepMode, setIsInStepMode] = useState(false)
  const [isProcessingStep, setIsProcessingStep] = useState(false)

  const messagesEndRef = useRef(null)
  const beepRef = useRef(null)
  const stepContainerRef = useRef(null)
  const recordingTimerRef = useRef(null)

  const allPredefinedQuestionsRef = useRef([
    "What are some popular makeup techniques?",
    "Can you recommend products for oily skin?",
    "How do I choose the right foundation color?",
    "What's a good skincare routine for beginners?",
    "What are the latest beauty trends?",
    "How to solve common makeup problems like cakey foundation?",
    "What are some tips for long-lasting lipstick?",
    "How to properly cleanse my face?",
    "What's the difference between serum and moisturizer?",
    "Any advice for covering dark circles?",
    "How to get a natural makeup look?",
    "What eyeshadow colors suit brown eyes?",
  ])
  const [randomSuggestions, setRandomSuggestions] = useState([])

  // Check microphone permission on mount
  useEffect(() => {
    const checkMicPermission = async () => {
      try {
        const result = await navigator.permissions.query({ name: "microphone" })
        setMicPermission(result.state)

        result.addEventListener("change", () => {
          setMicPermission(result.state)
        })
      } catch (err) {
        console.log("Permission API not supported")
      }
    }

    checkMicPermission()
  }, [])

  const nextStep = async () => {
    if (!currentStepData || isProcessingStep) {
      return
    }

    setIsProcessingStep(true)

    try {
      // Check if we've reached the end of steps
      if (currentStepIndex >= currentStepData.response.length) {
        // End of steps
        setIsInStepMode(false)
        setCurrentStepData(null)
        setCurrentStepIndex(0)
        const completionMessage = "Tutorial complete. You can now ask another question."
        await speakText(completionMessage)
        return
      }

      const currentStep = currentStepData.response[currentStepIndex]

      // Add the current step as a bot message
      setMessages((prev) => [
        ...prev,
        {
          from: "bot",
          text: currentStep,
          isStep: true,
          stepNumber: currentStepIndex + 1,
          totalSteps: currentStepData.response.length,
        },
      ])

      // ALWAYS speak the current step - no matter what
      await speakText(currentStep)

      // Move to next step
      setCurrentStepIndex((prev) => prev + 1)
    } finally {
      setIsProcessingStep(false)
    }
  }

  useEffect(() => {
    if (messages.length === 0) {
      const shuffled = [...allPredefinedQuestionsRef.current].sort(() => 0.5 - Math.random())
      setRandomSuggestions(shuffled.slice(0, 3))
    }
  }, [messages.length])

  // Load chat histories from localStorage
  useEffect(() => {
    const saved = localStorage.getItem("makeup-chat-histories")
    if (saved) {
      const parsed = JSON.parse(saved).map((chat) => ({
        ...chat,
        timestamp: new Date(chat.timestamp),
      }))
      setChatHistories(parsed)
    }
  }, [])

  // Preload beep sound
  useEffect(() => {
    beepRef.current = new Audio("/beep.mp3")
    beepRef.current.volume = 1
  }, [])

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  // Handle keyboard and click events for step progression
  useEffect(() => {
    const handleStepProgression = async (event) => {
      if (isInStepMode && currentStepData && !isProcessingStep) {
        // Prevent default behavior for certain keys
        if (event.type === "keydown" && ["Space", "Enter", "ArrowRight", "ArrowDown"].includes(event.code)) {
          event.preventDefault()
        }

        if (
          event.type === "click" ||
          (event.type === "keydown" && ["Space", "Enter", "ArrowRight", "ArrowDown"].includes(event.code))
        ) {
          await nextStep()
        }
      }
    }

    if (isInStepMode) {
      document.addEventListener("click", handleStepProgression)
      document.addEventListener("keydown", handleStepProgression)

      // Focus the step container for better accessibility
      stepContainerRef.current?.focus()
    }

    return () => {
      document.removeEventListener("click", handleStepProgression)
      document.removeEventListener("keydown", handleStepProgression)
    }
  }, [isInStepMode, currentStepData, isProcessingStep, currentStepIndex])

  const playBeep = () => {
    beepRef.current?.play().catch((err) => console.log("Beep sound failed:", err))
  }

  // Enhanced speakText function that ALWAYS tries to speak
  const speakText = async (text) => {
    if (!text || !text.trim()) {
      console.log("🔊 No text to speak")
      return
    }

    try {
      console.log("🔊 Starting TTS for:", text.substring(0, 50) + "...")
      setIsSpeaking(true)

      const formData = new FormData()
      formData.append("text", text.trim())

      const ttsRes = await fetch("http://localhost:8000/routes/synthesize", {
        method: "POST",
        body: formData,
      })

      if (!ttsRes.ok) {
        console.error("🔊 TTS request failed:", ttsRes.status)
        throw new Error(`TTS request failed: ${ttsRes.status}`)
      }

      const audioBlob = await ttsRes.blob()
      console.log("🔊 TTS audio blob received:", audioBlob.size, "bytes")

      const audioURL = URL.createObjectURL(audioBlob)
      const audio = new Audio(audioURL)

      return new Promise((resolve) => {
        audio.onended = () => {
          console.log("🔊 TTS playback completed")
          setIsSpeaking(false)
          URL.revokeObjectURL(audioURL)
          resolve()
        }
        audio.onerror = (error) => {
          console.error("🔊 TTS playback error:", error)
          setIsSpeaking(false)
          URL.revokeObjectURL(audioURL)
          resolve()
        }
        audio.play().catch((playError) => {
          console.error("🔊 TTS play failed:", playError)
          setIsSpeaking(false)
          URL.revokeObjectURL(audioURL)
          resolve()
        })
      })
    } catch (err) {
      console.error("🔊 TTS Error:", err)
      setIsSpeaking(false)
      // Don't throw error - just log it and continue
    }
  }

  const startStepByStep = async (data) => {
    setCurrentStepData(data)
    setCurrentStepIndex(0)
    setIsInStepMode(true)
    setIsProcessingStep(false)

    // Announce step-by-step mode
    const announcement = `Starting step-by-step tutorial with ${data.response.length} steps. Click anywhere or press any key to continue to each step.`

    // Add announcement message
    setMessages((prev) => [
      ...prev,
      {
        from: "bot",
        text: announcement,
        isStep: false,
      },
    ])

    // ALWAYS speak the announcement
    await speakText(announcement)
  }

  const handleChatAppendText = async (text) => {
    if (!text.trim() || isLoading) return

    console.log("Sending message:", text)

    setIsLoading(true)
    setMessages((prev) => [...prev, { from: "user", text: text }])

    try {
      const res = await fetch("http://localhost:8000/routes/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: text,
          session_id: "c9eddb5c-020b-55d3-90cf-9a3c66b03dc1",
          timestamp: new Date().toISOString(),
        }),
        credentials: 'include'
      })

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`)
      }

      const data = await res.json()
      console.log("Received response:", data)

      // Check if response is step-by-step format
      if (data.type === "step_by_step" && Array.isArray(data.response)) {
        await startStepByStep(data)
      } else {
        // Handle regular response
        const botText = data.response || data.text || "No response received"
        setMessages((prev) => [...prev, { from: "bot", text: botText }])

        // ALWAYS speak the response - no matter what
        await speakText(botText)
      }

      // Save chat history
      saveChatHistory()
    } catch (err) {
      console.error("Error sending to chat backend:", err)
      const errorMessage = "Bot is not responding. Please try again."
      setMessages((prev) => [...prev, { from: "bot", text: errorMessage }])

      // ALWAYS speak error messages too
      await speakText(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  const handleChatAppend = async (text) => {
    if (!text.trim() || isLoading) return

    console.log("Sending voice message:", text)

    setIsLoading(true)

    try {
      const res = await fetch("http://localhost:8000/routes/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: text,
          session_id: "c9eddb5c-020b-55d3-90cf-9a3c66b03dc1",
          timestamp: new Date().toISOString(),
        }),
        credentials: 'include'
      })

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`)
      }

      const data = await res.json()
      const query = data.query || text

      setMessages((prev) => [...prev, { from: "user", text: query }])

      // Check if response is step-by-step format
      if (data.type === "step_by_step" && Array.isArray(data.response)) {
        await startStepByStep(data)
      } else {
        // Handle regular response
        const botText = data.response || data.text || "No response received"
        setMessages((prev) => [...prev, { from: "bot", text: botText }])

        // ALWAYS speak the response - no matter what
        await speakText(botText)
      }

      // Save chat history
      saveChatHistory()
    } catch (err) {
      console.error("Error sending to chat backend:", err)
      const errorMessage = "Bot is not responding. Please try again."
      setMessages((prev) => [...prev, { from: "bot", text: errorMessage }])

      // ALWAYS speak error messages too
      await speakText(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  const handleStartRecording = async () => {
    if (recording || isLoading) return

    // Check microphone permission first
    if (micPermission === "denied") {
      const permissionMessage =
        "Microphone access is denied. Please enable microphone permissions in your browser settings."
      alert(permissionMessage)
      // Even speak permission errors
      await speakText(permissionMessage)
      return
    }

    playBeep()

    // Start recording duration timer
    setRecordingDuration(0)
    recordingTimerRef.current = setInterval(() => {
      setRecordingDuration((prev) => prev + 1)
    }, 1000)

    try {
      console.log("🎙️ Starting voice recording...")

      await recordVoiceUntilSilence({
        silenceThreshold: 8,
        silenceDuration: 2000,
        onStart: () => {
          console.log("🎙️ Recording started")
          setRecording(true)
        },
        onVolumeChange: (volume) => {
          setAudioLevel(Math.min(100, (volume / 20) * 100))
        },
        onStop: async (blob) => {
          console.log("🎙️ Recording stopped, blob size:", blob.size, "bytes")
          setRecording(false)
          setAudioLevel(0)

          // Clear recording timer
          if (recordingTimerRef.current) {
            clearInterval(recordingTimerRef.current)
            recordingTimerRef.current = null
          }

          if (blob.size === 0) {
            console.error("❌ Empty audio blob received")
            const errorMsg = "No audio was recorded. Please try speaking louder or check your microphone."
            alert(errorMsg)
            await speakText(errorMsg)
            return
          }

          if (blob.size < 1000) {
            console.error("❌ Audio blob too small:", blob.size, "bytes")
            const errorMsg = "Recording too short. Please try speaking for a longer duration."
            alert(errorMsg)
            await speakText(errorMsg)
            return
          }

          // Create FormData with proper field name matching your backend
          const formData = new FormData()

          // Try different field names that your backend might expect
          formData.append("audio", blob, "voice.wav")
          formData.append("file", blob, "voice.wav") // Alternative field name

          console.log("🎙️ Sending audio for transcription...")
          console.log("📤 FormData entries:")
          for (const [key, value] of formData.entries()) {
            console.log(`  ${key}:`, value)
          }

          setIsLoading(true)
          try {
            const res = await fetch("http://localhost:8000/routes/transcribe", {
              method: "POST",
              body: formData,
            })

            console.log("📥 Transcription response status:", res.status)
            console.log("📥 Transcription response headers:", Object.fromEntries(res.headers.entries()))

            if (!res.ok) {
              const errorText = await res.text()
              console.error("❌ Transcription failed:", res.status, errorText)
              throw new Error(`Transcription failed: ${res.status} - ${errorText}`)
            }

            const responseText = await res.text()
            console.log("📥 Raw transcription response:", responseText)

            let data
            try {
              data = JSON.parse(responseText)
            } catch (parseError) {
              console.error("❌ Failed to parse JSON response:", parseError)
              throw new Error("Invalid JSON response from transcription service")
            }

            console.log("📥 Parsed transcription result:", data)

            const transcript = data.transcript || data.text || data.transcription || ""
            if (transcript.trim()) {
              console.log("✅ Transcript received:", transcript)
              await handleChatAppend(transcript)
            } else {
              console.warn("⚠️ Empty transcript received")
              const errorMsg = "Could not understand the audio. Please try speaking more clearly."
              alert(errorMsg)
              await speakText(errorMsg)
              setIsLoading(false)
            }
          } catch (err) {
            console.error("❌ Error processing recording:", err)
            setIsLoading(false)

            let errorMessage = ""
            // More specific error messages
            if (err.message.includes("Failed to fetch")) {
              errorMessage = "Network error: Could not connect to transcription service. Please check your connection."
            } else if (err.message.includes("500")) {
              errorMessage = "Server error: The transcription service is having issues. Please try again later."
            } else if (err.message.includes("400")) {
              errorMessage = "Bad request: The audio format may not be supported. Please try again."
            } else {
              errorMessage = `Transcription error: ${err.message}`
            }

            alert(errorMessage)
            // ALWAYS speak error messages
            await speakText(errorMessage)
          }
        },
      })
    } catch (error) {
      console.error("❌ Recording error:", error)
      setRecording(false)
      setAudioLevel(0)
      setIsLoading(false)

      // Clear recording timer
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current)
        recordingTimerRef.current = null
      }

      let errorMessage = ""
      if (error.name === "NotAllowedError") {
        errorMessage = "Microphone access denied. Please allow microphone access and try again."
      } else if (error.name === "NotFoundError") {
        errorMessage = "No microphone found. Please check your microphone connection."
      } else {
        errorMessage = "Failed to start recording. Please check your microphone and try again."
      }

      alert(errorMessage)
      // ALWAYS speak error messages
      await speakText(errorMessage)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (inputText.trim() && !isInStepMode && !isLoading) {
      const messageText = inputText.trim()
      setInputText("") // Clear input immediately
      handleChatAppendText(messageText)
    }
  }

  const saveChatHistory = () => {
    if (messages.length === 0) return

    const title = messages[0]?.text?.slice(0, 50) + "..." || "New Chat"
    const chatHistory = {
      id: currentChatId || Date.now().toString(),
      title,
      messages,
      timestamp: new Date(),
    }

    const updatedHistories = currentChatId
      ? chatHistories.map((chat) => (chat.id === currentChatId ? chatHistory : chat))
      : [chatHistory, ...chatHistories]

    setChatHistories(updatedHistories)
    localStorage.setItem("makeup-chat-histories", JSON.stringify(updatedHistories))

    if (!currentChatId) {
      setCurrentChatId(chatHistory.id)
    }
  }

  const loadChatHistory = (chatId) => {
    if (isInStepMode) return // Prevent loading during step mode

    const chat = chatHistories.find((c) => c.id === chatId)
    if (chat) {
      setMessages(chat.messages)
      setCurrentChatId(chatId)
    }
  }

  const startNewChat = () => {
    if (isInStepMode) return

    setMessages([])
    setCurrentChatId(null)
    setInputText("")
    setIsInStepMode(false)
    setCurrentStepData(null)
    setCurrentStepIndex(0)
    setIsLoading(false)
    setIsSpeaking(false)
    setIsProcessingStep(false)
  }

  const deleteChatHistory = (chatId) => {
    const updatedHistories = chatHistories.filter((chat) => chat.id !== chatId)
    setChatHistories(updatedHistories)
    localStorage.setItem("makeup-chat-histories", JSON.stringify(updatedHistories))

    if (currentChatId === chatId) {
      startNewChat()
    }
  }

  return (
    <SidebarProvider>
      <div className="flex h-screen w-screen bg-gradient-to-br from-pink-50 to-purple-50">
        <Sidebar className="bg-slate-50 border-r border-slate-200">
          <SidebarHeader className="border-b border-slate-200 p-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-r from-pink-500 to-purple-500 rounded-full flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              <h2 className="font-semibold text-gray-800">Momo</h2>
            </div>
            <Button
              onClick={startNewChat}
              disabled={isInStepMode}
              className="w-full mt-3 bg-gradient-to-r from-pink-400 to-purple-400 text-white hover:from-pink-500 hover:to-purple-500 disabled:opacity-50"
            >
              <Plus className="w-4 h-4 mr-2" />
              New Chat
            </Button>
          </SidebarHeader>

          <SidebarContent>
            <SidebarGroup>
              <SidebarGroupLabel className="text-gray-600">Chat History</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {chatHistories.map((chat) => (
                  <SidebarMenuItem key={chat.id} className="group/item"> {/* Add group here */}
                    <div className="flex items-center w-full"> {/* Flex container */}
                      {/* Main clickable area for loading the chat */}
                      <SidebarMenuButton
                        onClick={() => loadChatHistory(chat.id)}
                        disabled={isInStepMode}
                        className={`flex-grow justify-start ${ // Use flex-grow
                          currentChatId === chat.id ? "bg-pink-100 text-pink-800" : ""
                        } ${isInStepMode ? "opacity-50 cursor-not-allowed" : ""}`}
                      >
                        <MessageCircle className="w-4 h-4 mr-2 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <div className="truncate text-sm">{chat.title}</div>
                          <div className="text-xs text-gray-500">{chat.timestamp.toLocaleDateString()}</div>
                        </div>
                      </SidebarMenuButton>

                      {/* Separate delete button, positioned to the side */}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          // No need for stopPropagation if they are separate buttons
                          deleteChatHistory(chat.id)
                        }}
                        disabled={isInStepMode}
                        // Use the group from the SidebarMenuItem to control visibility
                        className="opacity-0 group-hover/item:opacity-100 transition-opacity p-1 h-auto disabled:opacity-0 ml-2 flex-shrink-0"
                      >
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    </div>
                  </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          </SidebarContent>
        </Sidebar>

        <SidebarInset className="flex-1">
          <div className="flex flex-col h-full bg-white">
            {/* Header */}
            <div className="sticky top-0 z-10 p-4 bg-white/95 backdrop-blur-sm border-b border-gray-100">
              <div className="flex items-center gap-3">
                <SidebarTrigger />
                <div className="flex items-center gap-2">
                  <div className="w-10 h-10 bg-gradient-to-r from-pink-500 to-purple-500 rounded-full flex items-center justify-center">
                    <Sparkles className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h1 className="text-xl font-bold bg-gradient-to-r from-pink-600 to-purple-600 bg-clip-text text-transparent">
                      Momo
                    </h1>
                    <p className="text-sm text-gray-600">Your personal makeup consultant</p>
                  </div>
                </div>
                {isInStepMode && (
                  <div className="ml-auto flex items-center gap-2">
                    <div className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
                      Step Mode Active
                    </div>
                    {currentStepData && (
                      <div className="bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-sm">
                        {currentStepIndex}/{currentStepData.response.length}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Recording status */}
              {recording && (
                <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                    <span className="text-sm font-medium text-red-800">Recording</span>
                  </div>
                  <div className="flex items-center gap-1">
                    {[...Array(5)].map((_, i) => (
                      <div
                        key={i}
                        className={`w-1 h-4 rounded-full transition-colors ${
                          audioLevel > (i + 1) * 20 ? "bg-red-500" : "bg-gray-300"
                        }`}
                      />
                    ))}
                  </div>
                  <span className="text-sm text-red-600">{recordingDuration}s</span>
                </div>
              )}
            </div>

            {/* Messages */}
            <ScrollArea className="flex-1 p-4">
              <div className="space-y-4 max-w-4xl mx-auto px-4" ref={stepContainerRef} tabIndex={-1}>
                {messages.length === 0 && (
                  <Card className="p-6 mt-32 text-center border-none shadow-none flex flex-col items-center justify-center">
                    <div className="w-16 h-16 bg-gradient-to-r from-pink-500 to-purple-500 rounded-full flex items-center justify-center mx-auto mb-4">
                      <Sparkles className="w-8 h-8 text-white" />
                    </div>
                    <h3 className="text-3xl font-semibold text-gray-800 mb-1">Welcome to Momo! ✨</h3>
                    <p className="text-xl text-gray-600 mb-2 text-center">
                      I'm here to help with all your makeup and beauty questions!
                    </p>
                    {randomSuggestions.length > 0 && (
                      <div className="flex flex-col sm:flex-row gap-3 mt-6 w-full max-w-3xl px-4 sm:px-0">
                        {randomSuggestions.map((question) => (
                          <button
                            key={question}
                            onClick={() => handleChatAppendText(question)}
                            disabled={isInStepMode || isLoading}
                            className="flex-1 p-4 bg-white border border-gray-100 rounded-xl text-sm font-medium 
                              bg-gradient-to-r from-blue-400 via-pink-400 to-purple-400 
                              bg-clip-text text-transparent 
                              hover:bg-gray-50 
                              transition-colors duration-150 ease-in-out 
                              focus:outline-none
                              shadow-sm hover:shadow-md
                              disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            {question}
                          </button>
                        ))}
                      </div>
                    )}
                  </Card>
                )}

                {messages.map((message, index) => (
                  <div key={index} className={`flex ${message.from === "user" ? "justify-end" : "justify-start"}`}>
                    <Card
                      className={`max-w-md p-4 ${
                        message.from === "user"
                          ? "bg-gradient-to-r from-pink-400 to-purple-400 text-white border-0"
                          : message.isStep
                            ? "bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200 max-w-5xl"
                            : "bg-white border-none shadow-none max-w-5xl"
                      }`}
                    >
                      {message.isStep && (
                        <div className="flex items-center gap-2 mb-2 text-blue-600">
                          <ChevronRight className="w-4 h-4" />
                          <span className="text-sm font-medium">
                            Step {message.stepNumber} of {message.totalSteps}
                          </span>
                        </div>
                      )}
                      <div className="whitespace-pre-wrap">{message.text}</div>
                    </Card>
                  </div>
                ))}

                {isLoading && (
                  <div className="flex justify-start">
                    <Card className="max-w-[80%] p-4 bg-white/80 backdrop-blur-sm border-pink-200">
                      <div className="flex items-center gap-2 mb-2">
                        <div className="w-6 h-6 bg-gradient-to-r from-pink-500 to-purple-500 rounded-full flex items-center justify-center">
                          <Sparkles className="w-3 h-3 text-white" />
                        </div>
                        <span className="text-sm font-medium text-gray-700">Momo</span>
                      </div>
                      <div className="w-48 h-6 bg-gray-300 rounded-lg animate-pulse" />
                    </Card>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>

            {/* Input */}
            <div className="sticky bottom-0 z-10 bg-white">
              <form onSubmit={handleSubmit} className="max-w-4xl mx-auto p-4">
                <div className="flex gap-2">
                  <div className="flex-1 relative">
                    <Input
                      value={inputText}
                      onChange={(e) => setInputText(e.target.value)}
                      placeholder={
                        isInStepMode
                          ? "Step mode active - click anywhere to continue"
                          : isLoading
                            ? "Momo is thinking..."
                            : recording
                              ? "Recording... speak now!"
                              : "Ask me anything about makeup and beauty..."
                      }
                      disabled={isInStepMode || isLoading || recording}
                      className="h-16 pr-12 text-base border-slate-300 rounded-lg placeholder-slate-400 focus:outline-none focus:border-slate-200 focus:ring-1 focus:ring-slate-200 disabled:opacity-50"
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={handleStartRecording}
                      disabled={isInStepMode || isLoading}
                      className={`absolute right-2 top-1/2 -translate-y-1/2 h-16 w-16 p-0 ${
                        recording
                          ? "text-red-500 hover:text-red-600 animate-pulse"
                          : micPermission === "denied"
                            ? "text-gray-300"
                            : "text-gray-400 hover:text-pink-500"
                      } disabled:opacity-50`}
                      title={
                        micPermission === "denied"
                          ? "Microphone access denied"
                          : recording
                            ? "Recording... (speak now)"
                            : "Click to record voice message"
                      }
                    >
                      {recording ? <MicOff className="w-6 h-6" /> : <Mic className="w-6 h-6" />}
                    </Button>
                  </div>
                  <Button
                    type="submit"
                    disabled={!inputText.trim() || isInStepMode || isLoading || recording}
                    className="h-16 w-16 p-3 flex items-center justify-center bg-gradient-to-r from-pink-500 to-purple-500 hover:from-pink-600 hover:to-purple-600 rounded-lg disabled:opacity-50"
                  >
                    <Send className="w-5 h-5" />
                  </Button>
                </div>
              </form>
              <div className="px-4 pb-4 pt-2 text-center">
                <p className="text-sm text-gray-500">
                  {isInStepMode
                    ? "Step-by-step mode: Click anywhere or press any key to continue"
                    : recording
                      ? "🎙️ Recording... Speak clearly and I'll stop when you're done!"
                      : "Momo can make mistakes, so double check it."}
                </p>
              </div>
            </div>
          </div>
        </SidebarInset>
      </div>
    </SidebarProvider>
  )
}
