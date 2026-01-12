import uvicorn
import redis.asyncio as redis
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter

# Importamos el router
from routers import videos

# --- CONFIGURACIÓN DE REDIS ---
# Asegúrate de que Redis esté corriendo (Docker o local)
REDIS_URL = "redis://localhost:6379"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. AL INICIAR: Conectar a Redis
    try:
        redis_connection = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
        await FastAPILimiter.init(redis_connection)
        print("✅ Redis conectado y Rate Limiter activado.")
    except Exception as e:
        print(f"❌ Error conectando a Redis: {e}")
    
    yield # Aquí corre la aplicación
    
    # 2. AL APAGAR: Cerrar conexión
    await redis_connection.close()

# Inyectamos el lifespan en la app
app = FastAPI(
    title="AC602 English Learning API", 
    version="1.0.0",
    lifespan=lifespan 
)

# Configuración CORS (Igual que antes)
origins = ["http://localhost:3000", "http://localhost:5173", "*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(videos.router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)