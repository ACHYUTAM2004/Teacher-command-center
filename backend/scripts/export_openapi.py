import json
import sys
from pathlib import Path

# Add backend/ to sys.path so 'app' is discoverable
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app


def export_openapi() -> None:
    # Target: D:\tcc\docs\openapi.json
    output_path = BACKEND_DIR.parent / "docs" / "openapi.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    schema = app.openapi()
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)

    print(f"[OK] OpenAPI schema exported successfully to: {output_path}")


if __name__ == "__main__":
    export_openapi()