"""
VERITAS AI — Real Audio Deepfake & Speech Anti-Spoofing Detector
Module: backend.app.models.audio_deepfake_detector

Integrates the genuine RawNet2 end-to-end neural anti-spoofing architecture (ASVspoof 2021 baseline)
for CPU-optimized synthetic voice and deepfake speech classification.
Provides audio segmentation, quality analysis, aggregation, grounded timelines, and failure isolation.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple, Union
from pathlib import Path
from dataclasses import dataclass, field, asdict
import logging
import time
import math
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from app.models.model_registry import model_registry
from app.services.audio_forensics import audio_extractor, AudioForensicFeatures

logger = logging.getLogger("veritas.models.audio_deepfake")

DEFAULT_RAWNET2_WEIGHTS = Path(__file__).resolve().parent.parent / "weights" / "rawnet2_asvspoof2021.pth"


# =============================================================================
# 1. Abstract Base & Mock Fallback Detector
# =============================================================================

class AudioDeepfakeDetector(ABC):
    """Abstract base detector interface for speech anti-spoofing & voice clone detection."""

    @abstractmethod
    def analyze(self, media_path_or_bytes: Any) -> Dict[str, Any]:
        """Performs deepfake speech analysis and returns structured forensic payload."""
        pass


class MockAudioDetector(AudioDeepfakeDetector):
    """
    Simulated demo detector for speech forensics.
    Explicitly labeled as DEMO MODE // SIMULATED AUDIO DETECTION.
    """
    def __init__(self, model_version: str = "VERITAS-AUDIO-MOCK-v0.1"):
        self.model_version = model_version
        self.model_name = "Wav2Vec2 + Mel Vocoder Authenticator (Simulated)"
        self.is_mock = True
        self.detection_mode = "DEMO MODE // SIMULATED AUDIO DETECTION"

    def analyze(self, media_path_or_bytes: Any) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "model_version": self.model_version,
            "category": "Audio AI",
            "detection_mode": self.detection_mode,
            "is_mock": True,
            "classification_status": "ANALYZED",
            "score": 73,
            "confidence": 88,
            "maximum_spoof_score": 78,
            "mean_spoof_score": 68,
            "aggregate_spoof_score": 73,
            "score_standard_deviation": 5.2,
            "segment_count": 2,
            "segments_analyzed": 2,
            "segments": [
                {
                    "segment_id": "seg-0",
                    "start_timestamp": 0.0,
                    "end_timestamp": 4.0,
                    "spoof_probability": 0.68,
                    "prediction_confidence": 85,
                    "inference_latency_ms": 14.5,
                    "model_name": self.model_name,
                    "model_version": self.model_version,
                    "is_mock": True
                },
                {
                    "segment_id": "seg-1",
                    "start_timestamp": 2.0,
                    "end_timestamp": 6.0,
                    "spoof_probability": 0.78,
                    "prediction_confidence": 88,
                    "inference_latency_ms": 14.2,
                    "model_name": self.model_name,
                    "model_version": self.model_version,
                    "is_mock": True
                }
            ],
            "highest_risk_segment": {
                "segment_id": "seg-1",
                "start_timestamp": 2.0,
                "end_timestamp": 6.0,
                "spoof_probability": 0.78
            },
            "signals": [
                {
                    "id": "sig-aud-mock-1",
                    "name": "Audio Spectral Formant Anomaly (Simulated)",
                    "category": "audio",
                    "severity": "medium",
                    "confidence": 85,
                    "affectedRegionOrTime": "3.8kHz - 5.2kHz Band [00:07.30]",
                    "explanation": "Unnatural linear phase coherence across upper harmonic formants typical of neural vocoders."
                },
                {
                    "id": "sig-aud-mock-2",
                    "name": "Neural Voice Synthesis Indicator (Simulated)",
                    "category": "audio",
                    "severity": "high",
                    "confidence": 88,
                    "affectedRegionOrTime": "Voice Track [00:06 - 00:18]",
                    "explanation": "Mel-spectrogram zero-crossing distribution matches acoustic footprint of diffusion voice cloning."
                }
            ],
            "timeline": [
                {
                    "id": "aud-tm-mock-1",
                    "start_timestamp": 2.0,
                    "end_timestamp": 6.0,
                    "formatted_time": "00:02.0–00:06.0",
                    "event_type": "HIGH_SPOOF_SCORE",
                    "severity": "HIGH",
                    "spoof_score": 78,
                    "explanation": "Simulated voice cloning anomaly."
                }
            ],
            "latency_ms": 29.0
        }


# =============================================================================
# 2. RawNet2 Architecture (ASVspoof 2021 Baseline)
# =============================================================================

class SincConv(nn.Module):
    """
    Sinc-convolution layer implementing learnable/mel-initialized bandpass filters
    operating directly on raw 1D audio waveforms.
    """
    @staticmethod
    def to_mel(hz: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        return 2595.0 * np.log10(1.0 + hz / 700.0)

    @staticmethod
    def to_hz(mel: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        return 700.0 * (10.0 ** (mel / 2595.0) - 1.0)

    def __init__(
        self,
        out_channels: int = 20,
        kernel_size: int = 1024,
        in_channels: int = 1,
        sample_rate: int = 16000,
        stride: int = 1,
        padding: int = 0,
        dilation: int = 1
    ):
        super(SincConv, self).__init__()
        if in_channels != 1:
            raise ValueError(f"SincConv only supports single input channel (received {in_channels})")

        self.out_channels = out_channels
        self.kernel_size = kernel_size if kernel_size % 2 != 0 else kernel_size + 1
        self.sample_rate = sample_rate
        self.stride = stride
        self.padding = padding
        self.dilation = dilation

        # Initialize filterbanks using Mel scale
        NFFT = 512
        f = (self.sample_rate / 2.0) * np.linspace(0, 1, int(NFFT / 2) + 1)
        fmel = self.to_mel(f)
        fmelmax = np.max(fmel)
        fmelmin = np.min(fmel)
        filbandwidthsmel = np.linspace(fmelmin, fmelmax, self.out_channels + 1)
        self.mel = self.to_hz(filbandwidthsmel)
        self.hsupp = torch.arange(-(self.kernel_size - 1) / 2.0, (self.kernel_size - 1) / 2.0 + 1.0)
        self.band_pass = torch.zeros(self.out_channels, self.kernel_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        device = x.device
        hsupp = self.hsupp.to(device)
        band_pass = torch.zeros(self.out_channels, self.kernel_size, device=device)
        hamming_win = torch.hamming_window(self.kernel_size, periodic=False, device=device)

        for i in range(len(self.mel) - 1):
            fmin = float(self.mel[i])
            fmax = float(self.mel[i + 1])
            # sinc(x) in PyTorch is sin(pi*x)/(pi*x)
            hHigh = (2.0 * fmax / self.sample_rate) * torch.sinc(2.0 * fmax * hsupp / self.sample_rate)
            hLow = (2.0 * fmin / self.sample_rate) * torch.sinc(2.0 * fmin * hsupp / self.sample_rate)
            hideal = hHigh - hLow
            band_pass[i, :] = hamming_win * hideal

        filters = band_pass.view(self.out_channels, 1, self.kernel_size)
        return F.conv1d(x, filters, stride=self.stride, padding=self.padding, dilation=self.dilation, bias=None, groups=1)


class ResidualBlock(nn.Module):
    """Residual convolutional block with LeakyReLU activations and max pooling."""
    def __init__(self, in_channels: int, out_channels: int, first: bool = False):
        super(ResidualBlock, self).__init__()
        self.first = first
        if not self.first:
            self.bn1 = nn.BatchNorm1d(num_features=in_channels)
        self.lrelu = nn.LeakyReLU(negative_slope=0.3)
        self.conv1 = nn.Conv1d(in_channels=in_channels, out_channels=out_channels, kernel_size=3, padding=1, stride=1)
        self.bn2 = nn.BatchNorm1d(num_features=out_channels)
        self.conv2 = nn.Conv1d(in_channels=out_channels, out_channels=out_channels, kernel_size=3, padding=1, stride=1)

        self.downsample = in_channels != out_channels
        if self.downsample:
            self.conv_downsample = nn.Conv1d(in_channels=in_channels, out_channels=out_channels, kernel_size=1, padding=0, stride=1)
        self.mp = nn.MaxPool1d(3)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        identity = x
        if not self.first:
            out = self.bn1(x)
            out = self.lrelu(out)
        else:
            out = x

        out = self.conv1(out)
        out = self.bn2(out)
        out = self.lrelu(out)
        out = self.conv2(out)

        if self.downsample:
            identity = self.conv_downsample(identity)

        out += identity
        out = self.mp(out)
        return out


class RawNet2(nn.Module):
    """
    RawNet2 Neural Architecture for End-to-End Speech Anti-Spoofing.
    Architecture:
      SincConv (20 filters) -> 6 Residual Blocks with Feature Map Scaling (FMS) -> 3-layer GRU -> FC -> LogSoftmax(2)
    """
    def __init__(self):
        super(RawNet2, self).__init__()
        self.Sinc_conv = SincConv(out_channels=20, kernel_size=1024, in_channels=1, sample_rate=16000)
        self.first_bn = nn.BatchNorm1d(num_features=20)
        self.selu = nn.SELU(inplace=True)

        self.block0 = nn.Sequential(ResidualBlock(in_channels=20, out_channels=20, first=True))
        self.block1 = nn.Sequential(ResidualBlock(in_channels=20, out_channels=20))
        self.block2 = nn.Sequential(ResidualBlock(in_channels=20, out_channels=128))
        self.block3 = nn.Sequential(ResidualBlock(in_channels=128, out_channels=128))
        self.block4 = nn.Sequential(ResidualBlock(in_channels=128, out_channels=128))
        self.block5 = nn.Sequential(ResidualBlock(in_channels=128, out_channels=128))
        self.avgpool = nn.AdaptiveAvgPool1d(1)

        self.fc_attention0 = nn.Sequential(nn.Linear(20, 20))
        self.fc_attention1 = nn.Sequential(nn.Linear(20, 20))
        self.fc_attention2 = nn.Sequential(nn.Linear(128, 128))
        self.fc_attention3 = nn.Sequential(nn.Linear(128, 128))
        self.fc_attention4 = nn.Sequential(nn.Linear(128, 128))
        self.fc_attention5 = nn.Sequential(nn.Linear(128, 128))

        self.bn_before_gru = nn.BatchNorm1d(num_features=128)
        self.gru = nn.GRU(input_size=128, hidden_size=1024, num_layers=3, batch_first=True)
        self.fc1_gru = nn.Linear(1024, 1024)
        self.fc2_gru = nn.Linear(1024, 2, bias=True)

        self.sig = nn.Sigmoid()
        self.logsoftmax = nn.LogSoftmax(dim=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Expected input shape: (batch, num_samples) or (batch, 1, num_samples)
        if x.ndim == 2:
            x = x.unsqueeze(1)

        x = self.Sinc_conv(x)
        x = F.max_pool1d(torch.abs(x), 3)
        x = self.first_bn(x)
        x = self.selu(x)

        # Block 0 + FMS Attention
        x0 = self.block0(x)
        y0 = self.avgpool(x0).view(x0.size(0), -1)
        y0 = self.fc_attention0(y0)
        y0 = self.sig(y0).view(y0.size(0), y0.size(1), -1)
        x = x0 * y0 + y0

        # Block 1 + FMS Attention
        x1 = self.block1(x)
        y1 = self.avgpool(x1).view(x1.size(0), -1)
        y1 = self.fc_attention1(y1)
        y1 = self.sig(y1).view(y1.size(0), y1.size(1), -1)
        x = x1 * y1 + y1

        # Block 2 + FMS Attention
        x2 = self.block2(x)
        y2 = self.avgpool(x2).view(x2.size(0), -1)
        y2 = self.fc_attention2(y2)
        y2 = self.sig(y2).view(y2.size(0), y2.size(1), -1)
        x = x2 * y2 + y2

        # Block 3 + FMS Attention
        x3 = self.block3(x)
        y3 = self.avgpool(x3).view(x3.size(0), -1)
        y3 = self.fc_attention3(y3)
        y3 = self.sig(y3).view(y3.size(0), y3.size(1), -1)
        x = x3 * y3 + y3

        # Block 4 + FMS Attention
        x4 = self.block4(x)
        y4 = self.avgpool(x4).view(x4.size(0), -1)
        y4 = self.fc_attention4(y4)
        y4 = self.sig(y4).view(y4.size(0), y4.size(1), -1)
        x = x4 * y4 + y4

        # Block 5 + FMS Attention
        x5 = self.block5(x)
        y5 = self.avgpool(x5).view(x5.size(0), -1)
        y5 = self.fc_attention5(y5)
        y5 = self.sig(y5).view(y5.size(0), y5.size(1), -1)
        x = x5 * y5 + y5

        x = self.bn_before_gru(x)
        x = self.selu(x)
        x = x.permute(0, 2, 1)  # (batch, time, channels)
        self.gru.flatten_parameters()
        x, _ = self.gru(x)
        x = x[:, -1, :]
        x = self.fc1_gru(x)
        x = self.fc2_gru(x)
        return self.logsoftmax(x)


# =============================================================================
# 3. Real Audio Deepfake Detector Implementation
# =============================================================================

class RealAudioDeepfakeDetector(AudioDeepfakeDetector):
    """
    Real Audio Deepfake & Anti-Spoofing Detector.
    Uses pretrained RawNet2 on 16kHz PCM audio segments.
    
    Output Semantics:
      Class 0: Spoof (Synthetic speech, voice cloning, neural vocoder artifacts)
      Class 1: Bona fide (Genuine human speech)
      spoof_probability = exp(log_softmax[:, 0])
    """

    def __init__(
        self,
        weights_path: Optional[Union[str, Path]] = None,
        segment_duration_sec: float = 4.0,
        segment_overlap_sec: float = 2.0,
        target_sample_rate: int = 16000,
        model_version: str = "VERITAS-AUDIO-RAWNET2-v1.0"
    ):
        self.model_version = model_version
        self.model_name = "RawNet2 Speech Anti-Spoofing (ASVspoof 2021)"
        self.is_mock = False
        self.detection_mode = "REAL_AUDIO_ANTI_SPOOFING"
        self.segment_duration_sec = segment_duration_sec
        self.segment_overlap_sec = segment_overlap_sec
        self.target_sample_rate = target_sample_rate
        self.segment_samples = int(segment_duration_sec * target_sample_rate)  # 64,000 samples
        self.hop_samples = int((segment_duration_sec - segment_overlap_sec) * target_sample_rate)  # 32,000 samples

        self.weights_path = Path(weights_path) if weights_path else DEFAULT_RAWNET2_WEIGHTS
        self._mock_fallback = MockAudioDetector()
        self.model: Optional[RawNet2] = None
        self.weights_verified = False

        self._load_model()

    def _load_model(self):
        """Initializes RawNet2 and loads pretrained weights on CPU."""
        try:
            if not self.weights_path.exists():
                logger.warning(f"RawNet2 weights not found at '{self.weights_path}'. Fallback available.")
                self.weights_verified = False
                return

            self.model = RawNet2()
            ckpt = torch.load(str(self.weights_path), map_location="cpu", weights_only=False)
            self.model.load_state_dict(ckpt, strict=False)
            self.model.eval()
            self.weights_verified = True
            logger.info(f"Loaded RawNet2 speech anti-spoofing model from '{self.weights_path}' ({self.weights_path.stat().st_size / (1024*1024):.1f} MB)")
        except Exception as exc:
            logger.error(f"Failed to load RawNet2 weights: {exc}")
            self.model = None
            self.weights_verified = False

    def preprocess_samples(self, samples: np.ndarray, orig_sr: int) -> np.ndarray:
        """
        Normalizes audio to mono float32 in [-1.0, 1.0] and resamples to 16,000 Hz.
        """
        if samples is None or len(samples) == 0:
            return np.zeros(0, dtype=np.float32)

        # Convert stereo/multi-channel to mono
        if samples.ndim > 1:
            samples = np.mean(samples, axis=1)

        samples = samples.astype(np.float32)

        # Normalize amplitude if needed
        max_val = np.max(np.abs(samples)) if len(samples) > 0 else 0.0
        if max_val > 1.0:
            samples = samples / max_val

        # Resample to 16kHz if needed using PyTorch 1D linear interpolation
        if orig_sr != self.target_sample_rate and len(samples) > 0:
            duration = len(samples) / orig_sr
            target_len = max(1, int(round(duration * self.target_sample_rate)))
            tensor_in = torch.from_numpy(samples).view(1, 1, -1)
            tensor_out = F.interpolate(tensor_in, size=target_len, mode="linear", align_corners=False)
            samples = tensor_out.view(-1).numpy().astype(np.float32)

        return samples

    def segment_audio(self, samples: np.ndarray) -> List[Tuple[int, float, float, np.ndarray]]:
        """
        Segments 16kHz audio into 4.0s (64,000 sample) chunks with 2.0s overlap.
        If audio length is between 0.5s and 4.0s, repeats/tiles to 64,000 samples (ASVspoof standard).
        Returns: list of (segment_id_idx, start_time_sec, end_time_sec, segment_samples_64k)
        """
        N = len(samples)
        if N < int(0.5 * self.target_sample_rate):
            return []

        segments = []
        if N < self.segment_samples:
            # Repeat waveform to reach 64,000 samples
            repeats = int(math.ceil(self.segment_samples / float(N)))
            tiled = np.tile(samples, repeats)[:self.segment_samples]
            duration = N / float(self.target_sample_rate)
            segments.append((0, 0.0, round(duration, 2), tiled))
            return segments

        # Generate overlapping windows
        start_idx = 0
        seg_id = 0
        while start_idx + self.segment_samples <= N:
            seg = samples[start_idx : start_idx + self.segment_samples]
            start_t = round(start_idx / float(self.target_sample_rate), 2)
            end_t = round((start_idx + self.segment_samples) / float(self.target_sample_rate), 2)
            segments.append((seg_id, start_t, end_t, seg))
            seg_id += 1
            start_idx += self.hop_samples

        # Add trailing segment if significant remaining audio (> 1.0s)
        if start_idx < N and (N - start_idx) >= self.target_sample_rate:
            seg = samples[-self.segment_samples:]
            start_t = round(max(0.0, (N - self.segment_samples) / float(self.target_sample_rate)), 2)
            end_t = round(N / float(self.target_sample_rate), 2)
            segments.append((seg_id, start_t, end_t, seg))

        return segments

    def analyze(self, media_path_or_bytes: Any) -> Dict[str, Any]:
        """
        Performs speech anti-spoofing forensic analysis across audio segments.
        """
        t0 = time.perf_counter()

        # Check if fallback is required
        if not self.model or not self.weights_verified:
            logger.warning("RawNet2 model not initialized. Falling back to MockAudioDetector.")
            return self._mock_fallback.analyze(media_path_or_bytes)

        # 1. Ingest audio samples
        raw_samples, orig_sr, orig_ch = audio_extractor.read_audio_file(media_path_or_bytes)

        # 2. Extract measurable physical features before neural inference
        phys_features = audio_extractor.extract_from_pcm(raw_samples, orig_sr, orig_ch)

        # 3. Audio Quality & Limitations Filter
        quality_status, quality_issue = self._evaluate_audio_quality(raw_samples, phys_features)
        if quality_status != "VALID":
            latency_ms = round((time.perf_counter() - t0) * 1000, 2)
            model_registry.update_health("CANDIDATE-AUDIO-RAWNET2", latency_ms, True)
            return {
                "model_name": self.model_name,
                "model_version": self.model_version,
                "category": "Audio Anti-Spoofing",
                "detection_mode": self.detection_mode,
                "is_mock": False,
                "classification_status": quality_status,
                "quality_issue": quality_issue,
                "score": 0,
                "confidence": 0,
                "maximum_spoof_score": 0,
                "mean_spoof_score": 0,
                "aggregate_spoof_score": 0,
                "score_standard_deviation": 0.0,
                "segment_count": 0,
                "segments_analyzed": 0,
                "segments": [],
                "highest_risk_segment": None,
                "audio_forensic_features": phys_features.to_dict(),
                "signals": [
                    {
                        "id": f"sig-aud-{quality_status.lower()}",
                        "name": f"Audio Quality Limitation ({quality_status})",
                        "category": "audio",
                        "severity": "medium",
                        "confidence": 90,
                        "affectedRegionOrTime": f"Audio Stream (0.0s - {phys_features.duration_sec:.1f}s)",
                        "explanation": quality_issue
                    }
                ],
                "timeline": [],
                "latency_ms": latency_ms
            }

        # 4. Preprocess & Resample to 16kHz Mono
        samples_16k = self.preprocess_samples(raw_samples, orig_sr)

        # 5. Segment Audio
        segments_raw = self.segment_audio(samples_16k)
        if not segments_raw:
            latency_ms = round((time.perf_counter() - t0) * 1000, 2)
            return {
                "model_name": self.model_name,
                "model_version": self.model_version,
                "category": "Audio Anti-Spoofing",
                "detection_mode": self.detection_mode,
                "is_mock": False,
                "classification_status": "INSUFFICIENT_AUDIO_EVIDENCE",
                "quality_issue": "Audio length is too short to construct valid anti-spoofing analysis windows.",
                "score": 0,
                "confidence": 0,
                "maximum_spoof_score": 0,
                "mean_spoof_score": 0,
                "aggregate_spoof_score": 0,
                "score_standard_deviation": 0.0,
                "segment_count": 0,
                "segments_analyzed": 0,
                "segments": [],
                "highest_risk_segment": None,
                "audio_forensic_features": phys_features.to_dict(),
                "signals": [],
                "timeline": [],
                "latency_ms": latency_ms
            }

        # 6. Real Neural Inference per Segment
        analyzed_segments = []
        segment_scores = []
        signals = []
        timeline_events = []

        with torch.no_grad():
            for idx, start_t, end_t, seg_samples in segments_raw:
                t_seg0 = time.perf_counter()
                tensor_seg = torch.from_numpy(seg_samples).unsqueeze(0)  # Shape: (1, 64000)
                
                # Forward pass through RawNet2
                log_probs = self.model(tensor_seg)  # Shape: (1, 2)
                probs = torch.exp(log_probs).squeeze(0)  # [spoof_prob, bonafide_prob]

                spoof_p = float(probs[0].item())
                bonafide_p = float(probs[1].item())
                seg_latency = round((time.perf_counter() - t_seg0) * 1000, 2)

                # Prediction confidence based on margin between class probabilities
                margin = abs(spoof_p - bonafide_p)
                conf = int(round(margin * 100.0))
                spoof_score = int(round(spoof_p * 100.0))

                seg_dict = {
                    "segment_id": f"seg-{idx}",
                    "start_timestamp": start_t,
                    "end_timestamp": end_t,
                    "spoof_probability": round(spoof_p, 4),
                    "bonafide_probability": round(bonafide_p, 4),
                    "prediction_confidence": conf,
                    "inference_latency_ms": seg_latency,
                    "model_name": self.model_name,
                    "model_version": self.model_version,
                    "is_mock": False
                }
                analyzed_segments.append(seg_dict)
                segment_scores.append(spoof_score)

                # Timeline event if segment has high spoof score
                if spoof_score >= 70:
                    f_min_start = int(start_t // 60)
                    f_sec_start = start_t % 60
                    f_min_end = int(end_t // 60)
                    f_sec_end = end_t % 60
                    formatted_span = f"{f_min_start:02d}:{f_sec_start:04.1f}–{f_min_end:02d}:{f_sec_end:04.1f}"
                    timeline_events.append({
                        "id": f"aud-tm-high-{idx}",
                        "start_timestamp": start_t,
                        "end_timestamp": end_t,
                        "formatted_time": formatted_span,
                        "event_type": "HIGH_SPOOF_SCORE",
                        "severity": "HIGH" if spoof_score >= 85 else "MEDIUM",
                        "spoof_score": spoof_score,
                        "explanation": f"RawNet2 detected synthetic voice / vocoder artifacts (spoof evidence {spoof_score}%)."
                    })

        # Check for sudden score changes across consecutive segments
        for i in range(1, len(analyzed_segments)):
            prev_s = segment_scores[i - 1]
            curr_s = segment_scores[i]
            if abs(curr_s - prev_s) >= 30:
                s_t = analyzed_segments[i]["start_timestamp"]
                e_t = analyzed_segments[i]["end_timestamp"]
                f_min_start = int(s_t // 60)
                f_sec_start = s_t % 60
                f_min_end = int(e_t // 60)
                f_sec_end = e_t % 60
                formatted_span = f"{f_min_start:02d}:{f_sec_start:04.1f}–{f_min_end:02d}:{f_sec_end:04.1f}"
                timeline_events.append({
                    "id": f"aud-tm-jump-{i}",
                    "start_timestamp": s_t,
                    "end_timestamp": e_t,
                    "formatted_time": formatted_span,
                    "event_type": "SUDDEN_SPOOF_SCORE_CHANGE",
                    "severity": "MEDIUM",
                    "spoof_score": curr_s,
                    "explanation": f"Sharp spoof score shift of {abs(curr_s - prev_s)} points between consecutive segments."
                })

        # 7. Audio-Level Aggregation
        max_score = int(max(segment_scores)) if segment_scores else 0
        mean_score = int(round(float(np.mean(segment_scores)))) if segment_scores else 0
        std_score = float(round(float(np.std(segment_scores)), 2)) if len(segment_scores) > 1 else 0.0
        agg_score = int(round(0.7 * max_score + 0.3 * mean_score))

        highest_seg = max(analyzed_segments, key=lambda s: s["spoof_probability"]) if analyzed_segments else None

        # Build Forensic Signals
        if max_score >= 65:
            signals.append({
                "id": "sig-aud-rawnet2-spoof",
                "name": "Neural Speech Synthesis & Voice Clone Indicator",
                "category": "audio",
                "evidence_source": "AUDIO_SPEECH",
                "severity": "high" if max_score >= 85 else "medium",
                "confidence": int(round(highest_seg["prediction_confidence"])) if highest_seg else 85,
                "affectedRegionOrTime": f"Audio Segment [{highest_seg['start_timestamp']:.1f}s - {highest_seg['end_timestamp']:.1f}s]" if highest_seg else "Audio Track",
                "explanation": f"RawNet2 spectral convolution identified neural vocoder / synthetic acoustic patterns (peak spoof score: {max_score}%)."
            })

        if phys_features.clipping_ratio > 0.05:
            signals.append({
                "id": "sig-aud-clip-1",
                "name": "Acoustic Signal Amplitude Clipping",
                "category": "audio",
                "evidence_source": "AUDIO_GENERAL",
                "severity": "medium",
                "confidence": int(round(phys_features.clipping_ratio * 100)),
                "affectedRegionOrTime": f"Audio Stream (0.0s - {phys_features.duration_sec:.1f}s)",
                "explanation": f"High amplitude clipping observed in {round(phys_features.clipping_ratio*100, 1)}% of samples."
            })

        total_latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        model_registry.update_health("CANDIDATE-AUDIO-RAWNET2", total_latency_ms, True)

        return {
            "model_name": self.model_name,
            "model_version": self.model_version,
            "category": "Audio Anti-Spoofing",
            "evidence_source": "AUDIO_SPEECH",
            "detection_mode": self.detection_mode,
            "is_mock": False,
            "classification_status": "ANALYZED",
            "score": agg_score,
            "confidence": 88 if len(analyzed_segments) >= 2 else 80,
            "maximum_spoof_score": max_score,
            "mean_spoof_score": mean_score,
            "aggregate_spoof_score": agg_score,
            "score_standard_deviation": std_score,
            "segment_count": len(analyzed_segments),
            "segments_analyzed": len(analyzed_segments),
            "segments": analyzed_segments,
            "highest_risk_segment": highest_seg,
            "audio_forensic_features": phys_features.to_dict(),
            "signals": signals,
            "timeline": timeline_events,
            "latency_ms": total_latency_ms
        }

    def _evaluate_audio_quality(
        self,
        samples: np.ndarray,
        features: AudioForensicFeatures
    ) -> Tuple[str, Optional[str]]:
        """
        Assesses audio quality constraints before neural evaluation.
        Returns: (quality_status, issue_description)
        """
        if samples is None or len(samples) == 0 or features.total_samples == 0:
            return "NO_AUDIO", "No audio samples present in media file container."

        if features.duration_sec < 0.5:
            return "TOO_SHORT", f"Audio duration ({features.duration_sec:.2f}s) is below minimum threshold (0.50s)."

        if features.silence_ratio > 0.90:
            return "EXCESSIVE_SILENCE", f"Audio consists of {round(features.silence_ratio * 100, 1)}% silence."

        if features.clipping_ratio > 0.15:
            return "CLIPPING", f"Extreme acoustic clipping ({round(features.clipping_ratio * 100, 1)}% of samples clipped) corrupts spectral representation."

        if features.spectral_rolloff_hz < 1500 and features.duration_sec > 1.0:
            return "HEAVILY_COMPRESSED", f"Spectral rolloff constrained at {features.spectral_rolloff_hz:.0f}Hz indicates severe low-pass compression."

        return "VALID", None


# =============================================================================
# 4. Factory Function
# =============================================================================

def get_audio_deepfake_detector(force_mock: bool = False) -> AudioDeepfakeDetector:
    """Factory creating the active real AudioDeepfakeDetector or Mock fallback."""
    if force_mock:
        return MockAudioDetector()
    try:
        detector = RealAudioDeepfakeDetector()
        if not detector.weights_verified:
            logger.warning("RawNet2 weights unverified. Falling back to MockAudioDetector.")
            return MockAudioDetector()
        return detector
    except Exception as exc:
        logger.error(f"Failed to initialize RealAudioDeepfakeDetector: {exc}. Falling back to MockAudioDetector.")
        return MockAudioDetector()
