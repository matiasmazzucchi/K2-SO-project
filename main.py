"""
Aplicación principal del bot K2-SO.
FastAPI server con webhook de Telegram.
"""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importar módulos del bot
import sys
from pathlib import Path

# Agregar k2-bot al path de Python
sys.path.insert(0, str(Path(__file__).parent / "k2-bot"))

from src.config import get_settings
from src.handlers import TelegramWebhookHandler
from src.auth import extract_user_info, authorize_request, UserAuthorizationError


# Variables globales
telegram_handler = None
settings = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestiona el ciclo de vida de la aplicación.
    Se ejecuta al iniciar y cerrar.
    """
    # Startup
    global telegram_handler, settings
    logger.info("🤖 Iniciando K2-SO Bot...")
    
    try:
        settings = get_settings()
        telegram_handler = TelegramWebhookHandler()
        logger.info(f"✅ Bot K2-SO iniciado correctamente")
        logger.info(f"📍 Project ID: {settings.project_id}")
        logger.info(f"👤 Usuario autorizado: Matías")
    except Exception as e:
        logger.error(f"❌ Error al inicializar el bot: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Deteniendo K2-SO Bot...")


# Crear aplicación FastAPI
app = FastAPI(
    title="K2-SO Bot",
    description="Droide Imperial para tareas de gestión y domésticas",
    version="0.2.0",
    lifespan=lifespan
)


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Endpoint de health check para Cloud Run.
    Verifica que el bot está disponible.
    """
    return {
        "status": "healthy",
        "service": "K2-SO Bot",
        "version": "0.2.0"
    }


@app.get("/", tags=["Info"])
async def root():
    """Información del bot."""
    return {
        "name": "K2-SO Bot",
        "description": "Droide Imperial reprogramado como asistente personal",
        "endpoints": {
            "health": "/health",
            "webhook": "/webhook/telegram",
            "docs": "/docs"
        }
    }


@app.post("/webhook/telegram", tags=["Webhook"])
async def telegram_webhook(request: Request):
    """
    Endpoint webhook para recibir mensajes de Telegram.
    
    Cloud Run enviará POST requests aquí cuando el usuario envíe mensajes.
    """
    if telegram_handler is None:
        logger.error("❌ Telegram handler no inicializado")
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        # Procesar el webhook
        result = await telegram_handler.handle_webhook(request)
        
        # Log del resultado
        if result["status"] == "success":
            logger.info(f"✅ Mensaje procesado - Usuario: {result.get('user_id')}")
        elif result["status"] == "unauthorized":
            logger.warning(f"⚠️ Usuario no autorizado: {result.get('user_id')}")
        else:
            logger.error(f"❌ Error: {result.get('error')}")
        
        return JSONResponse(content=result, status_code=200)
    
    except Exception as e:
        logger.error(f"❌ Error procesando webhook: {e}", exc_info=True)
        return JSONResponse(
            content={"status": "error", "error": str(e)},
            status_code=500
        )


@app.get("/status", tags=["Status"])
async def bot_status():
    """Retorna el estado de los sub-agentes del bot."""
    if telegram_handler is None:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    
    try:
        # Obtener estados de los agentes (esto requiere un usuario válido)
        # Por ahora retornamos estado general
        from src.agents.orchestrator import K2Orchestrator
        
        orchestrator = K2Orchestrator(
            project_id=settings.project_id,
            user_id=8071121316  # Matías
        )
        
        agent_status = orchestrator.get_agent_status()
        
        return {
            "status": "operational",
            "agents": agent_status,
            "project": settings.project_id,
            "timezone": settings.default_timezone
        }
    
    except Exception as e:
        logger.error(f"Error obteniendo estado: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@app.get("/ping", tags=["Debug"])
async def ping():
    """Endpoint de debug para verificar conectividad."""
    return {
        "message": "pong",
        "timestamp": os.environ.get("CURRENT_TIME", "unknown")
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Manejador personalizado de excepciones HTTP."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "detail": exc.detail,
            "path": str(request.url.path)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Manejador generalizado de excepciones."""
    logger.error(f"Excepción no manejada: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "detail": "Internal server error",
            "path": str(request.url.path)
        }
    )


def main():
    """Punto de entrada principal."""
    # Configurar puerto y host
    port = int(os.getenv("PORT", "8080"))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"🚀 Iniciando servidor en {host}:{port}")
    
    # Ejecutar servidor
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
