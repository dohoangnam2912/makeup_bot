import React, { useState } from 'react';
import MicPulseCircle from './MicPulseCircle';

export default function MicWaveRecorder() {
  const [recording, setRecording] = useState(false);

  const startRecording = () => {
    if (recording) return;
    setRecording(true);

    setTimeout(() => {
      setRecording(false);
    }, 3000);
  };

  return (
    <div className="relative flex flex-col items-center justify-center mt-8 w-full h-72">
      {recording && <MicPulseCircle />}

      <button
        onClick={startRecording}
        disabled={recording}
        className={`
          z-10 transition-transform duration-300
          ${recording ? 'scale-110' : 'hover:scale-110'}
        `}
      >
        <img src="/mic_icon.svg" alt="Mic" className="w-24 h-24" />
      </button>
    </div>
  );
}
