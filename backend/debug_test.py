import youtube_transcript_api
from youtube_transcript_api import YouTubeTranscriptApi
import os

print("--- REPORTE DE DEBUG ---")
print(f"1. Ubicación de la librería: {os.path.dirname(youtube_transcript_api.__file__)}")
print(f"2. Versión (si existe): {getattr(youtube_transcript_api, '__version__', 'No encontrada')}")
print("3. ¿Existe get_transcript?:", hasattr(YouTubeTranscriptApi, 'get_transcript'))
print("4. ¿Existe list_transcripts?:", hasattr(YouTubeTranscriptApi, 'list_transcripts'))
print("------------------------")