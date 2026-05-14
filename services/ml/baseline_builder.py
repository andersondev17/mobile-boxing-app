from pathlib import Path
import sys
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent

if __package__:
    from services.ml.tracking.boxing_jab_tracker import BoxingJabTracker
else:  # ejecucion directa del script
    if str(BASE_DIR) not in sys.path:
        sys.path.insert(0, str(BASE_DIR))
    from services.ml.tracking.boxing_jab_tracker import BoxingJabTracker  # type: ignore

DEFAULT_INPUT = BASE_DIR / "videos_profesionales"
DEFAULT_OUTPUT = BASE_DIR / "baseline.parquet"
SUPPORTED_EXT = (".mp4", ".mov", ".avi", ".mkv")


def iter_videos(folder: Path):
    for path in sorted(folder.glob("*")):
        if path.suffix.lower() in SUPPORTED_EXT:
            yield path


def build_baseline(input_folder: Path = DEFAULT_INPUT, output_path: Path = DEFAULT_OUTPUT):
    input_folder = Path(input_folder)
    output_path = Path(output_path)
    if not input_folder.exists():
        raise FileNotFoundError(f"No existe la carpeta de videos profesionales: {input_folder}")

    tracker = BoxingJabTracker(baseline=None)
    all_features = []

    for video_path in iter_videos(input_folder):
        print(f"Procesando video: {video_path}")
        _, features, _ = tracker.process_video(str(video_path))
        clean = [f for f in features if f]
        all_features.extend(clean)

    if not all_features:
        raise RuntimeError("No se encontraron features para construir el baseline.")

    df = pd.DataFrame(all_features)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    print(f"Baseline generado y guardado en {output_path}")
    return output_path


if __name__ == "__main__":
    build_baseline()


def ensure_baseline(
    input_folder: Path = DEFAULT_INPUT,
    output_path: Path = DEFAULT_OUTPUT,
):
    """
    Garantiza que exista un baseline. Si el archivo ya esta generado,
    simplemente devuelve la ruta; de lo contrario, lanza build_baseline.
    """
    output_path = Path(output_path)
    if output_path.exists():
        return output_path
    return build_baseline(input_folder=input_folder, output_path=output_path)







