# routes/video_ws.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import base64, cv2, numpy as np, logging
from ml_service import procesar_frame, ContadorDominadas, mp_pose

router = APIRouter(prefix="/video", tags=["video"])

contador_global = ContadorDominadas()
logger = logging.getLogger(__name__)

@router.websocket("/ws/process_frame")
async def websocket_endpoint(websocket: WebSocket):
    #websocket para camara en tiempo real
    await websocket.accept()
    logger.info("Cliente conectado al socket de video")

    with mp_pose.Pose(
        min_tracking_confidence=0.5,
        min_detection_confidence=0.5,
        static_image_mode=False
    ) as pose:
        try:
            while True:
                data = await websocket.receive_text()
                try:
                    # Decodificar imagen
                    if ',' in data:
                        img_data = base64.b64decode(data.split(',')[1])
                    else:
                        img_data = base64.b64decode(data)
                    
                    nparr = np.frombuffer(img_data, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    if frame is None:
                        continue
                    
                    # Procesar frame
                    resultado = procesar_frame(frame, pose, contador_global)
                    
                    # Enviar respuesta
                    response = {
                        "count": resultado["count"],
                        "state": resultado["state"],
                        "landmarks": resultado["landmarks"]
                    }
                    
                    await websocket.send_json(response)

                except Exception as e:
                    logger.error(f"Error procesando frame: {e}")
                    continue
        except WebSocketDisconnect:
            logger.info("Cliente desconectado")
        except Exception as e:
            logger.error(f"Error en WebSocket: {str(e)}")
