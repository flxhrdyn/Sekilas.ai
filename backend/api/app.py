from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from pathlib import Path
from contextlib import asynccontextmanager

from backend.api.routes import digest, search, qa
from backend.config.logging import setup_logging
from backend.config.settings import ROOT_DIR, get_settings

setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Model dimuat secara lazy saat request pertama masuk (via Singleton)
    # Tidak ada pre-loading di sini agar server bisa shutdown dengan bersih
    yield

app = FastAPI(
    title="Sekilas.ai API",
    description="Backend API for Sekilas.ai Agentic-RAG News System",
    version="0.2.0",
    lifespan=lifespan
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(digest.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(qa.router, prefix="/api")

@app.get("/api/health")
def health_check():
    return {"status": "online", "system": "Sekilas.ai"}

# -- Frontend Integration --

# Tentukan lokasi folder build React
FRONTEND_DIST = ROOT_DIR / "frontend" / "dist"

# Jika folder dist ada (hasil build), layani file statisnya
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")

    # Catch-all route untuk mendukung Client-Side Routing React (SPA)
    @app.exception_handler(404)
    async def custom_404_handler(request: Request, _):
        if not request.url.path.startswith("/api"):
            return FileResponse(FRONTEND_DIST / "index.html")
        return {"detail": "Not Found"}
else:
    @app.get("/")
    def root_warning():
        return {
            "message": "Backend Online. Folder frontend/dist tidak ditemukan. Pastikan sudah menjalankan 'npm run build' di folder frontend.",
            "status": "online"
        }
