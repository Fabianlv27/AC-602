from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

# Enums para validación (mismos que en models)
class CefrEnum(str, Enum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"

class SubSourceEnum(str, Enum):
    manual = "manual"
    generated = "generated"
    none = "none"

# --- BASE ---
class VideoBase(BaseModel):
    url: str
    title: str
    channel_name: Optional[str] = None
    topics: List[str] = []
    
    # NUEVOS CAMPOS
    accents: List[str] = []
    content_types: List[str] = []
    language: str = "en"          # Default inglés
    transcript: Optional[str] = None
    
    level: Optional[CefrEnum] = None
    wpm: int = 0
    subtitle_source: SubSourceEnum = SubSourceEnum.none
    ai_analysis: Dict[str, Any] = {}
    transcript_json: List[Dict[str, Any]] = []

# --- CREATE ---
class VideoCreate(VideoBase):
    video_id: str

# --- UPDATE ---
class VideoUpdate(BaseModel):
    title: Optional[str] = None
    channel_name: Optional[str] = None
    topics: Optional[List[str]] = None
    
    # NUEVOS CAMPOS (Opcionales para update)
    accents: Optional[List[str]] = None
    content_types: Optional[List[str]] = None
    language: Optional[str] = None
    transcript: Optional[str] = None
    
    level: Optional[CefrEnum] = None
    wpm: Optional[int] = None
    subtitle_source: Optional[SubSourceEnum] = None
    ai_analysis: Optional[Dict[str, Any]] = None

# --- RESPONSE ---
class VideoResponse(VideoBase):
    video_id: str
    created_at: Any
    updated_at: Any

    class Config:
        from_attributes = True