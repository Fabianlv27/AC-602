from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from enum import Enum
from datetime import datetime

# --- ENUMS (Para validación estricta) ---
# Deben coincidir con los de models/video.py

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

# --- ESQUEMAS PYDANTIC ---

class VideoBase(BaseModel):
    title: str
    url: str
    channel_name: Optional[str] = None
    topics: List[str] = []
    accents: List[str] = []
    content_types: List[str] = []
    level: Optional[CefrEnum] = None
    wpm: Optional[int] = 0
    subtitle_source: Optional[SubSourceEnum] = "none"
    ai_analysis: Optional[Dict[str, Any]] = {}

# Schema para CREAR un video (POST)
class VideoCreate(VideoBase):
    video_id: str  # Obligatorio al crear

# Schema para ACTUALIZAR un video (PATCH)
# Todos los campos son opcionales aquí
class VideoUpdate(BaseModel):
    title: Optional[str] = None
    channel_name: Optional[str] = None
    topics: Optional[List[str]] = None
    accents: Optional[List[str]] = None
    content_types: Optional[List[str]] = None
    level: Optional[CefrEnum] = None
    wpm: Optional[int] = None
    ai_analysis: Optional[Dict[str, Any]] = None

# Schema para RESPONDER al cliente (GET)
# Incluye fechas y configuración para leer desde la DB
class VideoResponse(VideoBase):
    video_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        # Esto permite que Pydantic lea los datos directamente
        # de los objetos de SQLAlchemy (Base de datos)
        from_attributes = True