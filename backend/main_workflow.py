import asyncio
import os
import json
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# --- TUS MÓDULOS ---
# Asegúrate de que las carpetas existen: functions/ y models/
from functions.Metadata import VideoMetadataExtractor, get_videos_from_playlist
from functions.AI_Service import generate_response as analyze_with_ai
from database import AsyncSessionLocal, engine, Base
from models.video import Video, CefrEnum, SubSourceEnum

# --- CONFIGURACIÓN DE ARCHIVOS ---
STATE_FILE = "Data/crawler_state.json"
PLAYLIST_FILE = "Data/Playlists.txt"

# --- CLASE PRINCIPAL ---
class VideoPipeline:
    def __init__(self):
        self.extractor = VideoMetadataExtractor()

    async def init_db_schema(self):
        """Crea las tablas en PostgreSQL si no existen."""
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            print("📦 Esquema de base de datos verificado/creado.")

    async def get_existing_ids(self, video_ids: list[str]) -> set[str]:
        """Consulta la DB y devuelve un SET con los IDs que YA existen."""
        existing = set()
        if not video_ids: 
            return existing
        
        async with AsyncSessionLocal() as session:
            # Procesamos en bloques para no saturar la query
            chunk_size = 500 
            for i in range(0, len(video_ids), chunk_size):
                chunk = video_ids[i:i + chunk_size]
                # Nota: Video.video_id debe coincidir con tu modelo
                result = await session.execute(
                    select(Video.video_id).where(Video.video_id.in_(chunk))
                )
                for row in result:
                    existing.add(row[0])
        return existing

    async def save_video_to_db(self, final_data: dict):
        """Guarda o actualiza el video en la base de datos."""
        async with AsyncSessionLocal() as session:
            async with session.begin():
                try:
                    # 1. Validación y Conversión de Datos
                    
                    # Validar Enum de Nivel
                    level_val = final_data.get("level")
                    if level_val not in [e.value for e in CefrEnum]:
                        level_val = None 

                    # Validar Fuente Subtítulos
                    sub_source_val = final_data.get("subtitle_source", "none")
                    if sub_source_val not in [e.value for e in SubSourceEnum]:
                        sub_source_val = "none"
                    
                    # Convertir strings únicos a Listas para los ARRAYs de Postgres
                    accent_val = final_data.get("accent", "Mixed")
                    accent_list = [accent_val] if isinstance(accent_val, str) else accent_val

                    type_val = final_data.get("type", "General")
                    type_list = [type_val] if isinstance(type_val, str) else type_val

                    topics_list = final_data.get("topics", [])

                    # 2. Crear Objeto ORM
                    video_entry = Video(
                        video_id=final_data["video_id"],
                        title=final_data["title"],
                        url=final_data["url"],
                        channel_name=final_data["channel"],
                        
                        # Arrays
                        topics=topics_list,
                        accents=accent_list,
                        content_types=type_list,
                        
                        # Enums y Métricas
                        level=level_val,
                        wpm=final_data["wpm"],
                        subtitle_source=sub_source_val,
                        
                        # JSONB (Respaldo crudo de la IA)
                        ai_analysis=final_data.get("ai_raw_output", {})
                    )

                    # 3. Upsert (Merge)
                    await session.merge(video_entry)
                    print(f"💾 Guardado en DB: {final_data['title'][:40]}...")
                
                except Exception as e:
                    print(f"❌ Error guardando SQL {final_data.get('video_id')}: {e}")
                    await session.rollback()

    async def process_single_video(self, url: str):
        """Orquesta: Extracción -> IA -> Guardado"""
        try:
            # 1. Extracción de Metadatos (Youtube)
            metadata = await self.extractor.process_video(url)
            
            if not metadata:
                return # Falló la descarga o no tiene subtítulos

            # 2. Análisis de IA
            transcript = metadata.get("transcript_full", "")
            
            # Filtro: Si es muy corto, no gastamos IA
            if not transcript or len(transcript) < 50:
                print(f"⚠️ Transcript vacío o muy corto: {url}")
                return

            print(f"🧠 Enviando a IA: {metadata['title'][:30]}...")
            ai_result = await analyze_with_ai(transcript)
            
            if not ai_result or "error" in ai_result:
                print(f"⚠️ Fallo en respuesta IA: {ai_result}")
                return

            # 3. Fusión de Datos
            final_package = {
                **metadata,      # Datos técnicos (wpm, duration...)
                **ai_result,     # Datos lingüísticos (level, topics...)
                "ai_raw_output": ai_result
            }

            # 4. Guardar
            await self.save_video_to_db(final_package)
            
        except Exception as e:
            print(f"❌ Error procesando video {url}: {e}")

# --- GESTIÓN DE ESTADO (MEMORIA DEL CRAWLER) ---

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except:
            return {"current_index": 0}
    return {"current_index": 0}

def save_state(index):
    with open(STATE_FILE, "w") as f:
        json.dump({
            "current_index": index,
            "last_updated": str(datetime.now())
        }, f, indent=4)

def load_playlists():
    if not os.path.exists(PLAYLIST_FILE):
        return []
    with open(PLAYLIST_FILE, "r") as f:
        # Ignora líneas vacías o comentarios (#)
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

# --- FUNCIÓN PRINCIPAL ---

async def main():
    # 0. Inicialización
    pipeline = VideoPipeline()
    await pipeline.init_db_schema()

    # --- CONFIGURACIÓN DE LA TANDA ---
    VIDEOS_PER_RUN = 50        # Cuántos videos procesar hoy
    CONCURRENT_WORKERS = 1    # Cuántos hilos simultáneos

    # 1. Cargar Estado y Playlists
    playlists = load_playlists()
    state = load_state()
    current_idx = state.get("current_index", 0)

    if not playlists:
        print(f"⚠️ El archivo {PLAYLIST_FILE} está vacío o no existe.")
        return

    # Corrección de índice por si borraste playlists del archivo txt
    if current_idx >= len(playlists):
        current_idx = 0

    target_playlist = playlists[current_idx]
    print(f"\n📂 Estado Cargado | Playlist actual: #{current_idx} ({target_playlist[-15:]}...)")
    
    videos_to_process = []
    
    try:
        # 2. Obtener videos de la playlist objetivo
        print("📡 Obteniendo lista de videos desde YouTube...")
        all_urls = get_videos_from_playlist(target_playlist)
        
        # Recortamos la búsqueda a los primeros 50 para no analizar listas de 2000 videos
        # Asumiendo que los videos nuevos salen arriba.
        candidate_urls = all_urls[:50] 
        
        # 3. Extraer IDs para verificar en DB
        url_map = {}
        for url in candidate_urls:
            # Extraer ID de la URL estándar de YouTube
            if "v=" in url:
                try:
                    vid_id = url.split("v=")[1].split("&")[0]
                    url_map[vid_id] = url
                except:
                    pass
        
        candidate_ids = list(url_map.keys())
        
        # 4. Filtro: ¿Cuáles ya tenemos?
        existing_ids = await pipeline.get_existing_ids(candidate_ids)
        new_ids = [vid for vid in candidate_ids if vid not in existing_ids]
        
        print(f"📊 Análisis: {len(candidate_ids)} escaneados | {len(existing_ids)} ya existen | {len(new_ids)} NUEVOS.")

        if not new_ids:
            # CASO A: No hay nada nuevo en esta playlist -> ESTÁ COMPLETADA
            print("✅ Playlist al día. Avanzando al siguiente índice.")
            
            # Avanzamos índice (Circular)
            next_index = (current_idx + 1) % len(playlists)
            save_state(next_index)
            print(f"⏭️ Próxima ejecución será en Playlist #{next_index}")

        else:
            # CASO B: Hay videos nuevos -> A TRABAJAR
            count_to_do = min(len(new_ids), VIDEOS_PER_RUN)
            print(f"🔨 Procesando lote de {count_to_do} videos...")
            
            ids_to_do = new_ids[:count_to_do]
            for vid_id in ids_to_do:
                videos_to_process.append(url_map[vid_id])
            
            # NOTA: NO avanzamos el índice.
            # La próxima vez volveremos a esta playlist para terminar los que faltaron.

    except Exception as e:
        print(f"❌ Error crítico leyendo playlist: {e}")
        # Opcional: Avanzar índice si la playlist está rota/privada
        # save_state((current_idx + 1) % len(playlists))

    # 5. Ejecución del Trabajo (Crawler)
    if videos_to_process:
        print(f"🚀 Iniciando workers ({CONCURRENT_WORKERS} simultáneos)...")
        semaphore = asyncio.Semaphore(CONCURRENT_WORKERS)

        async def worker(url):
            async with semaphore:
                await pipeline.process_single_video(url)

        tasks = [worker(url) for url in videos_to_process]
        await asyncio.gather(*tasks)
        print("\n✨ Tanda finalizada con éxito.")
    else:
        print("\n💤 Sin tareas pendientes por hoy.")

if __name__ == "__main__":
    # Verificación de entorno
    if not os.getenv("GROQ_API_KEY"):
        print("❌ ERROR: No se encontró la variable de entorno GROQ_API_KEY")
        print("   Ejecuta: export GROQ_API_KEY='tu_api_key' (Linux/Mac) o $env:GROQ_API_KEY='tu_api_key' (Windows)")
    else:
        asyncio.run(main())