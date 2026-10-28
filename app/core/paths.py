from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = ROOT_DIR / "app" / "templates"
GENERATED_DIR = ROOT_DIR / "storage" / "documents" / "generated"
STATIC_DIR = ROOT_DIR / "static"
