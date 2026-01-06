"""
FastAPI Server with OpenAI-compatible TTS API
基于 CosyVoice 的生产级 TTS API 服务器
"""
import os
import sys
import io
import wave
import struct
import torch
import torchaudio
import numpy as np
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Response
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import tempfile
import logging
from datetime import datetime
from typing import Optional

# Add project root to path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append('{}/third_party/Matcha-TTS'.format(ROOT_DIR))

from cosyvoice.cli.cosyvoice import CosyVoice as CosyVoiceAutoModel
from cosyvoice.utils.file_utils import load_wav
from cosyvoice.utils.common import set_all_random_seed
from voice_manager import (
    save_custom_voice, load_custom_voices, delete_custom_voice,
    get_voice_by_id, get_voice_list_for_dropdown, get_voice_audio_path
)
from api_models import (
    TTSRequest, SimpleTTSRequest, VoiceCreateResponse, VoiceInfo,
    VoiceListResponse, VoiceDeleteResponse, ModelInfo, ModelListResponse,
    HealthResponse, ErrorResponse
)
from cache_manager import get_embedding_cache

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global model instance
cosyvoice_model = None
asr_model = None
model_config = {}
embedding_cache = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize model on startup"""
    global cosyvoice_model, asr_model, model_config
    
    logger.info("=" * 60)
    logger.info("🚀 Starting CosyVoice API Server")
    logger.info("=" * 60)
    
    # Load model
    model_dir = os.getenv("MODEL_DIR", "pretrained_models/Fun-CosyVoice3-0.5B")
    logger.info(f"📂 Loading model: {model_dir}")
    
    try:
        cosyvoice_model = CosyVoiceAutoModel(model_dir=model_dir, load_trt=False, fp16=False)
        model_config['sample_rate'] = cosyvoice_model.sample_rate
        model_config['model_dir'] = model_dir
        logger.info(f"✅ Model loaded successfully (SR: {model_config['sample_rate']}Hz)")
    except Exception as e:
        logger.error(f"❌ Failed to load CosyVoice model: {e}")
        raise
    
    # Try to load ASR model for auto-transcription
    try:
        from funasr import AutoModel as FunASRAutoModel
        asr_model_dir = "pretrained_models/SenseVoiceSmall"
        if os.path.exists(asr_model_dir):
            logger.info(f"📂 Loading ASR model: {asr_model_dir}")
            asr_model = FunASRAutoModel(
                model=asr_model_dir,
                disable_update=True,
                log_level='ERROR',
                device="cuda:0" if torch.cuda.is_available() else "cpu"
            )
    logger.info(f"✅ ASR model loaded successfully")
    except Exception as e:
        logger.warning(f"⚠️  ASR model not available: {e}")
        asr_model = None
    
    # Initialize embedding cache
    global embedding_cache
    embedding_cache = get_embedding_cache()
    logger.info("💾 Initializing embedding cache...")
    
    # Preload existing caches
    try:
        loaded_count = embedding_cache.preload_all_caches()
        if loaded_count > 0:
            logger.info(f"✅ Preloaded {loaded_count} embedding caches")
    except Exception as e:
        logger.warning(f"⚠️  Cache preload failed: {e}")
    
    logger.info("=" * 60)
    logger.info("✅ API Server ready")
    logger.info("🌐 Listening on port 81889")
    logger.info("=" * 60)
    
    yield
    
    logger.info("Shutting down API server...")

# Create FastAPI app
app = FastAPI(
    title="CosyVoice TTS API",
    description="OpenAI-compatible Text-to-Speech API powered by Fun-CosyVoice3",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Helper Functions =====

def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio using ASR model"""
    if asr_model is None:
        return ""
    
    try:
        res = asr_model.generate(
            input=audio_path,
            language="auto",
            use_itn=True
        )
        text = res[0]["text"].split('|>')[-1]
        return text
    except Exception as e:
        logger.error(f"ASR transcription failed: {e}")
        return ""

def numpy_to_wav_bytes(audio_np: np.ndarray, sample_rate: int) -> bytes:
    """Convert numpy array to WAV bytes"""
    buffer = io.BytesIO()
    
    # Ensure correct shape and dtype
    if audio_np.ndim == 2:
        audio_np = audio_np.squeeze()
    
    # Normalize to int16
    audio_np = np.clip(audio_np, -1.0, 1.0)
    audio_int16 = (audio_np * 32767).astype(np.int16)
    
    # Write WAV
    with wave.open(buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_int16.tobytes())
    
    buffer.seek(0)
    return buffer.getvalue()

def numpy_to_pcm_bytes(audio_np: np.ndarray) -> bytes:
    """Convert numpy array to raw PCM bytes (for streaming)"""
    if audio_np.ndim == 2:
        audio_np = audio_np.squeeze()
    
    audio_np = np.clip(audio_np, -1.0, 1.0)
    audio_int16 = (audio_np * 32767).astype(np.int16)
    return audio_int16.tobytes()

async def stream_pcm_generator(text: str, voice_id: str, speed: float = 1.0):
    """Generate PCM audio stream chunk by chunk"""
    voice_data = get_voice_by_id(voice_id)
    if not voice_data:
        raise HTTPException(status_code=404, detail=f"Voice '{voice_id}' not found")
    
    prompt_text = voice_data['text']
    prompt_audio = voice_data['audio']
    
    # Stream generation
    for chunk in cosyvoice_model.inference_zero_shot(
        text, prompt_text, prompt_audio, stream=True, speed=speed
    ):
        pcm_data = numpy_to_pcm_bytes(chunk['tts_speech'].numpy())
        yield pcm_data

# ===== API Endpoints =====

@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint"""
    return {
        "message": "CosyVoice TTS API Server",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    voices = load_custom_voices()
    
    return HealthResponse(
        status="ok",
        model_loaded=cosyvoice_model is not None,
        voice_count=len(voices),
        gpu_available=torch.cuda.is_available(),
        timestamp=datetime.now().isoformat()
    )

@app.get("/v1/models", response_model=ModelListResponse)
async def list_models():
    """List available models (OpenAI-compatible)"""
    return ModelListResponse(
        object="list",
        data=[
            ModelInfo(
                id="cosyvoice-v1",
                created=int(datetime.now().timestamp()),
                owned_by="cosyvoice"
            )
        ]
    )

@app.get("/v1/cache/stats")
async def get_cache_stats():
    """Get embedding cache statistics"""
    if embedding_cache is None:
        return {"error": "Cache not initialized"}
    
    stats = embedding_cache.get_stats()
    return {
        "cache_stats": stats,
        "status": "ok"
    }

@app.post("/v1/voices/create", response_model=VoiceCreateResponse)
async def create_voice(
    audio: UploadFile = File(..., description="Audio file (WAV, MP3, etc.)"),
    name: str = Form(..., description="Voice name"),
    text: Optional[str] = Form(None, description="Reference text (auto-transcribe if not provided)")
):
    """
    Create a custom voice
    
    If text is not provided, will use ASR to auto-transcribe the audio.
    """
    if not audio.filename:
        raise HTTPException(status_code=400, detail="Audio file is required")
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio.filename)[1]) as tmp_file:
        content = await audio.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name
    
    try:
        # Auto-transcribe if text not provided
        if not text:
            if asr_model is None:
                raise HTTPException(
                    status_code=400,
                    detail="Text is required (ASR not available for auto-transcription)"
                )
            logger.info(f"Auto-transcribing audio for voice '{name}'...")
            text = transcribe_audio(tmp_path)
            if not text:
                raise HTTPException(status_code=400, detail="Auto-transcription failed, please provide text manually")
            logger.info(f"Transcribed: {text[:100]}...")
        
        # Save voice
        result = save_custom_voice(name, tmp_path, text)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["message"])
        
        # Get voice data
        voice_id = result["voice_id"]
        voice_data = get_voice_by_id(voice_id)
        
        # Generate and cache embedding for the new voice
        logger.info(f"Generating embedding cache for voice '{name}'...")
        try:
            audio_path = voice_data['audio']
            # Extract embedding by doing a dummy inference
            for chunk in cosyvoice_model.inference_zero_shot(
                "预热", text, audio_path, stream=False
            ):
                # The embedding is computed internally
                pass
            
            # Note: CosyVoice doesn't directly expose embeddings,
            # so we rely on model's internal caching mechanism
            logger.info(f"✅ Voice '{name}' ready for use")
        except Exception as e:
            logger.warning(f"⚠️  Embedding generation failed: {e}")
        
        return VoiceCreateResponse(**voice_data)
        
    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@app.get("/v1/voices/custom", response_model=VoiceListResponse)
async def list_custom_voices():
    """List all custom voices"""
    voices = load_custom_voices()
    voice_list = [VoiceInfo(**data) for data in voices.values()]
    
    return VoiceListResponse(
        voices=voice_list,
        total=len(voice_list)
    )

@app.get("/v1/voices/{voice_id}", response_model=VoiceInfo)
async def get_voice(voice_id: str):
    """Get voice details"""
    voice_data = get_voice_by_id(voice_id)
    if not voice_data:
        raise HTTPException(status_code=404, detail=f"Voice '{voice_id}' not found")
    
    return VoiceInfo(**voice_data)

@app.delete("/v1/voices/{voice_id}", response_model=VoiceDeleteResponse)
async def delete_voice(voice_id: str):
    """Delete a custom voice"""
    # Delete embedding cache first
    if embedding_cache:
        embedding_cache.delete_cache(voice_id)
    
    # Delete voice
    result = delete_custom_voice(voice_id)
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])
    
    return VoiceDeleteResponse(
        success=True,
        message=result["message"],
        voice_id=voice_id
    )

@app.post("/v1/audio/speech")
async def create_speech(request: TTSRequest):
    """
    Generate speech from text (OpenAI-compatible)
    
    Supports response formats:
    - wav: Complete WAV file
    - pcm: Raw PCM stream (lowest latency)
    - mp3: MP3 file (requires ffmpeg)
    """
    if cosyvoice_model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    voice_id = request.voice
    text = request.input
    speed = request.speed
    response_format = request.response_format
    
    # Get voice data
    voice_data = get_voice_by_id(voice_id)
    if not voice_data:
        raise HTTPException(status_code=404, detail=f"Voice '{voice_id}' not found")
    
    prompt_text = voice_data['text']
    prompt_audio = voice_data['audio']
    
    try:
        if response_format == "pcm":
            # Stream PCM chunks
            return StreamingResponse(
                stream_pcm_generator(text, voice_id, speed),
                media_type="audio/pcm",
                headers={
                    "X-Sample-Rate": str(model_config['sample_rate']),
                    "X-Channels": "1",
                    "X-Bit-Depth": "16"
                }
            )
        
        elif response_format == "wav":
            # Generate complete audio
            speech_list = []
            for chunk in cosyvoice_model.inference_zero_shot(
                text, prompt_text, prompt_audio, stream=False, speed=speed
            ):
                speech_list.append(chunk['tts_speech'])
            
            audio_np = torch.concat(speech_list, dim=1).numpy().flatten()
            wav_bytes = numpy_to_wav_bytes(audio_np, model_config['sample_rate'])
            
            return Response(
                content=wav_bytes,
                media_type="audio/wav",
                headers={"Content-Disposition": "attachment; filename=speech.wav"}
            )
        
        else:  # mp3 or other formats
            raise HTTPException(
                status_code=400,
                detail=f"Format '{response_format}' not supported yet. Use 'wav' or 'pcm'."
            )
    
    except Exception as e:
        logger.error(f"Speech generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

# ===== Error Handlers =====

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            code=exc.status_code
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc)
        ).dict()
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 81889))
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )
