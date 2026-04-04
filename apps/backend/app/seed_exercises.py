import sys
from pathlib import Path

# Add current dir to path to import config and models
sys.path.append(str(Path(__file__).parent))

from config import get_db, engine, Base
from models.model import Exercise, Category, Difficulty
from sqlalchemy.orm import Session
import uuid

def seed_exercises():
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    db: Session = next(get_db())
    
    try:
        # 1. Seed Categories
        categories_data = [
            {"id": "tecnicas_golpeo", "description": "Técnicas de Golpeo"},
            {"id": "defensa", "description": "Defensa"},
            {"id": "fuerza_acondicionamiento", "description": "Fuerza y Acondicionamiento"}
        ]
        
        for cat in categories_data:
            if not db.query(Category).filter(Category.id == cat["id"]).first():
                db.add(Category(**cat))
        
        # 2. Seed Difficulties
        difficulties_data = [
            {"id": "principiante", "description": "Principiante"},
            {"id": "intermedio", "description": "Intermedio"},
            {"id": "avanzado", "description": "Avanzado"}
        ]
        
        for diff in difficulties_data:
            if not db.query(Difficulty).filter(Difficulty.id == diff["id"]).first():
                db.add(Difficulty(**diff))
        
        db.commit()

        # 3. Seed Exercises
        exercises_data = [
            {
                "title": "Jab",
                "poster_url": "jab",
                "video_url": "jab",
                "category_id": "tecnicas_golpeo",
                "difficulty_id": "principiante",
                "duration_min": 5,
                "description": "Golpe directo rápido con la mano adelantada",
                "technique": "Mantén la guardia alta, extiende el brazo rápidamente y retira inmediatamente. Gira la palma hacia abajo al impactar.",
                "muscles": ["Hombros", "Tríceps", "Core"],
                "equipment": "Saco de boxeo, pads o sombra"
            },
            {
                "title": "Directo de Derecha",
                "poster_url": "directoDerecha",
                "video_url": "directoDerecha",
                "category_id": "tecnicas_golpeo",
                "difficulty_id": "principiante",
                "duration_min": 5,
                "description": "Golpe potente con la mano trasera",
                "technique": "Gira la cadera y hombros mientras transfieres peso al pie delantero. Mantén la mano protegiendo el mentón.",
                "muscles": ["Hombros", "Espalda", "Core", "Piernas"],
                "equipment": "Saco de boxeo, pads o sombra"
            },
            {
                "title": "Gancho Izquierdo",
                "poster_url": "ganchoIzquierdo",
                "video_url": "ganchoIzquierdo",
                "category_id": "tecnicas_golpeo",
                "difficulty_id": "intermedio",
                "duration_min": 6,
                "description": "Golpe circular con la mano izquierda al rostro",
                "technique": "Mantén el codo a 90°, gira el torso y pivota el pie izquierdo. El movimiento viene de la rotación corporal.",
                "muscles": ["Hombros", "Oblicuos", "Core", "Piernas"],
                "equipment": "Saco de boxeo, pads o sombra"
            },
            {
                "title": "Uppercut",
                "poster_url": "uppercut",
                "video_url": "uppercut",
                "category_id": "tecnicas_golpeo",
                "difficulty_id": "intermedio",
                "duration_min": 7,
                "description": "Golpe ascendente dirigido al mentón",
                "technique": "Dobla las rodillas y empuja desde las piernas con movimiento ascendente. Mantén el codo flexionado.",
                "muscles": ["Piernas", "Glúteos", "Core", "Hombros", "Bíceps"],
                "equipment": "Saco de boxeo, pads o sombra"
            }
        ]

        for ex in exercises_data:
            if not db.query(Exercise).filter(Exercise.title == ex["title"]).first():
                db.add(Exercise(id=str(uuid.uuid4()), **ex))
        
        db.commit()
        print("✅ Database seeded successfully with exercises!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_exercises()
