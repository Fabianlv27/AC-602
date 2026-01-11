import yt_dlp
import logging
import requests
import os
import json
from typing import Optional
import time
import random

# Configuración de logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VideoMetadataExtractor:
    def __init__(self):
        # Configuración base de yt-dlp
        self.ydl_opts = {
            'quiet': True,           # No llenar la consola de basura
            'skip_download': True,   # IMPORTANTE: No descargar el video, solo info
            'writesubtitles': True,  # Queremos buscar subs
            'writeautomaticsub': True,
            'subtitleslangs': ['en'], # Prioridad al inglés
            'cookiefile': 'Data/cookies.txt' if os.path.exists('Data/cookies.txt') else None
        }

    def _calculate_wpm(self, word_count: int, duration_seconds: float) -> int:
        if duration_seconds <= 0: return 0
        minutes = duration_seconds / 60
        return int(word_count / minutes)

    def _fetch_transcript_text(self, formats_list) -> str:
        """
        Descarga y parsea el subtítulo desde la URL que nos da yt-dlp.
        Prefiere formato JSON3 para parseo limpio, si no, baja VTT.
        """
        target_url = None
        
        # 1. Buscar formato JSON3 (es el más fácil de procesar limpio)
        for fmt in formats_list:
            if fmt.get('ext') == 'json3':
                target_url = fmt['url']
                break
        
        # 2. Si no hay JSON3, intentar cualquiera (VTT/SRV1)
        if not target_url and formats_list:
            target_url = formats_list[0]['url']

        if not target_url:
            return ""

        try:
            # Descargamos el contenido del subtítulo
            response = requests.get(target_url)
            response.raise_for_status()

            # Si es JSON3, lo procesamos bonito
            if 'json3' in target_url or target_url.endswith('json3'):
                data = response.json()
                text_segments = []
                # Navegar la estructura extraña de JSON3 de YouTube
                events = data.get('events', [])
                for event in events:
                    segs = event.get('segs', [])
                    for seg in segs:
                        if 'utf8' in seg and seg['utf8'] != '\n':
                            text_segments.append(seg['utf8'])
                return " ".join(text_segments).replace("\n", " ").strip()
            
            else:
                # Si es VTT/XML, respuesta cruda (limpieza básica)
                # Esto es un fallback, normalmente siempre hay json3
                return response.text

        except Exception as e:
            logger.error(f"Error descargando texto del subtítulo: {e}")
            return ""

    async def process_video(self, url: str):
        """
        Extrae metadatos y transcripción usando yt-dlp.
        """
        wait_time = random.uniform(15, 30) 
        logger.info(f"⏳ Enfriando motores... Esperando {wait_time:.1f}s")
        time.sleep(wait_time)
        try:
            # yt-dlp es sincrónico, pero rápido para metadatos.
            # Lo envolvemos en un bloque try para que no tumbe el programa.
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(url, download=False)
                except Exception as e:
                    logger.error(f"❌ Error yt-dlp extrayendo info de {url}: {e}")
                    return None

                video_id = info.get('id')
                title = info.get('title')
                channel_name = info.get('uploader')
                duration = info.get('duration', 0)
                thumbnail = info.get('thumbnail')
                
                # --- LÓGICA DE SUBTÍTULOS ---
                transcript_text = ""
                sub_source = "none"

                # 1. Buscar Manuales ('subtitles')
                subs_manual = info.get('subtitles', {})
                # 2. Buscar Automáticos ('automatic_captions')
                subs_auto = info.get('automatic_captions', {})

                # Preferencia: Inglés manual > Inglés auto
                # yt-dlp devuelve un diccionario: {'en': [...formatos...], 'es': ...}
                
                selected_subs = None
                
                # Buscar en manuales (en, en-US, en-GB)
                for lang in ['en', 'en-US', 'en-GB']:
                    if lang in subs_manual:
                        selected_subs = subs_manual[lang]
                        sub_source = 'manual'
                        break
                
                # Si no, buscar en automáticos
                if not selected_subs:
                    for lang in ['en', 'en-US', 'en-orig']:
                        if lang in subs_auto:
                            selected_subs = subs_auto[lang]
                            sub_source = 'generated'
                            break

                if selected_subs:
                    # Descargamos el texto real
                    transcript_text = self._fetch_transcript_text(selected_subs)
                
                if not transcript_text:
                    logger.warning(f"⚠️ Video sin subtítulos válidos: {title}")
                    return None

                # Métricas
                word_count = len(transcript_text.split())
                wpm = self._calculate_wpm(word_count, duration)

                logger.info(f"✅ Procesado (yt-dlp): {title[:30]}... ({sub_source})")

                return {
                    "video_id": video_id,
                    "url": url,
                    "title": title,
                    "channel": channel_name,
                    "duration_seconds": duration,
                    "thumbnail": thumbnail,
                    "wpm": wpm,
                    "subtitle_source": sub_source,
                    "transcript_full": transcript_text
                }

        except Exception as e:
            logger.error(f"Error general procesando {url}: {e}")
            return None

# Funciones Helper para las playlists (Compatibilidad)
def get_videos_from_playlist(playlist_url: str):
    # yt-dlp también es EXCELENTE sacando playlists rápido
    # Usamos 'extract_flat' para no analizar cada video, solo sacar la lista (muy rápido)
    opts = {
        'extract_flat': True, 
        'quiet': True,
        'skip_download': True
    }
    urls = []
    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            res = ydl.extract_info(playlist_url, download=False)
            if 'entries' in res:
                for entry in res['entries']:
                    # Construimos la URL completa
                    if entry.get('url'):
                         urls.append(entry['url'])
                    elif entry.get('id'):
                         urls.append(f"https://www.youtube.com/watch?v={entry['id']}")
        except Exception as e:
            print(f"Error leyendo playlist con yt-dlp: {e}")
    return urls

def get_videos_from_channel(channel_url, limit=10):
    # Reutilizamos la lógica de playlist, yt-dlp trata canales como playlists
    # Para el límite, yt-dlp tiene 'playlistend'
    opts = {
        'extract_flat': True, 
        'quiet': True,
        'skip_download': True,
        'playlistend': limit
    }
    urls = []
    with yt_dlp.YoutubeDL(opts) as ydl:
        res = ydl.extract_info(channel_url, download=False)
        if 'entries' in res:
            for entry in res['entries']:
                 urls.append(f"https://www.youtube.com/watch?v={entry['id']}")
    return urls