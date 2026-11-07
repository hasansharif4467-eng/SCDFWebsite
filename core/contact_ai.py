import json
import logging
import os
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

AI_PYTHON = BASE_DIR / "ai-venv" / "Scripts" / "python.exe"
PREDICT_SCRIPT = (
    BASE_DIR / "ai_models" / "contact_classifier" / "predict.py"
)

VALID_CATEGORIES = {
    "volunteering",
    "project_inquiry",
    "partnership",
    "training_inquiry",
    "complaint",
    "other",
}

logger = logging.getLogger(__name__)


def classify_contact_message(message):
    if not isinstance(message, str) or not message.strip():
        return None

    try:
        if not AI_PYTHON.is_file():
            raise FileNotFoundError("AI Python interpreter not found.")

        if not PREDICT_SCRIPT.is_file():
            raise FileNotFoundError("AI prediction script not found.")

        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["TF_CPP_MIN_LOG_LEVEL"] = "2"

        result = subprocess.run(
            [
                str(AI_PYTHON),
                "-X",
                "utf8",
                str(PREDICT_SCRIPT),
            ],
            input=json.dumps(
                {"message": message.strip()},
                ensure_ascii=False,
            ),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=45,
            cwd=str(BASE_DIR),
            env=env,
            check=False,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"AI prediction process failed: {result.stderr[-1000:]}"
            )

        prediction = json.loads(result.stdout)

        if not prediction.get("success"):
            raise ValueError("AI prediction was unsuccessful.")

        category = prediction.get("category")
        confidence = float(prediction.get("confidence"))

        if category not in VALID_CATEGORIES:
            raise ValueError("AI returned an invalid category.")

        if not 0 <= confidence <= 100:
            raise ValueError("AI returned an invalid confidence score.")

        return {
            "category": category,
            "confidence": round(confidence, 2),
        }

    except Exception:
        logger.exception("Contact message AI classification failed.")
        return None
