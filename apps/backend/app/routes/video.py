from fastapi import APIRouter, UploadFile, File
from fastapi.responses import FileResponse
from pathlib import Path
import shutil
import logging
from ml_service import procesar_video, ContadorDominadas

router = APIRouter(prefix="/video", tags=["video"])

logger = logging.getLogger(__name__)

# Crear carpetas necesarias
TEMP_DIR = Path("videos/temp")
OUTPUT_DIR = Path("videos/output")
TEMP_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

contador_global = ContadorDominadas()

@router.get("/reset_counter")
async def reset_counter():
    #Reinicia el contador a 0
    contador_global.reset()
    logger.info("Contador reiniciado")
    return {"message": "Contador reiniciado", "count": 0}

@router.post("/process_video")
async def process_video_endpoint(file: UploadFile = File(...)):
    #Procesa un video y retorna el video con el contador
    logger.info(f"Procesando video: {file.filename}")
    
    # Rutas
    input_path = TEMP_DIR / f"temp_{file.filename}"
    output_path = OUTPUT_DIR / f"processed_{file.filename}"
    
    try:
        # Guardar archivo
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Procesar video
        resultado = procesar_video(str(input_path), str(output_path))
        
        logger.info(f"Video procesado: {resultado['total_pullups']} dominadas")
        
        # Limpiar temporal
        if input_path.exists():
            input_path.unlink()
        
        # Retornar video
        return FileResponse(
            output_path,
            media_type="video/mp4",
            filename=f"resultado_{file.filename}"
        )
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        # Limpiar en caso de error
        if input_path.exists():
            input_path.unlink()
        if output_path.exists():
            output_path.unlink()
        return {"error": str(e)}
