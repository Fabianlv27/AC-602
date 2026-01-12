import os
from fastapi import APIRouter, Depends, HTTPException, Query, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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

@router.get("/", response_model=List[VideoResponse], 
    dependencies=[Depends(RateLimiter(times=20, seconds=60))]) 
async def read_videos(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    search: Optional[str] = None,
    channel: Optional[str] = None,
    topic: Optional[str] = None,
    accent: Optional[str] = None,
    ctype: Optional[str] = None,
    level: Optional[CefrEnum] = None,
    source: Optional[SubSourceEnum] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    🔍 PÚBLICO: Buscador de videos.
    """
    query = select(Video)

    if search: query = query.where(Video.title.ilike(f"%{search}%"))
    if channel: query = query.where(Video.channel_name.ilike(f"%{channel}%"))
    if topic: query = query.where(Video.topics.contains([topic]))
    if accent: query = query.where(Video.accents.contains([accent]))
    if ctype: query = query.where(Video.content_types.contains([ctype]))
    if level: query = query.where(Video.level == level)
    if source: query = query.where(Video.subtitle_source == source)

    query = query.order_by(Video.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{video_id}", response_model=VideoResponse,
    dependencies=[Depends(RateLimiter(times=60, seconds=60))])
async def read_video(video_id: str, db: AsyncSession = Depends(get_db)):
    """
    🔍 PÚBLICO: Ver detalle de un video.
    """
    query = select(Video).where(Video.video_id == video_id)
    result = await db.execute(query)
    video = result.scalar_one_or_none()
    if not video: raise HTTPException(status_code=404, detail="Video no encontrado")
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


@router.post("/", response_model=VideoResponse,
    dependencies=[Depends(verify_admin_key)]) # <--- CANDADO 🔒
async def create_video(video: VideoCreate, db: AsyncSession = Depends(get_db)):
    """
    🔒 PRIVADO: Crear un video manual.
    """
    res = await db.execute(select(Video).where(Video.video_id == video.video_id))
    if res.scalar_one_or_none(): raise HTTPException(400, "ID existente")
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