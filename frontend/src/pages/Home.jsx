import React, { useState, useEffect } from 'react';
import MicPulseCircle from '../components/MicPulseCircle';
import { useNavigate } from 'react-router-dom';
import { recordVoiceUntilSilence } from '../utils/useVoiceRecorder';

export default function Home() {
  const navigate = useNavigate();
  const [recording, setRecording] = useState(false);
  const [navigated, setNavigated] = useState(false);
  const [greeted, setGreeted] = useState(false);

  const playGreeting = async () => {
    try {
      const formData = new FormData();
      formData.append("text", "Xin chào! Bạn có thể bấm vào bất kì đâu trên màn hình để bắt đầu trò chuyện.");

      const res = await fetch("http://localhost:8000/routes/speak", {
        method: "POST",
        body: formData,
      });

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);

      const audio = new Audio(url);
      audio.play();
    } catch (err) {
      console.error("❌ Lỗi phát âm thanh:", err);
    }
  };
  const playBeep = () => {
    const beep = new Audio('/beep.mp3');
    beep.volume = 1; // ✅ Nếu muốn nhỏ đi
    beep.play();
  };
  
  const handleStartRecording = async () => {
    if (recording || navigated) return;
  
    if (!greeted) {
      await playGreeting(); // 🔊 Gọi chào trước
      setGreeted(true);
      return;
    }
  
    // 🎵 Play tiếng beep báo hiệu trước khi thu âm
    playBeep();
  
    await recordVoiceUntilSilence({
      onStart: () => setRecording(true),
      onStop: async (blob) => {
        if (navigated) return;
  
        setRecording(false);

        const formData = new FormData();
        formData.append('audio', blob, 'voice.wav');

        try {
          const res = await fetch('http://localhost:8000/routes/transcribe', {
            method: 'POST',
            body: formData,
          });

          const data = await res.json();
          const transcript = data.transcript;

          setNavigated(true);
          navigate("/chat", { state: { initialMessage: transcript } });
        } catch (err) {
          console.error('❌ Lỗi khi gửi audio:', err);
        }
      },
    });
  };

  return (
    <div
      onClick={(e) => {
        if (e.target.tagName === "BUTTON" || e.target.closest("button")) {
          return;
        }
        handleStartRecording();
      }}
      className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-b from-pink-100 to-white text-center px-4 relative"
    >
      <h1 className="text-4xl md:text-5xl font-bold text-gray-800 mb-6">
        Tôi có thể giúp bạn làm đẹp hôm nay thế nào?
      </h1>

      <p className="text-gray-500 text-lg md:text-xl mb-50">
        Bấm vào nút mic hoặc bất kỳ đâu trên màn hình để bắt đầu trò chuyện
      </p>

      <div className="relative w-24 h-24 flex items-center justify-center z-10">
        {recording && <MicPulseCircle />}
        <button
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
    </div>
  );
}
