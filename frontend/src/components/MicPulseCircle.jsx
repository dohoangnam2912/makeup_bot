import React from 'react';

export default function MicPulseCircle({ size = 'w-60 h-60' }) {
  return (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
      <span className={`absolute ${size} rounded-full border border-black opacity-30 animate-ping`} />
      <span className={`absolute ${size} rounded-full border border-black opacity-10 animate-ping delay-200`} />
      <span className={`absolute ${size} rounded-full border border-black opacity-5 animate-ping delay-500`} />
    </div>
  );
}