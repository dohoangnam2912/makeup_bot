import React, { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import MicPulseCircle from '../components/MicPulseCircle';
import { recordVoiceUntilSilence } from '../utils/useVoiceRecorder';

export default function ChatInterface() {
  const location = useLocation();
  const initialMessage = location.state?.initialMessage;

  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [recording, setRecording] = useState(false);
  const [sidebarVisible, setSidebarVisible] = useState(true);
  const hasAppendedInitialRef = useRef(false);
  const scrollRef = useRef(null);
  const beepRef = useRef(null);

  // 🔊 Preload beep
  useEffect(() => {
    beepRef.current = new Audio('/beep.mp3');
    beepRef.current.volume = 1;
  }, []);

  const playBeep = () => {
    beepRef.current?.play();
  };

  // 🧠 Cuộn xuống cuối khi có tin nhắn mới
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // ✅ Append initial message 1 lần duy nhất
  useEffect(() => {
    if (!initialMessage || hasAppendedInitialRef.current) return;

    handleChatAppend(initialMessage);
    hasAppendedInitialRef.current = true;
  }, [initialMessage]);

  const handleChatAppend = async (text) => {
    // const userMsg = { from: 'user', text };
    // setMessages((prev) => [...prev, userMsg]); // Đảm bảo không lặp lại
    setIsLoading(true);
  
    try {
      const res = await fetch('http://localhost:8000/routes/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: text,
          session_id: 'frontend-simple-session',
          model: 'gemini-2.0-flash',
          timestamp: new Date().toISOString(),
        }),
      });
  
      const data = await res.json();
      const botText = data.response;
      const rewrittenPrompt = data.rewritten_question;  // Câu hỏi đã viết lại từ LLM
      // Thêm câu hỏi đã viết lại (rewritten_question) vào messages
      setMessages((prev) => [...prev, { from: 'user', text: rewrittenPrompt }]);
      // Chỉ thêm tin nhắn của bot vào messages, không thêm tin nhắn người dùng lần nữa
      setMessages((prev) => [...prev, { from: 'bot', text: botText }]);
  
      // Xử lý TTS nếu cần
      try {
        const formData = new FormData();
        formData.append("text", botText);
  
        const res = await fetch("http://localhost:8000/routes/speak", {
          method: "POST",
          body: formData,
        });
  
        const audioBlob = await res.blob();
        const audioURL = URL.createObjectURL(audioBlob);
        new Audio(audioURL).play();
      } catch (err) {
        console.error("Lỗi TTS:", err);
      }
    } catch (err) {
      console.error('Lỗi khi gửi tới chat backend:', err);
      setMessages((prev) => [...prev, { from: 'bot', text: 'Bot không phản hồi.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartRecording = async () => {
    if (recording) return;

    playBeep();

    await recordVoiceUntilSilence({
      onStart: () => setRecording(true),
      onStop: async (blob) => {
        setRecording(false);
        const formData = new FormData();
        formData.append('audio', blob, 'voice.wav');

        setIsLoading(true);
        try {
          const res = await fetch('http://localhost:8000/routes/transcribe', {
            method: 'POST',
            body: formData,
          });

          const data = await res.json();
          await handleChatAppend(data.transcript);
        } catch (err) {
          console.error('❌ Lỗi khi gửi ghi âm:', err);
        } finally {
          setIsLoading(false);
        }
      },
    });
  };
  const getMessageClass = (from) =>
    `w-fit max-w-[70%] break-words px-4 py-3 text-base leading-relaxed whitespace-pre-line ${
      from === 'user'
        ? 'ml-auto bg-rose-100 text-black font-semibold rounded-xl text-right shadow-md'
        : 'mr-auto bg-white text-black rounded-xl shadow border border-gray-200'
    }`;
  
  
  return (
    <div
      onClick={(e) => {
        if (e.target.tagName === "BUTTON" || e.target.closest("button")) return;
        handleStartRecording();
      }}
      className="min-h-screen flex bg-gradient-to-b from-pink-100 to-white text-gray-800 relative"
    >
      {/* Sidebar Toggle Button */}
      {!sidebarVisible && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            setSidebarVisible(true);
          }}
          className="absolute top-4 left-4 w-5 h-5 bg-purple-500 rounded-sm z-50"
          title="Mở lại menu"
        />
      )}

      {/* Sidebar */}
      {sidebarVisible && (
        <aside className="w-56 bg-white rounded-2xl shadow-xl p-4 m-4 flex flex-col gap-4">
          <div className="flex justify-between items-center">
            <div
              onClick={(e) => {
                e.stopPropagation();
                setSidebarVisible(false);
              }}
              className="w-6 h-6 rounded-sm bg-red-500 cursor-pointer hover:scale-110 transition"
              title="Ẩn menu"
            />
            <div
              onClick={(e) => {
                e.stopPropagation();
                setMessages([]);
              }}
              className="w-6 h-6 rounded-sm bg-blue-500 cursor-pointer hover:scale-110 transition"
              title="Chat mới"
            />
          </div>
          <div className="text-sm text-gray-600 mt-1">Hôm nay</div>
          <div className="bg-white hover:bg-gray-100 rounded-xl p-4 text-sm border border-transparent hover:border-gray-300 transition cursor-pointer">
            <p className="font-semibold text-gray-700">Cách trang điểm A</p>
          </div>
        </aside>
      )}

      {/* Chat Main */}
      {/* <main className="flex-1 flex flex-col justify-between px-6 md:px-16 py-4 w-full"> */}
      <main className="flex-1 flex flex-col justify-between px-4 py-4 max-w-4xl mx-auto w-full">
        <div className="flex-1 overflow-y-auto space-y-4 pt-8 pb-44">
          {messages.map((msg, idx) => (
            <div key={idx} className={getMessageClass(msg.from)}>
              {msg.text}
            </div>
          ))}

          {isLoading && (
            <div className="w-48 h-6 bg-gray-300 rounded-lg animate-pulse mr-auto" />
          )}

          <div ref={scrollRef} />
        </div>
      </main>

      {/* Footer mask */}
      <div className="fixed bottom-0 left-0 w-full h-24 z-40 pointer-events-none bg-gradient-to-t from-pink-100/95 to-transparent backdrop-blur-sm" />

      {/* Mic button */}
      <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 flex flex-col items-center gap-3 z-50">
        <div className="relative w-16 h-16 flex items-center justify-center z-10">
          {recording && <MicPulseCircle size="w-32 h-32" />}
          <button
            aria-label="Ghi âm"
            onClick={(e) => {
              e.stopPropagation();
              handleStartRecording();
            }}
            className={`transition-transform duration-300 ${
              recording ? 'scale-110' : 'hover:scale-110'
            }`}
          >
            <img src="/mic_icon.svg" alt="Mic" className="w-24 h-24" />
          </button>
        </div>
        <p className="text-gray-500 text-lg md:text-base text-center">
          Bấm vào nút mic hoặc bất kỳ đâu trên màn hình để bắt đầu trò chuyện
        </p>
      </div>
    </div>
  );
}
