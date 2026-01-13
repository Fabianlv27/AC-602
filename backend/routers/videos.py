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
@router.get("/", response_model=List[VideoResponse], 
    dependencies=[Depends(RateLimiter(times=20, seconds=60))]) 
async def read_videos(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    
    # --- TUS FILTROS ---
    search: Optional[str] = Query(None, description="Busca en título"),
    topic: Optional[str] = Query(None, description="Tag/Tema del video"),
    level: Optional[CefrEnum] = Query(None, description="Nivel A1-C2"),
    source: Optional[SubSourceEnum] = Query(None, description="manual, generated, none"),
    accent: Optional[str] = Query(None, description="Acento (ej: British, American)"),
    type: Optional[str] = Query(None, description="formal, informal, dia a dia"),
    
    # Filtro especial de velocidad (Lento/Normal/Rápido)
    speed: Optional[str] = Query(None, description="slow, normal, fast"),
    language: Optional[str] = Query(None, description="Código de idioma: en, es, fr..."),
    
    db: AsyncSession = Depends(get_db)
):
    query = select(Video)

    if language:
        query=query.where(Video.language==language)
    # 1. Filtro por Título (Búsqueda general)
    if search:
        query = query.where(Video.title.ilike(f"%{search}%"))

    # 2. Tag / Tema (Busca dentro del array topics)
    if topic:
        query = query.where(Video.topics.contains([topic]))

    # 3. Nivel (Exacto)
    if level:
        query = query.where(Video.level == level)

    # 4. Subtítulos (Exacto: manual, generated, none)
    if source:
        query = query.where(Video.subtitle_source == source)

    # 5. Acento (Busca dentro del array accents)
    if accent:
        query = query.where(Video.accents.contains([accent]))

    # 6. Tipo (Busca dentro del array content_types)
    # Nota: Tu base de datos guarda esto como array, así que usamos contains
    if type:
        query = query.where(Video.content_types.contains([type]))

    # 7. LÓGICA DE VELOCIDAD (WPM)
    # Convertimos "lento/normal/rápido" a rangos numéricos
    if speed == 'slow':
        # Menos de 120 palabras por minuto
        query = query.where(Video.wpm < 120)
    elif speed == 'normal':
        # Entre 120 y 160 wpm
        query = query.where(and_(Video.wpm >= 120, Video.wpm <= 160))
    elif speed == 'fast':
        # Más de 160 wpm
        query = query.where(Video.wpm > 160)

    # Ordenar por fecha y paginar
    query = query.order_by(Video.created_at.desc()).offset(skip).limit(limit)   
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/filters", response_model=dict)
async def get_video_filters():
    """
    Lee los archivos JSON de configuración y devuelve las opciones disponibles
    para llenar los selectores del Frontend.
    """
    # Calculamos la ruta absoluta a la carpeta Data
    # routers/videos.py está en backend/routers, así que subimos uno (..) y entramos a Data
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "Data")

    def load_json(filename):
        try:
            with open(os.path.join(data_dir, filename), 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return [] # Si no existe, devuelve lista vacía para no romper el front

    return {
        "levels": load_json("Niveles.json"),
        "types": load_json("Tipos.json"),
        "topics": load_json("Etiquetas.json"),
        "languages": load_json("accents.json")
    }

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