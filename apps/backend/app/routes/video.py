from fastapi import APIRouter, UploadFile, File
from fastapi.responses import FileResponse
from pathlib import Path
import shutil
import logging
from ml_service import procesar_video, ContadorDominadas

router = APIRouter(prefix="/video", tags=["video"])
logger = logging.getLogger(__name__)

TEMP_DIR = Path("videos/temp")
OUTPUT_DIR = Path("videos/output")

contador_global = ContadorDominadas()

@router.get("/reset_counter")
async def reset_counter():
    contador_global.reset()
    logger.info("Contador reiniciado")
    return {"message": "Contador reiniciado", "count": 0}

@router.post("/process_video")
async def process_video_endpoint(file: UploadFile = File(...)):
    input_path = TEMP_DIR / f"temp_{file.filename}"
    output_path = OUTPUT_DIR / f"processed_{file.filename}"

    try:
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        resultado = procesar_video(str(input_path), str(output_path))
        logger.info(f"Video procesado: {resultado['total_pullups']} dominadas")

        if input_path.exists():
            input_path.unlink()

        return FileResponse(
            output_path,
            media_type="video/mp4",
            filename=f"resultado_{file.filename}"
        )
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        if input_path.exists():
            input_path.unlink()
        if output_path.exists():
            output_path.unlink()
        return {"error": str(e)}
