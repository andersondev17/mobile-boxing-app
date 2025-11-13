from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from pathlib import Path
import shutil
import logging
import base64
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
    """Procesa un video y retorna el video procesado en base64 con metadata"""
    input_path = TEMP_DIR / f"temp_{file.filename}"
    output_path = OUTPUT_DIR / f"processed_{file.filename}"

    try:
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        resultado = procesar_video(str(input_path), str(output_path))
        logger.info(f"Video procesado: {resultado['total_pullups']} dominadas")

        input_path.unlink()

        with open(output_path, "rb") as video_file:
            video_base64 = base64.b64encode(video_file.read()).decode('utf-8')

        output_path.unlink()

        return JSONResponse(
            content={
                "video_base64": video_base64,
                "total_pullups": resultado['total_pullups'],
                "filename": f"resultado_{file.filename}"
            },
            headers={
                "X-Total-Pullups": str(resultado['total_pullups'])
            }
        )

    except Exception as e:
        logger.error(f"Error procesando video: {str(e)}")
        input_path.unlink(missing_ok=True)
        output_path.unlink(missing_ok=True)
        return {"error": str(e)}
