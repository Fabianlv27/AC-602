import asyncio
import os
import json
import time
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# --- TUS MÓDULOS ---
from functions.Metadata import VideoMetadataExtractor, get_videos_from_playlist
from functions.AI_Service import generate_response as analyze_with_ai
from database import AsyncSessionLocal, engine, Base
from models.video import Video, CefrEnum, SubSourceEnum

TOTAL_HOURS_TO_RUN = 2      # Duración total del script (horas de sueño)
BATCH_SIZE = 50             # Videos por tanda (Para no saturar memoria)
COOLDOWN_MINUTES = 15       # Descanso entre tandas (Para proteger IP)
CONCURRENT_WORKERS = 1      # OBLIGATORIO: 1 para Selenium

# --- CONFIGURACIÓN DE ARCHIVOS ---
STATE_FILE = "Data/crawler_state.json"
PLAYLIST_FILE = "Data/Playlists.txt"

# --- CLASE PRINCIPAL (PIPELINE) ---
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
            chunk_size = 500 
            for i in range(0, len(video_ids), chunk_size):
                chunk = video_ids[i:i + chunk_size]
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
                    # 1. Extracción de datos para COLUMNAS SQL (Filtrado)
                    level_val = final_data.get("level")
                    if level_val not in [e.value for e in CefrEnum]:
                        level_val = None 
                    
                    sub_source_val = final_data.get("subtitle_source", "none")
                    if sub_source_val not in [e.value for e in SubSourceEnum]:
                        sub_source_val = "none"

                    # Arrays
                    accents_list = final_data.get("accents", [])
                    if isinstance(accents_list, str): accents_list = [accents_list]
                    
                    types_list = final_data.get("content_types", [])
                    if isinstance(types_list, str): types_list = [types_list]

                    topics_list = final_data.get("topics", [])

                    # 2. Construcción del JSON LIMPIO (ai_analysis)
                    # --- CAMBIO AQUÍ: Eliminados 'summary' y 'functional_use' ---
                    ai_clean_json = {
                        "transcript_summary": final_data.get("transcript_summary"),
                        "vocabulary": final_data.get("vocabulary", []),
                        "grammar_stats": final_data.get("grammar_stats", {}),
                        "wpm_estimate": final_data.get("wpm_estimate")
                    }

                    # --- CREACIÓN DEL OBJETO ---
                    video_entry = Video(
                        video_id=final_data["video_id"],
                        title=final_data["title"],
                        url=final_data["url"],
                        channel_name=final_data["channel"],                        
                        # --- COLUMNAS SQL ---
                        topics=topics_list,
                        accents=accents_list,
                        content_types=types_list,
                        level=level_val,
                        wpm=final_data["wpm"],
                        subtitle_source=sub_source_val,
                        language=final_data.get("language", "en"), 
                        
                        # --- DATOS DE TEXTO ---
                        transcript=None, # No guardamos texto plano para ahorrar espacio
                        transcript_json=final_data.get("transcript_json", []),
                        
                        # --- COLUMNA JSON ---
                        ai_analysis=ai_clean_json
                    )

                    await session.merge(video_entry)
                    print(f"💾 Guardado optimizado en DB: {final_data['title'][:40]}...")
                
                except Exception as e:
                    print(f"❌ Error guardando SQL {final_data.get('video_id')}: {e}")
                    await session.rollback()
                    
    async def process_single_video(self, url: str):
        """Orquesta: Extracción -> IA (con contexto de país) -> Guardado"""
        try:
            # 1. Extracción de Metadatos
            metadata = await self.extractor.process_video(url)
            
            if not metadata:
                return 

            # 2. Preparar datos para la IA
            transcript = metadata.get("transcript_full", "")
            country = metadata.get("channel_country", "Desconocido")
            
            if not transcript or len(transcript) < 50:
                print(f"⚠️ Transcript vacío o muy corto: {url}")
                return

            print(f"🧠 Enviando a IA: {metadata['title'][:30]}... (Origen: {country})")
            
            # --- TRUCO: INYECTAR EL PAÍS EN EL PROMPT ---
            # Concatenamos el país al principio del texto para que la IA lo sepa
            prompt_con_contexto = (
                f"CONTEXTO DEL CANAL: El creador del video está ubicado en: {country}. "
                f"Usa esto para determinar el acento exacto (ej: si es ES -> Spain, si es AR -> Argentino).\n\n"
                f"TRANSCRIPCIÓN DEL VIDEO:\n{transcript}"
            )
            
            # Llamamos a la IA con el texto enriquecido
            ai_result = await analyze_with_ai(prompt_con_contexto)
            
            if not ai_result or "error" in ai_result:
                print(f"⚠️ Fallo en respuesta IA: {ai_result}")
                return

            # 3. Fusión de Datos (Aquí el country se queda en metadata pero no lo guardamos)
            final_package = {
                **metadata,
                **ai_result,
                "ai_raw_output": ai_result
            }

            # 4. Guardar
            await self.save_video_to_db(final_package)
            
        except Exception as e:
            print(f"❌ Error procesando video {url}: {e}")
# --- GESTIÓN DE ESTADO ---

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
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

# --- LOGICA DE TANDA INDIVIDUAL ---

async def run_batch_cycle(pipeline):
    """
    Ejecuta UNA tanda de trabajo (máximo BATCH_SIZE videos).
    Retorna: int (número de videos procesados realmente)
    """
    playlists = load_playlists()
    state = load_state()
    current_idx = state.get("current_index", 0)

    if not playlists:
        print(f"⚠️ El archivo {PLAYLIST_FILE} está vacío.")
        return 0

    if current_idx >= len(playlists):
        current_idx = 0

    target_playlist = playlists[current_idx]
    print(f"\n📂 Analizando Playlist #{current_idx}: {target_playlist[-15:]}...")
    
    videos_to_process = []
    
    try:
        # Obtener lista rápida (yt-dlp flat)
        all_urls = get_videos_from_playlist(target_playlist)
        # Analizamos los primeros 60 para tener margen sobre el BATCH_SIZE de 50
        candidate_urls = all_urls[:(BATCH_SIZE + 10)]
        
        url_map = {}
        for url in candidate_urls:
            if "v=" in url:
                try:
                    vid_id = url.split("v=")[1].split("&")[0]
                    url_map[vid_id] = url
                except: pass
        
        candidate_ids = list(url_map.keys())
        existing_ids = await pipeline.get_existing_ids(candidate_ids)
        new_ids = [vid for vid in candidate_ids if vid not in existing_ids]
        
        print(f"📊 Estado Playlist: {len(new_ids)} videos nuevos disponibles.")

        if not new_ids:
            # Playlist completada, pasamos a la siguiente
            print("✅ Playlist al día. Cambiando índice...")
            next_index = (current_idx + 1) % len(playlists)
            save_state(next_index)
            return 0 # No procesamos nada, devolvemos 0
        else:
            # Hay trabajo, seleccionamos lote
            count_to_do = min(len(new_ids), BATCH_SIZE)
            print(f"🔨 Agregando {count_to_do} videos a la cola de trabajo...")
            
            ids_to_do = new_ids[:count_to_do]
            for vid_id in ids_to_do:
                videos_to_process.append(url_map[vid_id])
            
            # Procesamiento
            if videos_to_process:
                print(f"🚀 Ejecutando Workers (Simultáneos: {CONCURRENT_WORKERS})...")
                semaphore = asyncio.Semaphore(CONCURRENT_WORKERS)

                async def worker(url):
                    async with semaphore:
                        await pipeline.process_single_video(url)

                tasks = [worker(url) for url in videos_to_process]
                await asyncio.gather(*tasks)
                print("✨ Tanda terminada.")
                return len(videos_to_process)
            
            return 0

    except Exception as e:
        print(f"❌ Error en run_batch_cycle: {e}")
        return 0

# --- CONTROLADOR PILOTO AUTOMÁTICO ---

async def autopilot_main():
    """
    Bucle principal que gestiona el tiempo total y los descansos.
    """
    pipeline = VideoPipeline()
    await pipeline.init_db_schema()
    
    end_time = datetime.now() + timedelta(hours=TOTAL_HOURS_TO_RUN)
    
    print("\n" + "="*50)
    print(f"🤖 PILOTO AUTOMÁTICO ACTIVADO")
    print(f"🕒 Inicio: {datetime.now().strftime('%H:%M:%S')}")
    print(f"🛑 Fin programado: {end_time.strftime('%H:%M:%S')}")
    print(f"📦 Config: {BATCH_SIZE} videos/tanda | {COOLDOWN_MINUTES} min descanso")
    print("="*50 + "\n")

    while datetime.now() < end_time:
        
        start_t = time.time()
        
        # EJECUTAR UNA TANDA
        processed_count = await run_batch_cycle(pipeline)
        
        elapsed = time.time() - start_t
        
        # VERIFICAR SI QUEDA TIEMPO
        time_left = end_time - datetime.now()
        if time_left.total_seconds() <= 0:
            break

        # LOGICA DE DESCANSO
        if processed_count > 0:
            # Si trabajamos, descansamos para enfriar IP y RAM
            print(f"\n❄️ Tanda de {processed_count} videos completada en {int(elapsed)}s.")
            print(f"💤 ENFRIANDO MOTORES: Durmiendo {COOLDOWN_MINUTES} minutos...")
            time.sleep(COOLDOWN_MINUTES * 60)
            print("🔔 Despertando para nueva tanda...\n")
        
        else:
            # Si NO trabajamos (playlist vacía), esperamos solo un poco antes de
            # probar la siguiente playlist, para no saturar logs si hay muchas vacías.
            print("⏩ Playlist vacía o error. Saltando brevemente (30s)...")
            time.sleep(30)

    print("\n🎉 TIEMPO CUMPLIDO. El Piloto Automático ha finalizado su turno.")

if __name__ == "__main__":
    if not os.getenv("GROQ_API_KEY"):
        print("❌ ERROR: Falta GROQ_API_KEY")
    else:
        try:
            asyncio.run(autopilot_main())
        except KeyboardInterrupt:
            print("\n🛑 Detenido manualmente por el usuario.")
            # Opcional: os.system("shutdown /s /t 60")