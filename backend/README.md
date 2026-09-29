# VERITAS AI Backend — Forensic Architecture & Model Adapters

## Architecture Overview
The VERITAS AI backend is an enterprise-grade AI orchestration and multimodal forensic intelligence pipeline built with **FastAPI**, **Pydantic v2**, and a modular **Detector Adapter Pattern**.

```
backend/
├── app/
│   ├── main.py                     # FastAPI application & WebSocket server
│   ├── api/
│   │   └── routes/
│   │       ├── analysis.py         # POST /api/v1/analyze, GET /api/v1/analyze/{id}
│   │       ├── cases.py            # GET /api/v1/cases, GET /api/v1/cases/{id}
│   │       ├── provenance.py       # POST /api/v1/provenance/check
│   │       └── reports.py          # GET/POST /api/v1/reports/{case_id}
│   ├── models/
│   │   ├── base.py                 # Abstract BaseDetector interface
│   │   ├── image_detector.py       # MockImageDetector / MesoNet / EfficientNet adapter
│   │   ├── video_detector.py       # MockVideoDetector / XceptionNet adapter
│   │   ├── audio_detector.py       # MockAudioDetector / SpecForensics adapter
│   │   ├── temporal_detector.py    # MockTemporalDetector / OpticalFlow adapter
│   │   └── av_sync_detector.py     # MockAVSyncDetector / SyncNet adapter
│   ├── schemas/
│   │   ├── analysis.py             # Standardized Pydantic forensic result schema
│   │   └── cases.py                # Forensic case entity & list schemas
│   └── services/
│       ├── orchestrator.py         # Multi-model dispatch & pipeline orchestrator
│       ├── fusion_engine.py        # Bayesian / weighted multimodal risk aggregator
│       ├── metadata_service.py     # Container & EXIF forensic extractor
│       └── provenance_service.py   # C2PA manifest & cryptographic ledger validator
└── requirements.txt
```

---

## Model Adapter Pattern: Swapping Mock Models for Real ML Weights

All forensic models adhere to the `BaseDetector` interface defined in `app/models/base.py`:

```python
class BaseDetector(ABC):
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Identifier of the model (e.g., 'VERITAS-VISION-v1.0')"""
        pass

    @property
    @abstractmethod
    def modality(self) -> str:
        """Modality: 'image', 'video', 'audio', 'temporal', 'sync'"""
        pass

    @abstractmethod
    def predict(self, media_path_or_bytes: Any, **kwargs) -> DetectorResult:
        """Returns standard DetectorResult: score (0-100), confidence, signals, and evidence."""
        pass
```

### Steps to Replace a Mock Model:
1. Open the respective adapter (e.g. [image_detector.py](file:///d:/PS12/backend/app/models/image_detector.py)).
2. Import your model weights (`torch`, `onnxruntime`, or `tensorrt`).
3. Replace the simulated inference logic in `predict()` with the forward pass and feature extraction.
4. Output the standardized `DetectorResult` dataclass.
5. The `ForensicOrchestrator` and `MultimodalFusionEngine` automatically ingest the output with zero changes required to the frontend UI!

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Engine health check & loaded model registry |
| `POST` | `/api/v1/analyze` | Dispatch new media item for forensic processing |
| `GET` | `/api/v1/analyze/{id}` | Query status and standardized forensic payload |
| `WS` | `/ws/analysis/{id}` | Real-time WebSocket streaming of 12-stage pipeline |
| `GET` | `/api/v1/cases` | Retrieve all registered forensic investigation cases |
| `GET` | `/api/v1/cases/{id}` | Retrieve case details & evidence dossier |
| `POST` | `/api/v1/provenance/check` | Validate SHA-256 cryptographic provenance & C2PA |
| `GET` | `/api/v1/reports/{case_id}` | Generate digitally signed verification certificate |

---

## Running the Servers Locally

### 1. Backend Server (FastAPI + Uvicorn)
```powershell
cd d:\PS12\backend
uvicorn app.main:app --port 8000 --host 127.0.0.1 --reload
```

### 2. Frontend Application (Vite + React)
```powershell
cd d:\PS12
npm run dev -- --port 5173
```
