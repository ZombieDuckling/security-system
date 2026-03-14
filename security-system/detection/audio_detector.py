"""Audio detection for voice commands and safe word detection."""

import threading
import numpy as np
from typing import Callable, Optional, List
import collections


class AudioDetector:
    """Detects audio events including safe word and voice commands using simple energy detection."""

    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_size: int = 1024,
        energy_threshold: float = 0.02,
        safe_word_callback: Optional[Callable] = None,
        voice_command_callback: Optional[Callable] = None,
    ):
        self._sample_rate = sample_rate
        self._chunk_size = chunk_size
        self._energy_threshold = energy_threshold
        self._safe_word_callback = safe_word_callback
        self._voice_command_callback = voice_command_callback
        self._running = False
        self._thread = None
        self._stream = None

        # Simple command patterns (energy-based triggers)
        self._commands = {
            "arm": ["up", "up"],
            "disarm": ["down", "down"],
            "help": ["help", "help"],
            "stop": ["stop", "stop"],
        }
        self._recent_patterns = collections.deque(maxlen=10)

    def _compute_energy(self, audio_data: np.ndarray) -> float:
        """Compute RMS energy of audio chunk."""
        return np.sqrt(np.mean(audio_data**2))

    def _detect_peak(self, energy: float) -> bool:
        """Detect if energy spike represents a clap/sound event."""
        return energy > self._energy_threshold

    def _start_audio(self):
        """Start audio capture thread."""
        try:
            import sounddevice as sd

            self._running = True

            def audio_callback(indata, frames, time, status):
                if not self._running:
                    return

                # Compute energy of this chunk
                energy = self._compute_energy(indata[:, 0])

                # Detect sound events
                if self._detect_peak(energy):
                    self._recent_patterns.append(energy)

                    # Check for patterns (double clap for safe word)
                    if len(self._recent_patterns) >= 2:
                        recent = list(self._recent_patterns)[-2:]
                        if all(e > self._energy_threshold for e in recent):
                            if self._safe_word_callback:
                                self._safe_word_callback()

                            if self._voice_command_callback:
                                # Simple double-peak detection
                                self._voice_command_callback("double_peak")

            self._stream = sd.InputStream(
                samplerate=self._sample_rate,
                blocksize=self._chunk_size,
                channels=1,
                callback=audio_callback,
            )
            self._stream.start()

        except ImportError:
            print("[AudioDetector] sounddevice not available, audio detection disabled")
        except Exception as e:
            print(f"[AudioDetector] Error starting audio: {e}")

    def start(self):
        """Start the audio detector."""
        if self._running:
            return
        self._thread = threading.Thread(target=self._start_audio, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the audio detector."""
        self._running = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    def set_safe_word_callback(self, callback: Callable):
        """Set callback for safe word detection."""
        self._safe_word_callback = callback

    def set_voice_command_callback(self, callback: Callable):
        """Set callback for voice command detection."""
        self._voice_command_callback = callback

    def is_available(self) -> bool:
        """Check if audio input is available."""
        try:
            import sounddevice as sd

            return len(sd.query_devices()) > 0
        except:
            return False


class SafeWordDetector:
    """Detects safe word using clap/sound pattern (double clap)."""

    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_size: int = 1024,
        energy_threshold: float = 0.03,
    ):
        self._sample_rate = sample_rate
        self._chunk_size = chunk_size
        self._energy_threshold = energy_threshold
        self._running = False
        self._stream = None
        self._thread = None

        # Track clap intervals
        self._clap_times = []
        self._callback = None

    def _detect_clap(self, energy: float) -> bool:
        """Detect if energy spike is a clap."""
        return energy > self._energy_threshold

    def _check_safe_word(self):
        """Check if double clap pattern detected within time window."""
        import time

        current_time = time.time()

        # Remove old claps (> 1 second ago)
        self._clap_times = [t for t in self._clap_times if current_time - t < 1.0]

        if len(self._clap_times) >= 2:
            # Double clap detected - trigger safe word
            if self._callback:
                self._callback()
            self._clap_times = []  # Reset after triggering

    def _audio_callback(self, indata, frames, time, status):
        if not self._running:
            return

        energy = np.sqrt(np.mean(indata[:, 0] ** 2))

        if self._detect_clap(energy):
            import time

            self._clap_times.append(time.time())
            self._check_safe_word()

    def start(self, callback: Callable):
        """Start listening for safe word (double clap)."""
        self._callback = callback
        self._running = True

        try:
            import sounddevice as sd

            self._stream = sd.InputStream(
                samplerate=self._sample_rate,
                blocksize=self._chunk_size,
                channels=1,
                callback=self._audio_callback,
            )
            self._stream.start()
        except ImportError:
            print("[SafeWordDetector] sounddevice not available")
        except Exception as e:
            print(f"[SafeWordDetector] Error: {e}")

    def stop(self):
        """Stop listening for safe word."""
        self._running = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    def is_available(self) -> bool:
        """Check if audio input is available."""
        try:
            import sounddevice as sd

            return len(sd.query_devices()) > 0
        except:
            return False
