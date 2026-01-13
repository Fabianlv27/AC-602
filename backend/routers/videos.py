import json
import os
from fastapi import APIRouter, Depends, HTTPException, Query, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select
from typing import List, Optional

# --- RATE LIMITING (Redis) ---
from fastapi_limiter.depends import RateLimiter

# --- IMPORTACIONES DEL PROYECTO ---
from database import AsyncSessionLocal
from models.video import Video, CefrEnum, SubSourceEnum
from schemas.video import VideoResponse, VideoUpdate, VideoCreate

# ==========================================
# 🔐 CONFIGURACIÓN DE SEGURIDAD
# ==========================================
API_KEY_NAME = "x-admin-key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)



async def verify_admin_key(api_key_header: str = Security(api_key_header)):
    """
    Verifica que el usuario tenga la clave maestra para escribir/borrar.
    """
    correct_key = os.getenv("ADMIN_SECRET")
    
    if not correct_key:
        # Si se te olvidó poner la clave en el .env, bloqueamos todo por seguridad
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error de configuración: ADMIN_SECRET no está definido en el servidor."
        )

    if api_key_header == correct_key:
        return api_key_header
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="⛔ Acceso denegado: Necesitas la Admin Key correcta."
    )

# ==========================================
# ROUTER
# ==========================================
router = APIRouter(
    prefix="/videos",
    tags=["Videos"]
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# ==========================================
# 1. ZONA PÚBLICA (SOLO LECTURA)
#    No pide clave, pero tiene Rate Limit.
# ==========================================
@router.get("/", response_model=List[VideoResponse])
async def read_videos(
    title: Optional[str] = None,
    level: Optional[str] = None,
    language: Optional[str] = None,
    accent: Optional[str] = None,
    topic: Optional[str] = None,
    content_types: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    query = select(Video)

    if title:
        query = query.where(Video.title.ilike(f"%{title}%"))
    if level:
        query = query.where(Video.level == level)
    if language:
        query = query.where(Video.language == language)
    
    # Filtros para Arrays (Postgres)
    if accent:
        # Busca si el acento está contenido en el array accents
        query = query.where(Video.accents.any(accent))
    if topic:
        query = query.where(Video.topics.any(topic))
    if content_types:
        query = query.where(Video.content_types.any(content_types))

    # Ordenar por fecha de creación descendente
    query = query.order_by(Video.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/filters")
def get_filters():
    """
    Carga: Niveles.json, Etiquetas.json, Tipos.json y accents.json
    Devuelve la estructura exacta para que el Frontend monte los selectores.
    """
    try:
        base_path = "Data" # Asegúrate de que la carpeta se llame así
        
        def load_json(filename):
            path = os.path.join(base_path, filename)
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            return []

        levels = load_json("Niveles.json")
        topics = load_json("Etiquetas.json")
        content_types = load_json("Tipos.json")
        
        # Cargar el archivo de acentos complejo que me mostraste
        accents_data = load_json("accents.json") 
        if not accents_data:
            accents_data = {} # Fallback vacío si falla

        return {
            "levels": levels,
            "topics": topics,
            "content_types": content_types,
            "accents_data": accents_data # Enviamos el objeto completo (en, es, fr...)
        }
    except Exception as e:
        print(f"❌ Error cargando filtros: {e}")
        return {"levels": [], "topics": [], "content_types": [], "accents_data": {}}
    
    
@router.get("/{video_id}", response_model=VideoResponse)
async def read_video(video_id: str, db: AsyncSession = Depends(get_db)):
    query = select(Video).where(Video.video_id == video_id)
    result = await db.execute(query)
    video = result.scalar_one_or_none()
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


# ==========================================
# 2. ZONA PRIVADA (ADMINISTRACIÓN)
#    Requiere Header: 'x-admin-key'
# ==========================================

@router.post("/batch/", response_model=dict,
    dependencies=[
        Depends(RateLimiter(times=5, seconds=60)),
        Depends(verify_admin_key) # <--- CANDADO 🔒
    ])
async def create_videos_batch(videos: List[VideoCreate], db: AsyncSession = Depends(get_db)):
    """
    🔒 PRIVADO: Carga masiva.
    """
    if len(videos) > 50: raise HTTPException(400, "Límite: 50 videos por batch")
    created, ignored = 0, 0
    for vid in videos:
        res = await db.execute(select(Video).where(Video.video_id == vid.video_id))
        if res.scalar_one_or_none():
            ignored += 1
            continue
        db.add(Video(**vid.model_dump()))
        created += 1
    await db.commit()
    return {"status": "success", "created": created, "ignored": ignored}


# --- CREATE VIDEO (MANUAL) ---
@router.post("/", response_model=VideoResponse)
async def create_video(video: VideoCreate, db: AsyncSession = Depends(get_db)):
    # Verificar si existe
    query = select(Video).where(Video.video_id == video.video_id)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Video ID already exists")

    new_video = Video(**video.model_dump())
    db.add(new_video)
    await db.commit()
    await db.refresh(new_video)
    return new_video

@router.patch("/{video_id}", response_model=VideoResponse,
    dependencies=[Depends(verify_admin_key)]) # <--- CANDADO 🔒
async def update_video(video_id: str, video_update: VideoUpdate, db: AsyncSession = Depends(get_db)):
    """
    🔒 PRIVADO: Editar video.
    """
    res = await db.execute(select(Video).where(Video.video_id == video_id))
    db_video = res.scalar_one_or_none()
    if not db_video: raise HTTPException(404, "Video no encontrado")
    
    for key, value in video_update.model_dump(exclude_unset=True).items():
        setattr(db_video, key, value)
    
    await db.commit()
    await db.refresh(db_video)
    return db_video


@router.delete("/{video_id}",
    dependencies=[Depends(verify_admin_key)]) # <--- CANDADO 🔒
async def delete_video(video_id: str, db: AsyncSession = Depends(get_db)):
    """
    🔒 PRIVADO: Eliminar video.
    """
    res = await db.execute(select(Video).where(Video.video_id == video_id))
    db_video = res.scalar_one_or_none()
    if not db_video: raise HTTPException(404, "Video no encontrado")
    
    await db.delete(db_video)
    await db.commit()
    return {"message": "Eliminado"}