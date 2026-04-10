"""
Database seed functions for initial data population.

Seeds roles, categories, difficulties, and sample exercises
into MongoDB on application startup (idempotent — skips if data exists).
"""

import logging
from models import Role, Category, Difficulty, Exercise

logger = logging.getLogger(__name__)


async def seed_roles() -> None:
    """Seed default roles if they don't exist."""
    base_roles = [
        {"name": "admin"},
        {"name": "trainer"},
        {"name": "user"},
    ]
    for role_data in base_roles:
        existing = await Role.find_one(Role.name == role_data["name"])
        if not existing:
            await Role(**role_data).insert()
            logger.info("Seeded role: %s", role_data["name"])


async def seed_categories() -> None:
    """Seed exercise categories if they don't exist."""
    categories = [
        {"name": "tecnicas_golpeo", "description": "Técnicas de Golpeo"},
        {"name": "defensa", "description": "Defensa"},
        {"name": "fuerza_acondicionamiento", "description": "Fuerza y Acondicionamiento"},
    ]
    for cat in categories:
        existing = await Category.find_one(Category.name == cat["name"])
        if not existing:
            await Category(**cat).insert()
            logger.info("Seeded category: %s", cat["name"])


async def seed_difficulties() -> None:
    """Seed difficulty levels if they don't exist."""
    difficulties = [
        {"name": "principiante", "description": "Principiante"},
        {"name": "intermedio", "description": "Intermedio"},
        {"name": "avanzado", "description": "Avanzado"},
    ]
    for diff in difficulties:
        existing = await Difficulty.find_one(Difficulty.name == diff["name"])
        if not existing:
            await Difficulty(**diff).insert()
            logger.info("Seeded difficulty: %s", diff["name"])


async def seed_exercises() -> None:
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
        existing = await Exercise.find_one(Exercise.title == ex_data["title"])
        if not existing:
            await Exercise(**ex_data).insert()
            logger.info("Seeded exercise: %s", ex_data["title"])


async def run_all_seeds() -> None:
    """Run all seed functions in order."""
    await seed_roles()
    await seed_categories()
    await seed_difficulties()
    await seed_exercises()
    logger.info("All seeds completed.")
