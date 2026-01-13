import logging
import time      # <--- Módulo correcto para dormir
import random    # <--- Para el tiempo aleatorio
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

# ==========================================
# 🌍 CONFIGURACIÓN MANUAL DE IDIOMA
# ==========================================
# Cambia esto a: 'en' (Inglés), 'es' (Español), 'fr' (Francés), 'de' (Alemán), etc.
TARGET_LANGUAGE = "en"
# ==========================================

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
        
    def _time_to_seconds(self, time_str: str) -> int:
        """Convierte '1:05' o '1:02:30' a segundos enteros"""
        try:
            parts = list(map(int, time_str.strip().split(':')))
            if len(parts) == 2:
                return parts[0] * 60 + parts[1]
            elif len(parts) == 3:
                return parts[0] * 3600 + parts[1] * 60 + parts[2]
            return 0
        except:
            return 0

    def _scrape_sync(self, url: str):
        data = None
        if "v=" in url:
            video_id = url.split("v=")[-1].split("&")[0]
        else:
            video_id = url.split("/")[-1]
        
        with SB(uc=True, test=True, headless=True, locale_code=TARGET_LANGUAGE) as sb:
            try:
                wait = random.uniform(4, 7)
                time.sleep(wait)
                
                logger.info(f"▶️ Procesando ({TARGET_LANGUAGE}): {video_id}...")
                
                sb.maximize_window()
                sb.activate_cdp_mode(url)
                
                # --- COOKIES ---
                sb.sleep(2)
                cookie_selectors = [
                    'button[aria-label*="Rechazar"]', 'button:contains("Rechazar")', 
                    'button[aria-label*="Reject"]', 'button:contains("Reject")',    
                    'form[action*="consent"] button',
                    'ytd-consent-bump-v2-lightbox button'
                ]
                for selector in cookie_selectors:
                    if sb.is_element_visible(selector):
                        sb.click(selector)
                        sb.sleep(1)
                        break

                if not sb.wait_for_element("#columns", timeout=20):
                    logger.warning(f"⚠️ Timeout cargando video: {video_id}")
                    return None
                
                # --- METADATOS BÁSICOS ---
                title = "Unknown"
                try: title = sb.get_text("h1.ytd-watch-metadata")
                except: pass

                channel = "Unknown"
                try: channel = sb.get_text("#owner-name a")
                except: pass

                duration = 0
                try:
                    dur_str = sb.get_text(".ytp-time-duration")
                    duration = self._parse_duration(dur_str)
                except: duration = 600

                thumbnail = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"

                # --- TRANSCRIPCIÓN ---
                transcript_text = ""
                sub_source = "none"
                transcript_structured = []

                try:
                    # 1. Expandir descripción
                    sb.execute_script("window.scrollBy(0, 300);")
                    sb.sleep(1)

                    expand_selectors = ["#expand", "#description-inline-expander", "tp-yt-paper-button#more"]
                    for exp in expand_selectors:
                        if sb.is_element_visible(exp):
                            try: sb.click(exp); sb.sleep(0.5)
                            except: pass

                    # 2. Buscar y Clicar Botón Transcripción
                    found_btn = False
                    search_texts = ["Show transcript", "Open transcript"] if TARGET_LANGUAGE == 'en' else ["Mostrar transcripción", "Abrir transcripción"]
                    
                    selectors = [
                        "ytd-video-description-transcript-section-renderer button", 
                        f'button[aria-label="{search_texts[0]}"]',
                        "#primary-button button"
                    ]

                    for btn in selectors:
                        if sb.is_element_present(btn):
                            try:
                                sb.scroll_to(btn)
                                sb.sleep(0.5)
                                sb.click(btn)
                                found_btn = True
                                logger.info("Botón encontrado y clickeado.")
                                break
                            except:
                                try:
                                    sb.execute_script("arguments[0].click();", sb.get_element(btn))
                                    found_btn = True
                                    logger.info("Botón clickeado con JS.")
                                    break
                                except: pass

                    if found_btn:
                        logger.info("Esperando carga de segmentos...")
                        
                        # Esperamos a que aparezcan los elementos de texto
                        is_loaded = sb.wait_for_element(".segment-text", timeout=10)
                        
                        if is_loaded:
                            sb.sleep(1) 
                            
                            # --- CORRECCIÓN AQUÍ: JavaScript ES5 (Más compatible) ---
                            # Usamos un bucle for clásico y var en lugar de map/const para evitar errores
                            transcript_data = sb.execute_script("""
                                var segments = document.querySelectorAll('ytd-transcript-segment-renderer');
                                var result = [];
                                for (var i = 0; i < segments.length; i++) {
                                    var seg = segments[i];
                                    var timeEl = seg.querySelector('.segment-timestamp');
                                    var textEl = seg.querySelector('.segment-text');
                                    
                                    if (textEl) {
                                        result.push({
                                            'timeStr': timeEl ? timeEl.textContent.trim() : "0:00",
                                            'text': textEl.textContent.trim()
                                        });
                                    }
                                }
                                return result;
                            """)
                            
                            full_text_list = []
                            if transcript_data:
                                for item in transcript_data:
                                    clean_text = re.sub(self.clean_regex, "", item['text']).replace("\n", " ").strip()
                                    if clean_text:
                                        seconds = self._time_to_seconds(item['timeStr'])
                                        transcript_structured.append({
                                            "start": seconds,
                                            "text": clean_text
                                        })
                                        full_text_list.append(clean_text)
                            
                                transcript_text = " ".join(full_text_list)
                                sub_source = "manual"
                                logger.info(f"📝 Transcripción extraída: {len(transcript_structured)} líneas.")
                            else:
                                logger.warning("El script JS retornó una lista vacía.")

                        else:
                            logger.warning("El panel se abrió pero no cargaron los segmentos (.segment-text).")
                                
                except Exception as e:
                    logger.warning(f"⚠️ Error intentando extraer subs: {str(e)}")

                if not transcript_text:
                    logger.warning(f"❌ Sin subtítulos (o no se pudieron extraer): {title[:30]}...")
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
                    "transcript_full": transcript_text,
                    "transcript_json": transcript_structured,               
                    "language": TARGET_LANGUAGE, 
                    "accents": []                
                }

            except Exception as e:
                logger.error(f"❌ Error en {video_id}: {str(e)[:50]}...")
                return None
        
        return data
    async def process_video(self, url: str):
        try:
            return await asyncio.to_thread(self._scrape_sync, url)
        except Exception as e:
            logger.error(f"Error thread: {e}")
            return None

# --- Helpers (Igual que antes) ---
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