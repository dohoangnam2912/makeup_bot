export const recordVoiceUntilSilence = async ({
    silenceThreshold = 5,
    silenceDuration = 2500,
    onStop = () => {},
    onStart = () => {},
  }) => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      const chunks = [];
  
      onStart();
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.push(e.data);
      };
  
      mediaRecorder.start();
  
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 2048;
      source.connect(analyser);
  
      const bufferLength = analyser.fftSize;
      const dataArray = new Uint8Array(bufferLength);
      let silenceStart = null;
  
      const checkSilence = () => {
        analyser.getByteTimeDomainData(dataArray);
  
        let sum = 0;
        for (let i = 0; i < bufferLength; i++) {
          sum += Math.abs(dataArray[i] - 128);
        }
        const volume = sum / bufferLength;
        const now = Date.now();
  
        if (volume < silenceThreshold) {
          if (!silenceStart) silenceStart = now;
          else if (now - silenceStart > silenceDuration) {
            mediaRecorder.stop();
            stream.getTracks().forEach((t) => t.stop());
            audioContext.close();
            return;
          }
        } else {
          silenceStart = null;
        }
  
        requestAnimationFrame(checkSilence);
      };
  
      checkSilence();
  
      mediaRecorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'audio/wav' });
        onStop(blob);
      };
    } catch (err) {
      console.error('🎙 Voice recording failed:', err);
    }
  };