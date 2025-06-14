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

export default function ChatInterface() {
  const [messages, setMessages] = useState([])
  const [inputText, setInputText] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [recording, setRecording] = useState(false)
  const [chatHistories, setChatHistories] = useState([])
  const [currentChatId, setCurrentChatId] = useState(null)
  const [isSpeaking, setIsSpeaking] = useState(false)

  // Step-by-step state
  const [currentStepData, setCurrentStepData] = useState(null)
  const [currentStepIndex, setCurrentStepIndex] = useState(0)
  const [isInStepMode, setIsInStepMode] = useState(false)

  const messagesEndRef = useRef(null)
  const beepRef = useRef(null)
  const stepContainerRef = useRef(null)

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

  // Remove the current nextStep useCallback and replace with this:
  const nextStepRef = useRef(null)

  nextStepRef.current = () => {
    if (!currentStepData || currentStepIndex >= currentStepData.response.length) {
      // End of steps
      setIsInStepMode(false)
      setCurrentStepData(null)
      setCurrentStepIndex(0)
      speakText("Tutorial complete. You can now ask another question.")
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

    // Speak the current step
    speakText(currentStep)

    // Move to next step
    setCurrentStepIndex((prev) => prev + 1)
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

  // Replace the step progression useEffect with this:
  useEffect(() => {
    if (!isInStepMode) return

    let lastClickTime = 0
    const DEBOUNCE_TIME = 300

    const handleStepProgression = (event) => {
      const now = Date.now()
      if (now - lastClickTime < DEBOUNCE_TIME) return
      lastClickTime = now

      // Prevent default behavior for certain keys
      if (event.type === "keydown" && ["Space", "Enter", "ArrowRight", "ArrowDown"].includes(event.code)) {
        event.preventDefault()
      }

      if (
        event.type === "click" ||
        (event.type === "keydown" && ["Space", "Enter", "ArrowRight", "ArrowDown"].includes(event.code))
      ) {
        nextStepRef.current?.()
      }
    }

    document.addEventListener("click", handleStepProgression)
    document.addEventListener("keydown", handleStepProgression)

    return () => {
      document.removeEventListener("click", handleStepProgression)
      document.removeEventListener("keydown", handleStepProgression)
    }
  }, [isInStepMode])

  const playBeep = () => {
    beepRef.current?.play()
  }

  const speakText = async (text) => {
    try {
      setIsSpeaking(true)
      const formData = new FormData()
      formData.append("text", text)

      const ttsRes = await fetch("http://localhost:8000/routes/speak", {
        method: "POST",
        body: formData,
      })

      const audioBlob = await ttsRes.blob()
      const audioURL = URL.createObjectURL(audioBlob)
      const audio = new Audio(audioURL)

      return new Promise((resolve) => {
        audio.onended = () => {
          setIsSpeaking(false)
          resolve()
        }
        audio.onerror = () => {
          setIsSpeaking(false)
          resolve()
        }
        audio.play()
      })
    } catch (err) {
      console.error("TTS Error:", err)
      setIsSpeaking(false)
    }
  }

  const startStepByStep = async (data) => {
    setCurrentStepData(data)
    setCurrentStepIndex(0)
    setIsInStepMode(true)

    // Announce step-by-step mode
    const announcement = `Starting step-by-step tutorial with ${data.response.length} steps. Click anywhere or press any key to continue to each step.`
    await speakText(announcement)

    // Don't call nextStep here - let the user click to start
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
      })

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`)
      }

      const data = await res.json()
      console.log("Received response:", data)

      // Clear loading immediately after getting response
      setIsLoading(false)

      // Check if response is step-by-step format
      if (data.type === "step_by_step" && Array.isArray(data.response)) {
        await startStepByStep(data)
      } else {
        // Handle regular response
        const botText = data.response || data.text || "No response received"
        setMessages((prev) => [...prev, { from: "bot", text: botText }])
        // Don't await speakText - let it run in background
        speakText(botText)
      }

      // Save chat history
      saveChatHistory()
    } catch (err) {
      console.error("Error sending to chat backend:", err)
      setIsLoading(false)
      const errorMessage = "Bot is not responding. Please try again."
      setMessages((prev) => [...prev, { from: "bot", text: errorMessage }])
      speakText(errorMessage)
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
      })

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`)
      }

      const data = await res.json()
      const query = data.query || text

      setMessages((prev) => [...prev, { from: "user", text: query }])

      // Clear loading immediately after getting response
      setIsLoading(false)

      // Check if response is step-by-step format
      if (data.type === "step_by_step" && Array.isArray(data.response)) {
        await startStepByStep(data)
      } else {
        // Handle regular response
        const botText = data.response || data.text || "No response received"
        setMessages((prev) => [...prev, { from: "bot", text: botText }])
        speakText(botText)
      }

      // Save chat history
      saveChatHistory()
    } catch (err) {
      console.error("Error sending to chat backend:", err)
      setIsLoading(false)
      const errorMessage = "Bot is not responding. Please try again."
      setMessages((prev) => [...prev, { from: "bot", text: errorMessage }])
      speakText(errorMessage)
    }
  }

  const handleStartRecording = async () => {
    if (recording || isLoading) return

    playBeep()
    try {
      await recordVoiceUntilSilence({
        onStart: () => setRecording(true),
        onStop: async (blob) => {
          setRecording(false)
          const formData = new FormData()
          formData.append("audio", blob, "voice.wav")

          setIsLoading(true)
          try {
            const res = await fetch("http://localhost:8000/routes/transcribe", {
              method: "POST",
              body: formData,
            })

            if (!res.ok) {
              throw new Error(`HTTP error! status: ${res.status}`)
            }

            const data = await res.json()
            await handleChatAppend(data.transcript)
          } catch (err) {
            console.error("Error sending recording:", err)
            setIsLoading(false)
          }
        },
      })
    } catch (error) {
      console.error("Recording error:", error)
      setRecording(false)
      setIsLoading(false)
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
  }

  const deleteChatHistory = (chatId) => {
    const updatedHistories = chatHistories.filter((chat) => chat.id !== chatId)
    setChatHistories(updatedHistories)
    localStorage.setItem("makeup-chat-histories", JSON.stringify(updatedHistories))

    if (currentChatId === chatId) {
      startNewChat()
    }
  }

  // Function to record voice until silence
  const recordVoiceUntilSilence = async ({ onStart, onStop }) => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      alert("Your browser doesn't support audio recording")
      return
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      const audioChunks = []

      onStart()

      mediaRecorder.ondataavailable = (e) => {
        audioChunks.push(e.data)
      }

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunks, { type: "audio/wav" })
        onStop(audioBlob)

        // Stop all tracks to release microphone
        stream.getTracks().forEach((track) => track.stop())
      }

      // Start recording
      mediaRecorder.start()

      // Set a maximum recording time (15 seconds)
      setTimeout(() => {
        if (mediaRecorder.state === "recording") {
          mediaRecorder.stop()
        }
      }, 15000)

      // Set up silence detection
      const audioContext = new AudioContext()
      const audioStreamSource = audioContext.createMediaStreamSource(stream)
      const analyser = audioContext.createAnalyser()
      analyser.fftSize = 512
      analyser.minDecibels = -45
      analyser.maxDecibels = -10
      analyser.smoothingTimeConstant = 0.5
      audioStreamSource.connect(analyser)

      const bufferLength = analyser.frequencyBinCount
      const dataArray = new Uint8Array(bufferLength)

      let silenceStart = Date.now()
      const silenceDelay = 1500 // 1.5 seconds of silence before stopping

      const checkSilence = () => {
        analyser.getByteFrequencyData(dataArray)

        // Check if there's audio
        let sum = 0
        for (let i = 0; i < bufferLength; i++) {
          sum += dataArray[i]
        }

        const average = sum / bufferLength

        if (average <= 5) {
          // Silence threshold
          if (Date.now() - silenceStart >= silenceDelay) {
            if (mediaRecorder.state === "recording") {
              mediaRecorder.stop()
            }
            return
          }
        } else {
          silenceStart = Date.now()
        }

        // Continue checking if still recording
        if (mediaRecorder.state === "recording") {
          requestAnimationFrame(checkSilence)
        }
      }

      // Start silence detection after a short delay
      setTimeout(() => {
        silenceStart = Date.now()
        checkSilence()
      }, 500)
    } catch (err) {
      console.error("Error accessing microphone:", err)
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
                    <SidebarMenuItem key={chat.id}>
                      <SidebarMenuButton
                        onClick={() => loadChatHistory(chat.id)}
                        disabled={isInStepMode}
                        className={`w-full justify-start group ${
                          currentChatId === chat.id ? "bg-pink-100 text-pink-800" : ""
                        } ${isInStepMode ? "opacity-50 cursor-not-allowed" : ""}`}
                      >
                        <MessageCircle className="w-4 h-4 mr-2 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <div className="truncate text-sm">{chat.title}</div>
                          <div className="text-xs text-gray-500">{chat.timestamp.toLocaleDateString()}</div>
                        </div>
                        <div
                          onClick={(e) => {
                            e.stopPropagation()
                            deleteChatHistory(chat.id)
                          }}
                          className="opacity-0 group-hover:opacity-100 transition-opacity p-1 h-auto cursor-pointer hover:bg-red-100 rounded disabled:opacity-0"
                        >
                          <Trash2 className="w-3 h-3 text-red-500" />
                        </div>
                      </SidebarMenuButton>
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
            <div className="sticky top-0 z-20 p-4 bg-white/95 backdrop-blur-sm border-b border-gray-100 shadow-sm">
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
                  <div className="ml-auto">
                    <div className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
                      Step Mode Active
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Messages */}
            <ScrollArea className="flex-1">
              <div className="space-y-4 max-w-4xl mx-auto p-4">
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
                            : "Ask me anything about makeup and beauty..."
                      }
                      disabled={isInStepMode || isLoading}
                      className="h-16 pr-12 text-base border-slate-300 rounded-lg placeholder-slate-400 focus:outline-none focus:border-slate-200 focus:ring-1 focus:ring-slate-200 disabled:opacity-50"
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={recording ? () => setRecording(false) : handleStartRecording}
                      disabled={isInStepMode || isLoading}
                      className={`absolute right-2 top-1/2 -translate-y-1/2 h-16 w-16 p-0 ${
                        recording ? "text-red-500 hover:text-red-600" : "text-gray-400 hover:text-pink-500"
                      } disabled:opacity-50`}
                    >
                      {recording ? <MicOff className="w-6 h-6" /> : <Mic className="w-6 h-6" />}
                    </Button>
                  </div>
                  <Button
                    type="submit"
                    disabled={!inputText.trim() || isInStepMode || isLoading}
                    className="h-16 w-16 p-3 flex items-center justify-center bg-gradient-to-r from-pink-500 to-purple-500 hover:from-pink-600 hover:to-purple-600 rounded-lg disabled:opacity-50"
                  >
                    <Send className="w-5 h-5" />
                  </Button>
                </div>
              </form>
              <div className="px-4 pb-4 pt-2 text-center">
                <p className="text-m text-gray-500">
                  {isInStepMode
                    ? "Step-by-step mode: Click anywhere or press any key to continue"
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
