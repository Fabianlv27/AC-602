from sqlalchemy import Column, String, Integer, Float, Enum, DateTime, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.sql import func
import enum
from database import Base # Importamos Base de TU archivo database.py

# Definimos los Enums de Python para que coincidan con los de Postgres
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

class Video(Base):
    __tablename__ = "videos"

    video_id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    channel_name = Column(String)
    
    # Manejo de Arrays de Postgres (Listas de Strings)
    topics = Column(ARRAY(String))
    accents = Column(ARRAY(String))
    content_types = Column(ARRAY(String))
    
    # Enums
    level = Column(Enum(CefrEnum, name="cefr_enum"))
    
    wpm = Column(Integer)
    subtitle_source = Column(Enum(SubSourceEnum, name="sub_source_enum"))
    
    # JSONB para guardar la respuesta cruda de la IA
    ai_analysis = Column(JSONB)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())