"""
Pydantic models for FastAPI endpoints
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime

# ===== TTS Request Models =====

class TTSRequest(BaseModel):
    """OpenAI-compatible /v1/audio/speech request"""
    input: str = Field(..., description="The text to generate audio for", min_length=1, max_length=4096)
    voice: str = Field(..., description="Voice ID or preset voice name")
    model: str = Field(default="cosyvoice-v1", description="Model to use for generation")
    response_format: Literal["wav", "pcm", "mp3"] = Field(default="wav", description="Audio format")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Speed of generated audio")
    
class SimpleTTSRequest(BaseModel):
    """Simplified TTS request"""
    text: str = Field(..., min_length=1)
    voice_id: str
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    stream: bool = Field(default=False)

# ===== Voice Management Models =====

class VoiceCreateResponse(BaseModel):
    """Response for voice creation"""
    voice_id: str
    name: str
    text: str
    created_at: str
    audio_path: str = Field(alias="audio")
    
    class Config:
        populate_by_name = True

class VoiceInfo(BaseModel):
    """Voice information"""
    voice_id: str
    name: str
    text: str
    created_at: str
    audio: str
    updated_at: Optional[str] = None
    
class VoiceListResponse(BaseModel):
    """List of voices"""
    voices: List[VoiceInfo]
    total: int

class VoiceDeleteResponse(BaseModel):
    """Response for voice deletion"""
    success: bool
    message: str
    voice_id: str

# ===== Model Info Models =====

class ModelInfo(BaseModel):
    """Model information"""
    id: str
    object: str = "model"
    created: int
    owned_by: str = "cosyvoice"
    
class ModelListResponse(BaseModel):
    """List of available models"""
    object: str = "list"
    data: List[ModelInfo]

# ===== Health Check Models =====

class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "ok"
    model_loaded: bool
    voice_count: int
    gpu_available: bool
    timestamp: str

# ===== Error Models =====

class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    code: Optional[int] = None
