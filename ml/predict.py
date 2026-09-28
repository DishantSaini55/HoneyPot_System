from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib

from ml.features import vectorize


def predict(model_path: str | Path, features: dict[str, Any]) -> dict[str, str | float]:
    artifact = joblib.load(model_path)
    probabilities = artifact["pipeline"].predict_proba([vectorize(features)])[0]
    index = int(probabilities.argmax())
    return {
        "model_version": artifact["version"],
        "classification": str(artifact["pipeline"].classes_[index]),
        "confidence": float(probabilities[index]),
    }
