from sqlalchemy import Column, String, Integer, Enum as PgEnum, JSON, DateTime, Text
from sqlalchemy.sql import func
from database import Base
import enum
from sqlalchemy.dialects.postgresql import ARRAY

# --- ENUMS ---
class CefrEnum(str, enum.Enum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"

class SubSourceEnum(str, enum.Enum):
    manual = "manual"
    generated = "generated"
    none = "none"

# --- MODELO VIDEO ACTUALIZADO ---
class Video(Base):
    __tablename__ = "videos"

    video_id = Column(String, primary_key=True, index=True)
    url = Column(String, nullable=False)
    title = Column(String, nullable=False)
    channel_name = Column(String, nullable=True)

    # Arrays
    topics = Column(ARRAY(Text), default=[])       
    accents = Column(ARRAY(Text), default=[])      
    content_types = Column(ARRAY(Text), default=[]) 

    # Clasificación
    level = Column(PgEnum(CefrEnum, name="cefr_enum", create_type=False), nullable=True)
    wpm = Column(Integer, default=0)
    subtitle_source = Column(PgEnum(SubSourceEnum, name="sub_source_enum", create_type=False), default=SubSourceEnum.none)

    # --- NUEVOS CAMPOS ---
    language = Column(String, default="en") # ej: 'en', 'es'
    transcript = Column(Text, nullable=True) # Texto completo del video
    transcript_json = Column(JSON, default=[])
    # Datos extra y Fechas
    ai_analysis = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())