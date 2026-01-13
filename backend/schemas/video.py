from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

# Enums (Deben coincidir con tus modelos)
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
    
    # Arrays
    topics: List[str] = []
    accents: List[str] = []       # <--- Nuevo
    content_types: List[str] = [] # <--- Nuevo
    
    # Clasificación
    level: Optional[CefrEnum] = None
    wpm: int = 0
    language: str = "en"
    subtitle_source: SubSourceEnum = SubSourceEnum.none

    # Datos Ricos (JSON)
    # transcript: Se omite o se pone Optional porque ya no lo usamos en texto plano
    transcript_json: List[Dict[str, Any]] = [] # <--- Crucial para el player interactivo
    ai_analysis: Dict[str, Any] = {}           # <--- Aquí va vocabulario, grammar, summary

# --- CREATE ---
class VideoCreate(VideoBase):
    video_id: str

# --- UPDATE ---
class VideoUpdate(BaseModel):
    title: Optional[str] = None
    topics: Optional[List[str]] = None
    accents: Optional[List[str]] = None
    content_types: Optional[List[str]] = None
    level: Optional[CefrEnum] = None
    ai_analysis: Optional[Dict[str, Any]] = None

# --- RESPONSE ---
class VideoResponse(VideoBase):
    video_id: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True