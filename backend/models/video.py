from sqlalchemy import Column, String, Integer, Enum as PgEnum, ARRAY, JSON, DateTime, Text
from sqlalchemy.sql import func
from database import Base
import enum

# --- ENUMS (Deben coincidir con los de tu workflow) ---
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

# --- LA CLASE QUE ESTABA FALTANDO ---
class Video(Base):
    __tablename__ = "videos"

    # Identificadores
    video_id = Column(String, primary_key=True, index=True)
    url = Column(String, nullable=False)
    title = Column(String, nullable=False)
    channel_name = Column(String, nullable=True)

    # Arrays de Postgres
    topics = Column(ARRAY(String), default=[])
    accents = Column(ARRAY(String), default=[])
    content_types = Column(ARRAY(String), default=[])

    # Clasificación y Métricas
    level = Column(PgEnum(CefrEnum, name="cefr_enum", create_type=False), nullable=True)
    wpm = Column(Integer, default=0)
    subtitle_source = Column(PgEnum(SubSourceEnum, name="sub_source_enum", create_type=False), default=SubSourceEnum.none)

    # JSON y Fechas
    ai_analysis = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())