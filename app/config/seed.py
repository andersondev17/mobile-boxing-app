import logging
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    User,
    Exercise,
    Training,
    BoxingSession,
    Consent,
)

logger = logging.getLogger(__name__)


async def seed_exercises(db: AsyncSession) -> None:
    """Seed sample boxing exercises if they don't exist."""
    exercises_data = [
        {
            "title": "Jab",
            "poster_url": "jab",
            "video_url": "jab",
            "category": "tecnicas_golpeo",
            "difficulty": "principiante",
            "duration_min": 5,
            "description": "Golpe directo rápido con la mano adelantada",
            "technique": (
                "Mantén la guardia alta, extiende el brazo rápidamente "
                "y retira inmediatamente. Gira la palma hacia abajo al impactar."
            ),
            "muscles": ["Hombros", "Tríceps", "Core"],
            "equipment": "Saco de boxeo, pads o sombra",
        },
        {
            "title": "Directo de Derecha",
            "poster_url": "directoDerecha",
            "video_url": "directoDerecha",
            "category": "tecnicas_golpeo",
            "difficulty": "principiante",
            "duration_min": 5,
            "description": "Golpe potente con la mano trasera",
            "technique": (
                "Gira la cadera y hombros mientras transfieres peso al pie delantero. "
                "Mantén la mano protegiendo el mentón."
            ),
            "muscles": ["Hombros", "Espalda", "Core", "Piernas"],
            "equipment": "Saco de boxeo, pads o sombra",
        },
        {
            "title": "Gancho Izquierdo",
            "poster_url": "ganchoIzquierdo",
            "video_url": "ganchoIzquierdo",
            "category": "tecnicas_golpeo",
            "difficulty": "intermedio",
            "duration_min": 6,
            "description": "Golpe circular con la mano izquierda al rostro",
            "technique": (
                "Mantén el codo a 90°, gira el torso y pivota el pie izquierdo. "
                "El movimiento viene de la rotación corporal."
            ),
            "muscles": ["Hombros", "Oblicuos", "Core", "Piernas"],
            "equipment": "Saco de boxeo, pads o sombra",
        },
        {
            "title": "Uppercut",
            "poster_url": "uppercut",
            "video_url": "uppercut",
            "category": "tecnicas_golpeo",
            "difficulty": "intermedio",
            "duration_min": 7,
            "description": "Golpe ascendente dirigido al mentón",
            "technique": (
                "Dobla las rodillas y empuja desde las piernas con movimiento ascendente. "
                "Mantén el codo flexionado."
            ),
            "muscles": ["Piernas", "Glúteos", "Core", "Hombros", "Bíceps"],
            "equipment": "Saco de boxeo, pads o sombra",
        },
    ]
    for ex_data in exercises_data:
        stmt = select(Exercise).where(Exercise.title == ex_data["title"])
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if not existing:
            db.add(Exercise(**ex_data))
            logger.info("Seeded exercise: %s", ex_data["title"])


async def run_all_seeds(db: AsyncSession) -> None:
    """Run all seed functions in order."""
    # Note: Categorías y Dificultades ahora son strings en el modelo de Ejercicio para simplificar la migración inicial.
    # Si se requieren tablas separadas, se deben definir en postgres.py.
    await seed_exercises(db)
    await db.commit()
    logger.info("All seeds completed.")






