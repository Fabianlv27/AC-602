import logging
import time      # <--- ESTE es el módulo correcto para dormir (time.sleep)
import random    # <--- Necesario para el tiempo aleatorio
import re
import asyncio
from seleniumbase import SB
import yt_dlp

# --- CONFIGURACIÓN DE LOGS LIMPIA ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger("Scraper")

# Silenciar librerías ruidosas
logging.getLogger('seleniumbase').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('websockets').setLevel(logging.WARNING)
logging.getLogger('yt_dlp').setLevel(logging.ERROR)

class VideoMetadataExtractor:
    def __init__(self):
        self.clean_regex = re.compile(r"\[.*?\]|\(.*?\)")

    def _calculate_wpm(self, word_count: int, duration_seconds: float) -> int:
        if duration_seconds <= 0: return 0
        minutes = duration_seconds / 60
        return int(word_count / minutes)

    def _parse_duration(self, duration_str: str) -> int:
        try:
            parts = list(map(int, duration_str.split(':')))
            if len(parts) == 2:
                return parts[0] * 60 + parts[1]
            elif len(parts) == 3:
                return parts[0] * 3600 + parts[1] * 60 + parts[2]
            return 0
        except:
            return 0

    def _scrape_sync(self, url: str):
        data = None
        video_id = url.split("v=")[-1]
        
        # HEADLESS=TRUE: Invisible por defecto.
        # Cambia a False si quieres ver el navegador trabajando.
        with SB(uc=True, test=True, headless=True, locale_code="es") as sb:
            try:
                # --- PAUSA DE SEGURIDAD (ANTI-BLOQUEO) ---
                # Esperamos entre 5 y 10 segundos antes de empezar para parecer humanos
                wait = random.uniform(5, 10)
                # Usamos time.sleep aquí sin miedo porque los imports están arreglados
                time.sleep(wait)
                
                logger.info(f"▶️ Procesando: {video_id}...")
                
                sb.maximize_window()
                sb.activate_cdp_mode(url)
                
                # --- COOKIES ---
                sb.sleep(2)
                cookie_selectors = [
                    'button[aria-label="Rechazar todo"]', 'button:contains("Rechazar todo")',
                    'button[aria-label="Aceptar todo"]', 'button:contains("Aceptar todo")',
                    'form[action*="consent"] button'
                ]
                for selector in cookie_selectors:
                    if sb.is_element_visible(selector):
                        sb.click(selector)
                        sb.sleep(1)
                        break

                if not sb.wait_for_element("#columns", timeout=15):
                    logger.warning(f"⚠️ Timeout cargando video: {video_id}")
                    return None
                
                # --- METADATOS ---
                title = "Unknown"
                try: title = sb.get_text("h1.ytd-watch-metadata")
                except: pass

                channel = "Unknown"
                selectors = ["#owner-name a", "#upload-info a", "ytd-channel-name a"]
                for sel in selectors:
                    if sb.is_element_visible(sel):
                        channel = sb.get_text(sel)
                        break

                duration = 0
                try:
                    dur_str = sb.get_text(".ytp-time-duration")
                    duration = self._parse_duration(dur_str)
                except: duration = 600

                thumbnail = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"

                # --- TRANSCRIPCIÓN ---
                transcript_text = ""
                sub_source = "none"

                try:
                    # Expandir descripción
                    if sb.is_element_visible("#expand"): sb.click("#expand")
                    elif sb.is_element_visible("#description-inline-expander"): sb.click("#description-inline-expander")
                    sb.sleep(1)

                    # Buscar botón transcripción
                    found = False
                    btns = [
                        'button[aria-label="Mostrar transcripción"]', 'button:contains("Mostrar transcripción")',
                        'button[aria-label="Show transcript"]', 'button:contains("Show transcript")',
                        '#primary-button button'
                    ]
                    for btn in btns:
                        if sb.is_element_present(btn):
                            try: sb.scroll_to(btn)
                            except: pass
                            sb.click(btn)
                            found = True
                            break

                    if found:
                        sb.sleep(1)
                        # Scroll al panel
                        if sb.is_element_visible("ytd-transcript-renderer"):
                            sb.scroll_to("ytd-transcript-renderer")
                        else:
                            sb.execute_script("window.scrollBy(0, 400);")
                        
                        sb.sleep(2)

                        # Extraer texto
                        if sb.wait_for_element(".segment-text", timeout=10):
                            segments = sb.find_elements(".segment-text")
                            full_text = [s.text for s in segments]
                            transcript_text = " ".join(full_text).replace("\n", " ")
                            transcript_text = re.sub(self.clean_regex, "", transcript_text)
                            if transcript_text: sub_source = "manual"

                except Exception:
                    pass 

                if not transcript_text:
                    logger.warning(f"❌ Sin subtítulos: {title[:20]}...")
                    return None

                # Métricas
                word_count = len(transcript_text.split())
                wpm = self._calculate_wpm(word_count, duration)

                logger.info(f"✅ OK: {title[:40]}... | 🗣️ {channel} | ⚡ {wpm} WPM")

                data = {
                    "video_id": video_id,
                    "url": url,
                    "title": title,
                    "channel": channel,
                    "duration_seconds": duration,
                    "thumbnail": thumbnail,
                    "wpm": wpm,
                    "subtitle_source": sub_source,
                    "transcript_full": transcript_text
                }

            except Exception as e:
                # Mostramos solo el mensaje corto del error para no ensuciar
                logger.error(f"❌ Error en {video_id}: {str(e)[:50]}...")
                return None
        
        return data

    async def process_video(self, url: str):
        try:
            return await asyncio.to_thread(self._scrape_sync, url)
        except Exception as e:
            logger.error(f"Error thread: {e}")
            return None

# --- Helpers (Silenciados) ---
def get_videos_from_playlist(playlist_url: str):
    opts = {'extract_flat': True, 'quiet': True, 'skip_download': True}
    urls = []
    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            res = ydl.extract_info(playlist_url, download=False)
            if 'entries' in res:
                for entry in res['entries']:
                    if entry.get('url'): urls.append(entry['url'])
                    elif entry.get('id'): urls.append(f"https://www.youtube.com/watch?v={entry['id']}")
        except: pass
    return urls

def get_videos_from_channel(channel_url, limit=10):
    opts = {'extract_flat': True, 'quiet': True, 'skip_download': True, 'playlistend': limit}
    urls = []
    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            res = ydl.extract_info(channel_url, download=False)
            if 'entries' in res:
                for entry in res['entries']:
                     urls.append(f"https://www.youtube.com/watch?v={entry['id']}")
        except: pass
    return urls