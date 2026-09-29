"""
VERITAS AI — Real Audio Forensic Features & Signal Extractor
Module: backend.app.services.audio_forensics

Extracts real measurable physical acoustic properties and frequency distributions
from audio files without claiming heuristic features are trained deepfake probabilities.
"""

import io
import math
import time
import wave
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
import numpy as np

from app.models.model_registry import model_registry

logger = logging.getLogger("veritas.forensics.audio")


@dataclass
class AudioForensicFeatures:
    """Measurable physical and acoustic properties extracted from audio data."""
    sample_rate: int
    channels: int
    duration_sec: float
    total_samples: int
    rms_energy: float
    zero_crossing_rate: float
    spectral_centroid_hz: float
    spectral_bandwidth_hz: float
    spectral_rolloff_hz: float
    mfcc_estimates: List[float]
    f0_estimate_hz: float
    silence_ratio: float
    clipping_ratio: float

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["rms_energy"] = round(self.rms_energy, 4)
        d["zero_crossing_rate"] = round(self.zero_crossing_rate, 4)
        d["spectral_centroid_hz"] = round(self.spectral_centroid_hz, 2)
        d["spectral_bandwidth_hz"] = round(self.spectral_bandwidth_hz, 2)
        d["spectral_rolloff_hz"] = round(self.spectral_rolloff_hz, 2)
        d["mfcc_estimates"] = [round(c, 4) for c in self.mfcc_estimates]
        d["f0_estimate_hz"] = round(self.f0_estimate_hz, 2)
        d["silence_ratio"] = round(self.silence_ratio, 4)
        d["clipping_ratio"] = round(self.clipping_ratio, 4)
        return d


class AudioFeatureExtractor:
    """
    Extracts deterministic physical acoustic and spectral domain features from audio waveforms.
    Does not require heavy GPU neural dependencies.
    """

    @staticmethod
    def extract_from_pcm(
        samples: np.ndarray,
        sample_rate: int,
        channels: int = 1
    ) -> AudioForensicFeatures:
        """
        Extracts acoustic features from normalized float NumPy audio samples [-1.0, 1.0].
        """
        if samples is None or len(samples) == 0:
            return AudioForensicFeatures(
                sample_rate=sample_rate, channels=channels, duration_sec=0.0,
                total_samples=0, rms_energy=0.0, zero_crossing_rate=0.0,
                spectral_centroid_hz=0.0, spectral_bandwidth_hz=0.0, spectral_rolloff_hz=0.0,
                mfcc_estimates=[0.0]*13, f0_estimate_hz=0.0, silence_ratio=1.0, clipping_ratio=0.0
            )

        # Convert to mono if multi-channel
        if samples.ndim > 1:
            samples = np.mean(samples, axis=1)

        N = len(samples)
        duration_sec = round(N / max(1, sample_rate), 3)

        # 1. RMS Energy
        rms = float(np.sqrt(np.mean(samples ** 2))) if N > 0 else 0.0

        # 2. Zero-Crossing Rate
        zcr = float(np.mean(np.abs(np.diff(np.sign(samples)))) / 2.0) if N > 1 else 0.0

        # 3. Clipping Ratio (samples >= 0.99)
        clipping_ratio = float(np.mean(np.abs(samples) >= 0.99)) if N > 0 else 0.0

        # 4. Silence Ratio (frames below -40dB RMS)
        frame_len = max(256, int(sample_rate * 0.025))  # 25ms frame
        hop_len = max(128, int(sample_rate * 0.010))    # 10ms hop
        num_frames = max(1, (N - frame_len) // hop_len + 1)
        silent_frames = 0
        threshold_amp = 10 ** (-40 / 20)  # -40 dB

        for i in range(num_frames):
            frame = samples[i * hop_len : i * hop_len + frame_len]
            f_rms = np.sqrt(np.mean(frame ** 2)) if len(frame) > 0 else 0.0
            if f_rms < threshold_amp:
                silent_frames += 1

        silence_ratio = float(silent_frames / max(1, num_frames))

        # 5. Spectral Domain Features (FFT)
        fft_size = 1024
        window = np.hanning(min(N, fft_size))
        pad_samples = samples[:fft_size] if N >= fft_size else np.pad(samples, (0, fft_size - N))
        spectrum = np.abs(np.fft.rfft(pad_samples * window))
        freqs = np.fft.rfftfreq(fft_size, d=1.0 / sample_rate)

        sum_spec = np.sum(spectrum) or 1e-9
        centroid = float(np.sum(freqs * spectrum) / sum_spec)
        bandwidth = float(np.sqrt(np.sum(((freqs - centroid) ** 2) * spectrum) / sum_spec))

        # Spectral Rolloff (85% energy threshold)
        cumsum_spec = np.cumsum(spectrum)
        rolloff_idx = np.where(cumsum_spec >= 0.85 * cumsum_spec[-1])[0]
        rolloff_hz = float(freqs[rolloff_idx[0]]) if len(rolloff_idx) > 0 else float(freqs[-1])

        # 6. MFCC Estimates (13 Triangular Filter-Bank approximations)
        mfcc = AudioFeatureExtractor._compute_approx_mfcc(spectrum, freqs, num_filters=13)

        # 7. Fundamental Frequency (F0) Estimation via Autocorrelation
        f0_hz = AudioFeatureExtractor._estimate_f0(samples, sample_rate)

        return AudioForensicFeatures(
            sample_rate=sample_rate,
            channels=channels,
            duration_sec=duration_sec,
            total_samples=N,
            rms_energy=rms,
            zero_crossing_rate=zcr,
            spectral_centroid_hz=centroid,
            spectral_bandwidth_hz=bandwidth,
            spectral_rolloff_hz=rolloff_hz,
            mfcc_estimates=mfcc,
            f0_estimate_hz=f0_hz,
            silence_ratio=silence_ratio,
            clipping_ratio=clipping_ratio
        )

    @staticmethod
    def _compute_approx_mfcc(spectrum: np.ndarray, freqs: np.ndarray, num_filters: int = 13) -> List[float]:
        """Approximates Mel-Frequency Cepstral Coefficients from FFT power spectrum."""
        if len(spectrum) == 0:
            return [0.0] * num_filters

        # Log mel filterbank energy
        bins = np.linspace(0, len(spectrum), num_filters + 2, dtype=int)
        energies = []
        for m in range(1, num_filters + 1):
            e = np.sum(spectrum[bins[m-1]:bins[m+1]])
            energies.append(np.log(max(1e-9, e)))

        # Discrete Cosine Transform (DCT-II)
        K = len(energies)
        mfcc = []
        for n in range(num_filters):
            val = sum(energies[k] * math.cos(math.pi * n * (k + 0.5) / K) for k in range(K))
            mfcc.append(float(val))
        return mfcc

    @staticmethod
    def _estimate_f0(samples: np.ndarray, sample_rate: int) -> float:
        """Estimates fundamental pitch frequency using autocorrelation in voice band [60Hz - 400Hz]."""
        if len(samples) < sample_rate // 20:
            return 0.0

        corr_len = min(len(samples), sample_rate)
        seg = samples[:corr_len]
        corr = np.correlate(seg, seg, mode='full')
        corr = corr[len(corr) // 2:]

        min_lag = int(sample_rate / 600.0)  # Max 600 Hz (supports high pitch voice & standard pitch)
        max_lag = int(sample_rate / 50.0)   # Min 50 Hz

        if max_lag >= len(corr) or min_lag >= max_lag:
            return 0.0

        peak_lag = min_lag + int(np.argmax(corr[min_lag:max_lag]))
        if peak_lag > 0 and corr[peak_lag] > 0.25 * corr[0]:
            return float(sample_rate / peak_lag)
        return 0.0

    @staticmethod
    def read_audio_file(file_path_or_bytes: Union[str, Path, bytes, None]) -> Tuple[np.ndarray, int, int]:
        """
        Reads audio file container or bytes into normalized NumPy samples [-1.0, 1.0].
        Returns: (samples, sample_rate, channels).
        If audio is absent, empty, or unreadable, returns (empty_array, 0, 0).
        """
        if file_path_or_bytes is None:
            return np.zeros(0, dtype=np.float32), 0, 0

        if isinstance(file_path_or_bytes, bytes):
            if len(file_path_or_bytes) == 0:
                return np.zeros(0, dtype=np.float32), 0, 0
            bio = io.BytesIO(file_path_or_bytes)
            try:
                with wave.open(bio, 'rb') as wf:
                    sr = wf.getframerate()
                    ch = wf.getnchannels()
                    sw = wf.getsampwidth()
                    raw = wf.readframes(wf.getnframes())
                    if len(raw) == 0:
                        return np.zeros(0, dtype=np.float32), sr, ch
                    if sw == 2:
                        data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
                    elif sw == 4:
                        data = np.frombuffer(raw, dtype=np.int32).astype(np.float32) / 2147483648.0
                    elif sw == 1:
                        data = (np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
                    elif sw == 3:
                        # 24-bit PCM
                        n_samples = len(raw) // 3
                        unpacked = np.zeros(n_samples, dtype=np.float32)
                        for i in range(n_samples):
                            b = raw[i*3 : (i+1)*3]
                            val = int.from_bytes(b, byteorder='little', signed=True)
                            unpacked[i] = val / 8388608.0
                        data = unpacked
                    else:
                        data = np.zeros(0, dtype=np.float32)
                    return data, sr, ch
            except Exception:
                return np.zeros(0, dtype=np.float32), 0, 0

        p = Path(file_path_or_bytes)
        if not p.exists() or not p.is_file() or p.stat().st_size == 0:
            return np.zeros(0, dtype=np.float32), 0, 0

        ext = p.suffix.lower()
        if ext == ".wav":
            try:
                with wave.open(str(p), 'rb') as wf:
                    sr = wf.getframerate()
                    ch = wf.getnchannels()
                    sw = wf.getsampwidth()
                    raw = wf.readframes(wf.getnframes())
                    if len(raw) == 0:
                        return np.zeros(0, dtype=np.float32), sr, ch
                    if sw == 2:
                        data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
                    elif sw == 4:
                        data = np.frombuffer(raw, dtype=np.int32).astype(np.float32) / 2147483648.0
                    elif sw == 1:
                        data = (np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
                    elif sw == 3:
                        # 24-bit PCM
                        n_samples = len(raw) // 3
                        unpacked = np.zeros(n_samples, dtype=np.float32)
                        for i in range(n_samples):
                            b = raw[i*3 : (i+1)*3]
                            val = int.from_bytes(b, byteorder='little', signed=True)
                            unpacked[i] = val / 8388608.0
                        data = unpacked
                    else:
                        data = np.zeros(0, dtype=np.float32)
                    return data, sr, ch
            except Exception:
                return np.zeros(0, dtype=np.float32), 0, 0

        return np.zeros(0, dtype=np.float32), 0, 0


audio_extractor = AudioFeatureExtractor()
