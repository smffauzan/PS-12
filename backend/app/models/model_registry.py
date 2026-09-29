"""
VERITAS AI — Advanced Model Registry & Candidate Audit Architecture
Module: backend.app.models.model_registry

Maintains the comprehensive catalog of active, candidate, and research AI forensic models.
Tracks model metadata, hardware feasibility, execution provider health, and operational readiness.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging

logger = logging.getLogger("veritas.models.registry")


class ModalityType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    AV_SYNC = "av_sync"
    PROVENANCE = "provenance"
    MULTIMODAL = "multimodal"


class ModelStatus(str, Enum):
    ACTIVE = "ACTIVE"
    CANDIDATE = "CANDIDATE"
    EVALUATING = "EVALUATING"
    PLANNED = "PLANNED"
    OPTIONAL_GPU = "OPTIONAL_GPU"
    DEPRECATED = "DEPRECATED"


class ExecutionMode(str, Enum):
    FAST = "FAST"                      # YuNet + ViT
    BALANCED = "BALANCED"              # Fast + Frequency + Audio Features
    DEEP_FORENSICS = "DEEP_FORENSICS"  # All Available Active & Candidate Modalities


@dataclass
class ModelMetadata:
    """Detailed technical specification of an AI model or forensic analyzer."""
    model_id: str
    model_name: str
    modality: ModalityType
    task: str
    architecture: str
    source: str
    repository: str
    version: str
    license: str
    weight_size_mb: float
    input_format: str
    input_size: Tuple[int, ...]
    output_semantics: str
    execution_provider: str
    cpu_supported: bool
    gpu_required: bool
    quantization: str
    expected_latency_ms: float
    training_dataset_if_known: str
    known_limitations: List[str]
    status: ModelStatus
    loaded: bool = False
    weights_verified: bool = False
    last_inference_ms: Optional[float] = None
    error_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["modality"] = self.modality.value
        d["status"] = self.status.value
        return d


class ModelRegistry:
    """
    Central registry and health manager for all VERITAS forensic models and algorithms.
    Provides candidate audits, runtime health tracking, and model selection.
    """

    def __init__(self):
        self._models: Dict[str, ModelMetadata] = {}
        self._initialize_default_registry()

    def _initialize_default_registry(self):
        """Populates active models and candidate audit entries across all 5 forensic modalities."""
        
        # =====================================================================
        # 1. ACTIVE RUNTIME MODELS (Verified on CPU)
        # =====================================================================
        self.register_model(ModelMetadata(
            model_id="VERITAS-VISION-YUNET-v1",
            model_name="OpenCV YuNet Face Detector",
            modality=ModalityType.IMAGE,
            task="face_detection_and_landmark_localization",
            architecture="YuNet (Feature Pyramid Network + Anchor-free Head)",
            source="OpenCV Model Zoo",
            repository="opencv/opencv_zoo",
            version="2023mar",
            license="Apache-2.0",
            weight_size_mb=0.23,
            input_format="RGB Image (variable resolution)",
            input_size=(1, 3, 320, 320),
            output_semantics="bounding_boxes, 5_landmarks, detector_confidence",
            execution_provider="OpenCV_DNN_CPU",
            cpu_supported=True,
            gpu_required=False,
            quantization="FP32",
            expected_latency_ms=25.0,
            training_dataset_if_known="WIDER FACE",
            known_limitations=["Performance drops on extreme profile angles (>75 deg) or heavy motion blur"],
            status=ModelStatus.ACTIVE,
            loaded=True,
            weights_verified=True
        ))

        self.register_model(ModelMetadata(
            model_id="VERITAS-VISION-VIT-v2",
            model_name="Vision Transformer Deepfake Classifier v2",
            modality=ModalityType.IMAGE,
            task="facial_manipulation_classification",
            architecture="ViT (Vision Transformer base patch-16)",
            source="HuggingFace (prithivMLmods)",
            repository="prithivMLmods/Deep-Fake-Detector-v2",
            version="2.0-quantized",
            license="Apache-2.0",
            weight_size_mb=83.3,
            input_format="RGB Tensor standardized (224x224x3)",
            input_size=(1, 3, 224, 224),
            output_semantics="manipulation_probability [0.0, 1.0], realism_probability [0.0, 1.0]",
            execution_provider="CPUExecutionProvider (ONNXRuntime)",
            cpu_supported=True,
            gpu_required=False,
            quantization="INT8 (Dynamic Quantization)",
            expected_latency_ms=130.0,
            training_dataset_if_known="Synthetic Faces, Diffusion Generated, GAN Artifacts",
            known_limitations=[
                "Requires detected face crop; bypassed when no face is detected",
                "Uncalibrated raw softmax output; represents classification score, not calibrated Bayesian probability"
            ],
            status=ModelStatus.ACTIVE,
            loaded=True,
            weights_verified=True
        ))

        self.register_model(ModelMetadata(
            model_id="VERITAS-VISION-GLOBAL-v1",
            model_name="Global Spatial & Texture Forensic Analyzer",
            modality=ModalityType.IMAGE,
            task="content_agnostic_spatial_texture_and_compression_analysis",
            architecture="Statistical Spatial Residual & Texture Dispersion (Laplacian, Sobel, 16x16 Noise Grid, 8x8 DCT)",
            source="VERITAS Core Forensics",
            repository="backend/app/services/global_visual_forensics.py",
            version="1.0",
            license="MIT",
            weight_size_mb=0.0,
            input_format="RGB Image (variable resolution)",
            input_size=(1, 3, 224, 224),
            output_semantics="spatial_texture_variance, noise_dispersion, blocking_ratio, visual_score [0, 100]",
            execution_provider="CPU_Native_NumPy_OpenCV",
            cpu_supported=True,
            gpu_required=False,
            quantization="None",
            expected_latency_ms=12.0,
            training_dataset_if_known="None (Deterministic Statistical Physics)",
            known_limitations=[
                "Content-agnostic statistical forensic indicator",
                "Not a trained deep neural network; measures physical gradient and compression boundaries"
            ],
            status=ModelStatus.ACTIVE,
            loaded=True,
            weights_verified=True
        ))

        self.register_model(ModelMetadata(
            model_id="VERITAS-TEMPORAL-STABILITY-v1",
            model_name="Temporal Forensic Stability & Jitter Analyzer",
            modality=ModalityType.VIDEO,
            task="temporal_motion_and_score_instability_analysis",
            architecture="Mathematical Forensic Heuristic (Variance, Velocity, Landmark Jitter, Continuity)",
            source="VERITAS Core Team",
            repository="backend/app/services/video_forensics.py",
            version="1.0",
            license="Proprietary / MIT",
            weight_size_mb=0.0,
            input_format="Sequence of TrackedFaceObservation objects",
            input_size=(1,),
            output_semantics="temporal_anomaly_score [0, 100], stability_metrics",
            execution_provider="CPU_Native_NumPy",
            cpu_supported=True,
            gpu_required=False,
            quantization="None",
            expected_latency_ms=1.5,
            training_dataset_if_known="None (Deterministic Statistical Formula)",
            known_limitations=[
                "Mathematical heuristic, not a trained 3D-CNN or spatio-temporal neural network",
                "Assumes continuous face tracks; sensitive to severe tracking occlusions"
            ],
            status=ModelStatus.ACTIVE,
            loaded=True,
            weights_verified=True
        ))

        self.register_model(ModelMetadata(
            model_id="VERITAS-AUDIO-RAWNET2-v1",
            model_name="RawNet2 End-to-End Speech Anti-Spoofing",
            modality=ModalityType.AUDIO,
            task="voice_cloning_and_speech_synthesis_detection",
            architecture="Sinc-convolution + Residual Gated Recurrent Units",
            source="Interspeech / ASVspoof 2021 Baseline",
            repository="asvspoof-challenge/2021/RawNet2",
            version="1.0",
            license="MIT",
            weight_size_mb=70.5,
            input_format="Raw 16kHz PCM Audio Tensor (1, 64000 samples)",
            input_size=(1, 64000),
            output_semantics="spoof_probability [0.0, 1.0], prediction_confidence [0, 100]",
            execution_provider="PyTorch_CPU",
            cpu_supported=True,
            gpu_required=False,
            quantization="FP32",
            expected_latency_ms=120.0,
            training_dataset_if_known="ASVspoof 2019 LA + ASVspoof 2021 DF Baseline",
            known_limitations=[
                "Sensitive to background environmental acoustic reverberation",
                "Uncalibrated raw model output; represents classification activation, not calibrated Bayesian probability"
            ],
            status=ModelStatus.ACTIVE,
            loaded=True,
            weights_verified=True
        ))

        self.register_model(ModelMetadata(
            model_id="VERITAS-AUDIO-FEATURE-v1",
            model_name="Physical Acoustic & Spectral Domain Audio Analyzer",
            modality=ModalityType.AUDIO,
            task="physical_acoustic_and_spectral_feature_extraction",
            architecture="Deterministic Signal Processing (RMS, ZCR, Spectral Rolloff, F0, MFCC)",
            source="VERITAS Core Team",
            repository="backend/app/services/audio_forensics.py",
            version="1.0",
            license="MIT",
            weight_size_mb=0.0,
            input_format="Normalized Float32 Audio PCM Samples",
            input_size=(1,),
            output_semantics="acoustic_forensic_features, physical_anomaly_indicators",
            execution_provider="CPU_Native_NumPy_SciPy",
            cpu_supported=True,
            gpu_required=False,
            quantization="None",
            expected_latency_ms=10.0,
            training_dataset_if_known="None (Deterministic Acoustic Formulas)",
            known_limitations=[
                "Acoustic feature extractor measures signal properties, NOT deepfake probabilities"
            ],
            status=ModelStatus.ACTIVE,
            loaded=True,
            weights_verified=True
        ))

        self.register_model(ModelMetadata(
            model_id="VERITAS-PROVENANCE-DNA-v1",
            model_name="Cryptographic Media DNA & C2PA Provenance Engine",
            modality=ModalityType.PROVENANCE,
            task="cryptographic_hash_and_metadata_validation",
            architecture="SHA-256 + ExifTool/FFprobe Metadata Extraction",
            source="VERITAS Core Team",
            repository="backend/app/services/provenance_service.py",
            version="1.0",
            license="Apache-2.0",
            weight_size_mb=0.0,
            input_format="Raw media bytes / file headers",
            input_size=(1,),
            output_semantics="provenance_status, sha256_hash, metadata_json",
            execution_provider="CPU_Native",
            cpu_supported=True,
            gpu_required=False,
            quantization="None",
            expected_latency_ms=5.0,
            training_dataset_if_known="None (Cryptographic & Container Parsing)",
            known_limitations=[
                "Provenance verification validates metadata integrity, NOT content authenticity"
            ],
            status=ModelStatus.ACTIVE,
            loaded=True,
            weights_verified=True
        ))

        # =====================================================================
        # 2. IMAGE SPATIAL CANDIDATES (DeepfakeBench Audit)
        # =====================================================================
        self.register_model(ModelMetadata(
            model_id="CANDIDATE-SPATIAL-EFFICIENTNET-B4",
            model_name="EfficientNet-B4 Dual-Domain Forensic Net",
            modality=ModalityType.IMAGE,
            task="facial_manipulation_classification",
            architecture="EfficientNet-B4 Convolutional Network",
            source="DeepfakeBench",
            repository="SCLBD/DeepfakeBench",
            version="1.0",
            license="MIT",
            weight_size_mb=75.0,
            input_format="RGB Face Crop (256x256)",
            input_size=(1, 3, 256, 256),
            output_semantics="binary_logits, manipulation_score",
            execution_provider="CPUExecutionProvider / ONNX",
            cpu_supported=True,
            gpu_required=False,
            quantization="INT8 / FP32",
            expected_latency_ms=90.0,
            training_dataset_if_known="FaceForensics++, Celeb-DF-v2, DFDC",
            known_limitations=["Susceptible to JPEG compression artifacts at CRF > 32"],
            status=ModelStatus.CANDIDATE
        ))

        self.register_model(ModelMetadata(
            model_id="CANDIDATE-SPATIAL-SBI",
            model_name="Synthetic Basis Item (SBI) Generalization Detector",
            modality=ModalityType.IMAGE,
            task="facial_boundary_and_blending_anomaly_detection",
            architecture="EfficientNet-B4 + Synthetic Blending Self-Supervision",
            source="CVPR 2022 / DeepfakeBench",
            repository="mapooon/SelfBlendedImages",
            version="1.0",
            license="MIT",
            weight_size_mb=88.0,
            input_format="RGB Face Crop (224x224)",
            input_size=(1, 3, 224, 224),
            output_semantics="blending_mask_prediction, manipulation_score",
            execution_provider="CPUExecutionProvider",
            cpu_supported=True,
            gpu_required=False,
            quantization="INT8",
            expected_latency_ms=110.0,
            training_dataset_if_known="Self-Blended Synthetic Base (FFHQ)",
            known_limitations=["Lower sensitivity on fully synthetic diffusion images with no seam boundary"],
            status=ModelStatus.CANDIDATE
        ))

        self.register_model(ModelMetadata(
            model_id="CANDIDATE-SPATIAL-XCEPTION",
            model_name="Xception FaceForensics Benchmark Classifier",
            modality=ModalityType.IMAGE,
            task="facial_manipulation_classification",
            architecture="XceptionNet (Depthwise Separable Convolutions)",
            source="FaceForensics++ / DeepfakeBench",
            repository="ondyari/FaceForensics",
            version="1.0",
            license="MIT",
            weight_size_mb=85.0,
            input_format="RGB Face Crop (299x299)",
            input_size=(1, 3, 299, 299),
            output_semantics="binary_manipulation_probability",
            execution_provider="CPUExecutionProvider",
            cpu_supported=True,
            gpu_required=False,
            quantization="INT8",
            expected_latency_ms=120.0,
            training_dataset_if_known="FaceForensics++ (Deepfakes, Face2Face, FaceSwap, NeuralTextures)",
            known_limitations=["Prone to overfitting on in-dataset compression settings"],
            status=ModelStatus.CANDIDATE
        ))

        self.register_model(ModelMetadata(
            model_id="CANDIDATE-SPATIAL-UIA-VIT",
            model_name="UIA-ViT (Unsupervised Identity-Aware Vision Transformer)",
            modality=ModalityType.IMAGE,
            task="identity_discrepancy_and_manipulation_detection",
            architecture="Vision Transformer + Identity-Consistency Head",
            source="DeepfakeBench / ECCV 2022",
            repository="SCLBD/DeepfakeBench",
            version="1.0",
            license="MIT",
            weight_size_mb=320.0,
            input_format="RGB Face Tensor (384x384)",
            input_size=(1, 3, 384, 384),
            output_semantics="identity_loss, manipulation_probability",
            execution_provider="CPU / CUDA",
            cpu_supported=True,
            gpu_required=False,
            quantization="FP32",
            expected_latency_ms=450.0,
            training_dataset_if_known="Celeb-DF-v2, DFDC, FF++",
            known_limitations=["Heavy memory footprint (320MB), high CPU latency"],
            status=ModelStatus.EVALUATING
        ))

        # =====================================================================
        # 3. IMAGE FREQUENCY FORENSICS CANDIDATES
        # =====================================================================
        self.register_model(ModelMetadata(
            model_id="CANDIDATE-FREQ-F3NET",
            model_name="F3Net (Frequency in Face Forgery Network)",
            modality=ModalityType.IMAGE,
            task="frequency_domain_artifact_detection",
            architecture="Dual-stream (Spatial + Discrete Cosine Transform Spectral Stream)",
            source="ECCV 2020 / DeepfakeBench",
            repository="zhiyuanyan/F3Net",
            version="1.0",
            license="Apache-2.0",
            weight_size_mb=102.0,
            input_format="RGB Face Crop + DCT Spectral Decomposition",
            input_size=(1, 3, 224, 224),
            output_semantics="frequency_anomaly_score [0, 100], spectral_discontinuity",
            execution_provider="CPUExecutionProvider",
            cpu_supported=True,
            gpu_required=False,
            quantization="INT8",
            expected_latency_ms=135.0,
            training_dataset_if_known="FaceForensics++ C23/C40",
            known_limitations=["Requires 2D DCT decomposition in preprocessing"],
            status=ModelStatus.CANDIDATE
        ))

        self.register_model(ModelMetadata(
            model_id="CANDIDATE-FREQ-SRM",
            model_name="SRM-Filter Frequency Residual Forensics",
            modality=ModalityType.IMAGE,
            task="high_frequency_noise_residual_analysis",
            architecture="Spatial Rich Model (SRM) Filter Banks + 2D FFT Energy Spectrum",
            source="VERITAS Research",
            repository="backend/app/models/frequency_detector.py",
            version="1.0",
            license="MIT",
            weight_size_mb=45.0,
            input_format="RGB Face Crop (224x224)",
            input_size=(1, 3, 224, 224),
            output_semantics="frequency_anomaly_score, high_frequency_attenuation_ratio",
            execution_provider="CPU_Native_NumPy_SciPy",
            cpu_supported=True,
            gpu_required=False,
            quantization="FP32",
            expected_latency_ms=30.0,
            training_dataset_if_known="Deterministic High-Pass Filters",
            known_limitations=["Heuristic frequency filter; robust against blur but sensitive to heavy re-quantization"],
            status=ModelStatus.CANDIDATE
        ))

        # =====================================================================
        # 4. VIDEO TEMPORAL CANDIDATES (DeepfakeBench Audit)
        # =====================================================================
        self.register_model(ModelMetadata(
            model_id="CANDIDATE-TEMP-FTCN",
            model_name="FTCN (Fully Temporal Convolutional Network)",
            modality=ModalityType.VIDEO,
            task="temporal_frame_coherence_and_flicker_analysis",
            architecture="3D Temporal Convolutional Net with Spatial Kernel Reduction",
            source="ICCV 2021 / DeepfakeBench",
            repository="yinglinzheng/FTCN",
            version="1.0",
            license="MIT",
            weight_size_mb=120.0,
            input_format="Video Frame Tensor (1, 3, 32, 224, 224)",
            input_size=(1, 3, 32, 224, 224),
            output_semantics="temporal_inconsistency_probability",
            execution_provider="CPUExecutionProvider",
            cpu_supported=True,
            gpu_required=False,
            quantization="INT8",
            expected_latency_ms=350.0,
            training_dataset_if_known="FaceForensics++, Celeb-DF-v2, DeeperForensics",
            known_limitations=["Requires fixed temporal window of 32 contiguous sampled frames"],
            status=ModelStatus.CANDIDATE
        ))

        self.register_model(ModelMetadata(
            model_id="CANDIDATE-TEMP-VIDEOMAE",
            model_name="VideoMAE Spatio-Temporal Masked Autoencoder",
            modality=ModalityType.VIDEO,
            task="dense_temporal_video_representation",
            architecture="3D Vision Transformer (VideoMAE base)",
            source="NeurIPS 2022",
            repository="MCG-NJU/VideoMAE",
            version="1.0",
            license="CC-BY-NC-4.0",
            weight_size_mb=380.0,
            input_format="Video Clip Tensor (1, 3, 16, 224, 224)",
            input_size=(1, 3, 16, 224, 224),
            output_semantics="spatio_temporal_embeddings, forgery_logits",
            execution_provider="CUDAExecutionProvider",
            cpu_supported=False,
            gpu_required=True,
            quantization="FP16",
            expected_latency_ms=1200.0,
            training_dataset_if_known="Kinetics-400 Pretrained",
            known_limitations=["High GPU memory requirement (>6GB VRAM); impractical for CPU pipeline"],
            status=ModelStatus.OPTIONAL_GPU
        ))

        # =====================================================================
        # 5. AUDIO DEEPFAKE DETECTION CANDIDATES (ASVspoof Benchmark)
        # =====================================================================
        self.register_model(ModelMetadata(
            model_id="CANDIDATE-AUDIO-RAWNET2",
            model_name="RawNet2 End-to-End Speech Anti-Spoofing",
            modality=ModalityType.AUDIO,
            task="voice_cloning_and_speech_synthesis_detection",
            architecture="Sinc-convolution + Residual Gated Recurrent Units",
            source="Interspeech / ASVspoof 2019/2021",
            repository="asvspoof-challenge/2021/RawNet2",
            version="2.0",
            license="MIT",
            weight_size_mb=18.5,
            input_format="Raw 16kHz PCM Audio Tensor (1, 64000 samples)",
            input_size=(1, 64000),
            output_semantics="spoof_probability [0.0, 1.0], prediction_confidence",
            execution_provider="CPUExecutionProvider / PyTorch",
            cpu_supported=True,
            gpu_required=False,
            quantization="INT8 / FP32",
            expected_latency_ms=45.0,
            training_dataset_if_known="ASVspoof 2019 Logical Access (LA) Benchmark",
            known_limitations=["Sensitive to background environmental acoustic reverberation"],
            status=ModelStatus.CANDIDATE
        ))

        self.register_model(ModelMetadata(
            model_id="CANDIDATE-AUDIO-LFCC-LCNN",
            model_name="LFCC-LCNN (Linear Frequency Cepstral Coefficients + Light CNN)",
            modality=ModalityType.AUDIO,
            task="synthetic_speech_and_vocoder_artifact_detection",
            architecture="Light CNN (Max-Feature-Map) on LFCC Spectrograms",
            source="ASVspoof 2021 Benchmark",
            repository="asvspoof-challenge/2021/LFCC-LCNN",
            version="1.0",
            license="MIT",
            weight_size_mb=12.0,
            input_format="LFCC Cepstral Coefficients Matrix (1, 60, 750)",
            input_size=(1, 1, 60, 750),
            output_semantics="bonafide_vs_spoof_logits",
            execution_provider="CPUExecutionProvider",
            cpu_supported=True,
            gpu_required=False,
            quantization="INT8",
            expected_latency_ms=35.0,
            training_dataset_if_known="ASVspoof 2019 LA + Deepfake Partition",
            known_limitations=["Requires short-time Fourier transform & linear filter bank preprocessing"],
            status=ModelStatus.CANDIDATE
        ))

        self.register_model(ModelMetadata(
            model_id="CANDIDATE-AUDIO-AASIST",
            model_name="AASIST (Audio Anti-Spoofing Integrated Spectro-Temporal Graph Net)",
            modality=ModalityType.AUDIO,
            task="speech_synthesis_and_voice_conversion_detection",
            architecture="Heterogeneous Graph Attention Network on Raw Waveforms",
            source="ACM MM 2022 / ASVspoof",
            repository="clovaai/aasist",
            version="1.0",
            license="BSD-3-Clause",
            weight_size_mb=34.0,
            input_format="Raw 16kHz PCM Waveform (1, 64600 samples)",
            input_size=(1, 64600),
            output_semantics="spoof_probability, graph_node_attentions",
            execution_provider="CPUExecutionProvider",
            cpu_supported=True,
            gpu_required=False,
            quantization="FP32",
            expected_latency_ms=75.0,
            training_dataset_if_known="ASVspoof 2019 LA + ASVspoof 2021 DF",
            known_limitations=["Graph attention message passing slightly increases latency on long audio"],
            status=ModelStatus.CANDIDATE
        ))

        # =====================================================================
        # 6. AUDIO-VISUAL SYNCHRONIZATION CANDIDATES
        # =====================================================================
        self.register_model(ModelMetadata(
            model_id="CANDIDATE-SYNC-SYNCNET",
            model_name="SyncNet Audio-Visual Lip-Sync Coherence Discriminator",
            modality=ModalityType.AV_SYNC,
            task="lip_sync_offset_and_phoneme_viseme_coherence_evaluation",
            architecture="Dual-stream 2D/3D CNN Cross-Correlation Transformer",
            source="ACCV 2016 / SyncNet Project",
            repository="joonson/syncnet_python",
            version="1.0",
            license="MIT",
            weight_size_mb=55.0,
            input_format="Mouth ROIs (5 frames, 112x112) + MFCC 200ms Audio Slice",
            input_size=(1, 5, 112, 112),
            output_semantics="lip_sync_offset_ms, sync_consistency_score, temporal_alignment_anomaly",
            execution_provider="CPUExecutionProvider",
            cpu_supported=True,
            gpu_required=False,
            quantization="INT8",
            expected_latency_ms=65.0,
            training_dataset_if_known="LRS2 (Lip Reading Sentences 2), VoxCeleb",
            known_limitations=["Requires accurate mouth landmark localization and speech phoneme segmentation"],
            status=ModelStatus.CANDIDATE
        ))

    def register_model(self, metadata: ModelMetadata):
        """Registers or updates a model specification in the registry."""
        self._models[metadata.model_id] = metadata

    def get_model(self, model_id: str) -> Optional[ModelMetadata]:
        """Retrieves model metadata by ID."""
        return self._models.get(model_id)

    def list_models(
        self,
        modality: Optional[ModalityType] = None,
        status: Optional[ModelStatus] = None
    ) -> List[ModelMetadata]:
        """Lists registered models matching optional modality and status filters."""
        results = list(self._models.values())
        if modality:
            results = [m for m in results if m.modality == modality]
        if status:
            results = [m for m in results if m.status == status]
        return results

    def get_active_models(self) -> List[ModelMetadata]:
        """Returns all currently active runtime models."""
        return self.list_models(status=ModelStatus.ACTIVE)

    def update_health(self, model_id: str, latency_ms: float, success: bool = True):
        """Updates health statistics for a model after an inference pass."""
        if model_id in self._models:
            m = self._models[model_id]
            m.last_inference_ms = round(latency_ms, 2)
            if not success:
                m.error_count += 1

    def get_health_report(self) -> Dict[str, Any]:
        """Returns runtime health status for all registered models."""
        report = {}
        for mid, m in self._models.items():
            report[mid] = {
                "model_name": m.model_name,
                "status": m.status.value,
                "loaded": m.loaded,
                "weights_verified": m.weights_verified,
                "execution_provider": m.execution_provider,
                "cpu_supported": m.cpu_supported,
                "last_inference_ms": m.last_inference_ms,
                "error_count": m.error_count
            }
        return report

    def get_candidate_audit(self) -> Dict[str, List[Dict[str, Any]]]:
        """Returns candidate model audit categorized by modality."""
        audit: Dict[str, List[Dict[str, Any]]] = {
            "spatial_candidates": [],
            "frequency_candidates": [],
            "temporal_candidates": [],
            "audio_candidates": [],
            "av_sync_candidates": []
        }
        for m in self._models.values():
            if m.status in (ModelStatus.CANDIDATE, ModelStatus.EVALUATING, ModelStatus.OPTIONAL_GPU):
                entry = m.to_dict()
                if m.modality == ModalityType.IMAGE and "FREQ" not in m.model_id:
                    audit["spatial_candidates"].append(entry)
                elif m.modality == ModalityType.IMAGE and "FREQ" in m.model_id:
                    audit["frequency_candidates"].append(entry)
                elif m.modality == ModalityType.VIDEO:
                    audit["temporal_candidates"].append(entry)
                elif m.modality == ModalityType.AUDIO:
                    audit["audio_candidates"].append(entry)
                elif m.modality == ModalityType.AV_SYNC:
                    audit["av_sync_candidates"].append(entry)
        return audit


# Global singleton instance
model_registry = ModelRegistry()
